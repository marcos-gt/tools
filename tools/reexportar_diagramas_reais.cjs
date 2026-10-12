const path = require('path');
const fs = require('fs');
const assert = require('node:assert/strict');
const {chromium} = require(path.resolve('.test-artifacts/node_modules/playwright'));
const root = path.resolve('docs/testes-reais-2026-10-12');
const results = JSON.parse(fs.readFileSync(path.join(root,'resultados.json'),'utf8'));
const base = process.env.TCC_REAL_BASE;
(async()=>{
 const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  const page = await browser.newPage({viewport:{width:1600,height:1000}});
  page.on('dialog',d=>d.accept());
  await page.goto(base+'/login/');await page.fill('#username','tcc');await page.fill('#password',process.env.TCC_LOGIN_PASSWORD);
  await page.click('button[type=submit]');await page.waitForURL(base+'/');
  await page.waitForFunction(()=>window.mermaid && window.renderMermaid,{timeout:60000});
  const exported = [];
  for(const record of results.filter(r=>r.fase==='sintaxe_explicita'&&r.render_status==='success')) {
   const response = await page.request.get(base+`/output/${record.output_id}/export/json/`);
   assert.equal(response.status(),200);
   const evidence = await response.json();
   await page.evaluate(evidence=>{
    const app=Object.create(ChatApp.prototype);
    app.output=evidence.mermaid;app.outputId=evidence.id;
    app.showGeneratedModal(evidence.categoria.nome,evidence.mermaid,{visualizationType:evidence.modalidade,chatsUsed:evidence.mensagens.length});
   },evidence);
   await page.waitForSelector('#modalMermaidContent a');
   assert.equal(await page.locator('#modalRenderStatus').textContent(),'Diagrama renderizado');
   const geometry=await page.locator('#modalMermaidContent svg').evaluate(svg=>[...svg.querySelectorAll('.mindmap-node')]
    .filter(node=>node.querySelector(':scope > circle'))
    .map(node=>{const text=node.querySelector('text');const box=text.getBBox();const radius=Number(node.querySelector('circle').getAttribute('r'));return {texto:text.textContent,x:box.x,width:box.width,radius,centralizado:Math.abs(box.x+box.width/2)<2,cabe:box.x>=-radius&&box.x+box.width<=radius};}));
   for(const node of geometry) assert.ok(node.centralizado && node.cabe,'Rótulo circular deve ficar centralizado e legível');
   const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar PNG'}).click();
   const download=await downloadPromise;
   const filename=`${record.caso}-${record.modalidade}-geracao-${record.output_id}-alinhamento-corrigido.png`;
   await download.saveAs(path.join(root,filename));
   exported.push({output_id:record.output_id,caso:record.caso,modalidade:record.modalidade,arquivo_png:filename,geometria:geometry,codigo_mermaid_alterado:false});
   await page.locator('#generatedContentModal button[data-bs-dismiss=modal]').last().click();await page.waitForSelector('#generatedContentModal',{state:'detached'});
   console.log('PNG CORRIGIDO',record.caso,record.modalidade,record.output_id);
  }
  fs.writeFileSync(path.join(root,'exportacoes-alinhamento-corrigido.json'),JSON.stringify(exported,null,2));
 } finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
