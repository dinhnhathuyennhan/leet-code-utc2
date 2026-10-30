const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.LOCALAPPDATA+'/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage();
 page.on('pageerror',e=>console.log('PAGEERROR',e.message));
 page.on('response',r=>{if(r.status()>=400)console.log('HTTP',r.status(),r.url())});
 await page.goto('http://localhost:3000/login');
 await page.locator('input[name=email]').fill(process.env.ADMIN_EMAIL);
 await page.locator('input[name=password]').fill(process.env.ADMIN_PASSWORD);
 await page.locator('button[type=submit]').click();
 await page.waitForURL('**/admin/**',{timeout:30000});
 console.log('LOGIN',page.url());
 for(const path of ['dashboard','accounts','accounts/import','courses','classes','problem-bank','submissions','settings']){
  await page.goto('http://localhost:3000/admin/'+path); await page.waitForTimeout(1800);
  console.log('PAGE',path, (await page.locator('body').innerText()).slice(0,10000));
  await page.screenshot({path:'.tmp-admin-playwright/'+path.replaceAll('/','-')+'.png',fullPage:true});
 }
 await context.storageState({path:'.tmp-admin-playwright/session.json'});
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1});
