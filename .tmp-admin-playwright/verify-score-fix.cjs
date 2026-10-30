const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('fs');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:process.env.LOCALAPPDATA+'/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});const ctx=await browser.newContext();const page=await ctx.newPage();page.setDefaultTimeout(15000);let token;let original;
page.on('request',r=>{if(r.headers().authorization)token=r.headers().authorization});
async function read(){const r=await ctx.request.get('http://localhost:8000/submissions/10',{headers:{Authorization:token}});assert.ok(r.ok());return r.json()}
async function save(){const response=page.waitForResponse(r=>r.url().endsWith('/submissions/10')&&r.request().method()==='PATCH');await page.getByRole('button',{name:'Lưu đánh giá',exact:true}).click();const r=await response;assert.ok(r.ok());return r.json()}
const result={};
try{
await page.goto('http://localhost:3000/login');await page.locator('input[name=email]').fill(process.env.ADMIN_EMAIL);await page.locator('input[name=password]').fill(process.env.ADMIN_PASSWORD);await page.locator('button[type=submit]').click();await page.waitForURL('**/admin/**');await page.goto('http://localhost:3000/admin/submissions/10');await page.getByLabel('Điểm chốt (0–10)').waitFor();original=await read();
await page.getByLabel('Điểm chốt (0–10)').fill('7.5');assert.equal((await save()).manual_score,7.5);await page.reload();await page.getByLabel('Điểm chốt (0–10)').waitFor();assert.equal(await page.getByLabel('Điểm chốt (0–10)').inputValue(),'7.5');
await page.getByLabel('Điểm chốt (0–10)').fill('');assert.equal((await save()).manual_score,null);await page.reload();await page.getByLabel('Điểm chốt (0–10)').waitFor();assert.equal(await page.getByLabel('Điểm chốt (0–10)').inputValue(),'');assert.equal((await read()).manual_score,null);result.save_then_clear='PASS';await page.screenshot({path:'.tmp-admin-playwright/score-fix-pass.png',fullPage:true});
}finally{
if(original){await page.goto('http://localhost:3000/admin/submissions/10');await page.getByLabel('Điểm chốt (0–10)').fill(original.manual_score==null?'':String(original.manual_score));await page.locator('textarea').fill(original.feedback??'');await page.locator('select').selectOption(original.status);await save();const restored=await read();for(const field of ['manual_score','feedback','status'])assert.equal(restored[field],original[field]);result.restored='PASS';}
await page.goto('http://localhost:3000/login');await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();await page.locator('input[name=email]').waitFor();await browser.close();fs.writeFileSync('.tmp-admin-playwright/score-fix-result.json',JSON.stringify(result,null,2));
}console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exitCode=1});
