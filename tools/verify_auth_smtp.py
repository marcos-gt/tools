"""Teste local: SMTP que captura mensagens, sem entrega externa, e PostgreSQL isolado."""
import json
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import threading
import time
from email import policy
from email.parser import BytesParser
import requests
import psycopg

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
artifacts = ROOT / '.test-artifacts'
artifacts.mkdir(exist_ok=True)
evidence = ROOT / 'docs/auth-evidencias'
evidence.mkdir(exist_ok=True)
outbox = artifacts / 'auth-mailbox.json'
outbox.write_text('[]', encoding='utf-8')
messages = []
lock = threading.Lock()


class SMTPHandler(socketserver.StreamRequestHandler):
    def reply(self, text):
        self.wfile.write((text+'\r\n').encode('ascii'))
        self.wfile.flush()

    def handle(self):
        self.reply('220 localhost auth-test SMTP')
        while line := self.rfile.readline():
            command = line.decode('utf-8', errors='replace').strip().upper()
            if command.startswith(('EHLO', 'HELO')):
                self.reply('250-localhost\r\n250 SIZE 1048576')
            elif command.startswith(('MAIL FROM:', 'RCPT TO:', 'RSET', 'NOOP')):
                self.reply('250 OK')
            elif command == 'DATA':
                self.reply('354 End with dot')
                raw = b''
                while data := self.rfile.readline():
                    if data == b'.\r\n':
                        break
                    raw += data[1:] if data.startswith(b'..') else data
                message = BytesParser(policy=policy.default).parsebytes(raw)
                plain = message.get_body(preferencelist=('plain',))
                html = message.get_body(preferencelist=('html',))
                with lock:
                    messages.append({'subject':str(message['subject']), 'to':str(message['to']),
                        'text':plain.get_content() if plain else '', 'html':html.get_content() if html else ''})
                    outbox.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding='utf-8')
                self.reply('250 Message captured locally')
            elif command == 'QUIT':
                self.reply('221 Bye')
                break
            else:
                self.reply('502 Command not supported in test sink')


class SMTPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


pg_bin = Path(os.getenv('TCC_TEST_PG_BIN', 'C:/Program Files/PostgreSQL/18/bin'))
data = artifacts / 'auth-pgdata'
if not (data/'PG_VERSION').exists():
    subprocess.run([str(pg_bin/'initdb.exe'),'-D',str(data),'-U','auth_test','-A','trust',
                    '--encoding=UTF8','--locale=C'],check=True,stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
pg_command = [str(pg_bin/'pg_ctl.exe'), '-D', str(data), '-l', str(artifacts/'postgres.log'), '-o', '-h 127.0.0.1 -p 55432', '-w']
started = subprocess.run(pg_command+['start'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if started.returncode:
    raise RuntimeError('Instância PostgreSQL temporária indisponível; nunca usa o banco tcc como fallback.')
web = None
smtp = None
log = (artifacts/'django-auth-test.log').open('w', encoding='utf-8')
try:
    with psycopg.connect(dbname='postgres',user='auth_test',host='127.0.0.1',port=55432,autocommit=True) as connection:
        if not connection.execute("SELECT 1 FROM pg_database WHERE datname='auth_browser'").fetchone():
            connection.execute('CREATE DATABASE auth_browser OWNER auth_test')
    smtp = SMTPServer(('127.0.0.1', 55437), SMTPHandler)
    threading.Thread(target=smtp.serve_forever, daemon=True).start()
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', DJANGO_SECRET_KEY='isolated-auth-browser-test-key', DJANGO_DEBUG='true',
        DB_NAME='auth_browser', DB_USER='auth_test', DB_PASSWORD='', DB_HOST='127.0.0.1', DB_PORT='55432',
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST='127.0.0.1', EMAIL_PORT='55437',
        EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='', EMAIL_USE_TLS='false', EMAIL_USE_SSL='false',
        DEFAULT_FROM_EMAIL='Sistema <notificacoes@example.test>', PUBLIC_SITE_URL='http://127.0.0.1:55436',
        TCC_AUTH_BASE='http://127.0.0.1:55436', TCC_AUTH_TEST_USER='email_ui_'+str(int(time.time())))
    subprocess.run([sys.executable,'manage.py','migrate','--noinput'],env=env,check=True,stdout=log,stderr=log)
    web = subprocess.Popen([sys.executable,'manage.py','runserver','127.0.0.1:55436','--noreload'],
        env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(60):
        if web.poll() is not None:
            raise RuntimeError('Servidor isolado encerrou antes do teste')
        try:
            if requests.get(env['TCC_AUTH_BASE']+'/login/',timeout=1).status_code==200:
                break
        except requests.RequestException:
            time.sleep(.25)
    result = subprocess.run(['node','tools/verify_auth_smtp.cjs'],env=env,capture_output=True,text=True,encoding='utf-8')
    (evidence/'browser-smtp.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    print(result.stdout,result.stderr)
    result.check_returncode()
finally:
    if web:
        web.terminate()
        web.wait(timeout=15)
    if smtp:
        smtp.shutdown()
        smtp.server_close()
    log.close()
    subprocess.run(pg_command+['-m','fast','stop'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
