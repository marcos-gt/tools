const path = require('path');
const fs = require('fs');
const assert = require('node:assert/strict');
const {chromium} = require(path.resolve('.test-artifacts/node_modules/playwright'));
const report = path.resolve(process.env.TCC_REAL_REPORT || 'docs/testes-reais-2026-10-12');
const manifest = JSON.parse(fs.readFileSync(path.join(report, 'manifesto.json'), 'utf8'));
const base = process.env.TCC_REAL_BASE;
const timeout = Number(process.env.TCC_BROWSER_TIMEOUT || 210000);
const resultsPath = path.join(report, 'resultados.json');
const results = fs.existsSync(resultsPath) ? JSON.parse(fs.readFileSync(resultsPath, 'utf8')) : [];
const runId = new Date().toISOString();
const save = () => fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));

(async () => {
 const browser = await chromium.launch({executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true});
 try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const errors = [];
  const dialogs = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('dialog', dialog => {dialogs.push(dialog.message());dialog.accept();});
  await page.goto(base + '/login/');
  await page.fill('#username', process.env.TCC_LOGIN_USER || 'tcc');
  await page.fill('#password', process.env.TCC_LOGIN_PASSWORD);
  await page.click('button[type=submit]');
  await page.waitForURL(base + '/');
  await page.waitForFunction(() => window.mermaid && document.querySelector('#generatorCategory').options.length >= 16, {timeout:60000});
  // A primeira solicitação é o mapa mental da referência diagrama-1.png.
  for (const caseData of manifest.casos) {
   for (const mode of ['mapa-mental', 'fluxograma']) {
    const started = Date.now();
    const entry = {run_id:runId, modelo:manifest.modelo, fase:manifest.fase || 'baseline', caso:caseData.caso, categoria_id:caseData.categoria_id, modalidade:mode, inicio:new Date().toISOString()};
    console.log('INICIANDO', entry.caso, mode, 'mensagens', caseData.mensagens_efetivas.length);
    try {
     await page.selectOption('#generatorCategory', String(caseData.categoria_id));
     await page.selectOption('#generatorMode', mode);
     const responsePromise = page.waitForResponse(r => r.url() === base + '/' && r.request().method() === 'POST', {timeout});
     await page.click('#generateBtn');
     const response = await responsePromise;
     const result = await response.json();
     entry.http = response.status();
     entry.output_id = result.output_id;
     entry.codigo_erro = result.code || '';
     entry.erro = result.error || '';
     if (entry.output_id) {
      const exported = await page.request.get(base + `/output/${entry.output_id}/export/json/`);
      assert.equal(exported.status(), 200);
      const evidence = await exported.json();
      const name = `${caseData.caso}-${mode}-geracao-${entry.output_id}`;
      fs.writeFileSync(path.join(report, name+'.json'), JSON.stringify(evidence,null,2));
      entry.arquivo_json = name+'.json';
      entry.mensagens_usadas = evidence.mensagens.length;
      entry.payload_integral = JSON.stringify(evidence.mensagens.map(m=>({id:m.id,texto:m.texto}))) === JSON.stringify(caseData.mensagens_efetivas);
      entry.inativo_excluido = !evidence.mensagens.some(m => m.id === manifest.controle_inativo_id);
      entry.duracao_inferencia_ms = evidence.duracao_ms;
      assert.ok(entry.payload_integral, 'Payload deve coincidir com IDs/textos integrais em ordem');
      assert.ok(entry.inativo_excluido, 'Mensagem inativa deve ser excluída');
      if (evidence.mermaid) {
       const mmd = await page.request.get(base + `/output/${entry.output_id}/export/mmd/`);
       assert.equal(mmd.status(),200);
       assert.equal(await mmd.text(),evidence.mermaid);
       fs.writeFileSync(path.join(report,name+'.mmd'),evidence.mermaid);
       entry.arquivo_mmd = name+'.mmd';
      }
     }
     if (response.ok()) {
      assert.ok(result.output && result.output.trim());
      assert.equal(result.total_chats,caseData.mensagens_efetivas.length);
      await page.waitForSelector('#modalMermaidContent a', {timeout:60000});
      const status = await page.locator('#modalRenderStatus').textContent();
      entry.render_status = status === 'Diagrama renderizado' ? 'success' : 'failure';
      if (entry.render_status === 'success') {
       const name = `${caseData.caso}-${mode}-geracao-${entry.output_id}`;
       const downloadPromise = page.waitForEvent('download',{timeout:20000});
       await page.getByRole('button',{name:'Exportar PNG'}).click();
       const download = await downloadPromise;
       await download.saveAs(path.join(report,name+'.png'));
       assert.ok(fs.readFileSync(path.join(report,name+'.png')).subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])));
       entry.arquivo_png = name+'.png';
      } else {
       entry.mermaid_preservado_no_frontend = (await page.locator('#modalMermaidContent pre').textContent()) === result.output;
       await page.locator('#generatedContentModal').screenshot({path:path.join(report,`${caseData.caso}-${mode}-erro-render-${entry.output_id}.png`)});
      }
      await page.locator('#generatedContentModal button[data-bs-dismiss=modal]').last().click();
      await page.waitForSelector('#generatedContentModal',{state:'detached'});
     } else {
      assert.equal(await page.locator('#generatedContentModal').count(),0);
      entry.erro_visivel = (await page.locator('#errorMessage').textContent()).includes(result.error);
     }
     await page.waitForFunction(()=>!document.querySelector('#generateBtn').disabled,{timeout:30000});
     entry.botao_restaurado = true;
    } catch (error) {
     entry.falha_verificacao = error.message;
     const modal = page.locator('#generatedContentModal');
     if (await modal.count()) {
      try {await modal.locator('button[data-bs-dismiss=modal]').last().click();await page.waitForSelector('#generatedContentModal',{state:'detached'});} catch (_) {}
     }
    }
    entry.duracao_teste_ms = Date.now()-started;
    results.push(entry);
    save();
    console.log('RESULTADO',entry.caso,mode,'HTTP',entry.http,'registro',entry.output_id,'renderer',entry.render_status||'-','tempo_ms',entry.duracao_teste_ms,entry.falha_verificacao?'FALHA_DE_VERIFICACAO':'');
   }
  }
  fs.writeFileSync(path.join(report,'erros-browser.json'),JSON.stringify(errors,null,2));
  fs.writeFileSync(path.join(report,'dialogos-browser.json'),JSON.stringify(dialogs,null,2));
  assert.ok(!dialogs.some(message=>message==='1'), 'HTML/script literal não deve executar alert(1)');
  console.log('FINALIZADO',results.filter(r=>r.run_id===runId).length,'tentativas reais; erros JS:',errors.length);
 } finally {await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
