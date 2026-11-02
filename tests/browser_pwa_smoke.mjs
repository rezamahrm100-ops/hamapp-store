import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({headless: true});
const context = await browser.newContext({locale: 'fa-IR', viewport: {width: 1100, height: 780}});
const page = await context.newPage();
try {
  await page.goto('http://127.0.0.1:8765/', {waitUntil: 'networkidle'});
  assert.match(await page.title(), /هَماپ/);
  await page.locator('#cards .card').first().waitFor();
  assert.equal(await page.locator('#cards .card').count(), 3);

  await page.locator('#cards .detail-button').first().click();
  assert.equal(await page.locator('#detailsDialog').isVisible(), true);
  assert.match(await page.locator('#detailsContent').innerText(), /هنوز نسخه یا فایل قابل دریافت وجود ندارد/);
  await page.locator('#detailsClose').click();
  assert.equal(await page.locator('#detailsDialog').isVisible(), false);

  await page.locator('[data-filter="android"]').click();
  assert.equal(await page.locator('#cards .card').count(), 1);
  await page.locator('[data-filter="all"]').click();
  await page.locator('#search').fill('Windows');
  assert.equal(await page.locator('#cards .card').count(), 1);
  await page.locator('#search').fill('');
  assert.equal(await page.locator('#cards a.download').count(), 0);

  await page.screenshot({path: 'dist/pwa-browser-evidence.png'});
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller), null, {timeout: 20000});
  await context.setOffline(true);
  await page.reload({waitUntil: 'domcontentloaded', timeout: 20000});
  await page.waitForFunction(
    () => document.getElementById('status').textContent.includes('حالت آفلاین'),
    null, {timeout: 20000}
  );
  assert.equal(await page.locator('#cards .card').count(), 3);
  assert.equal(await page.locator('#cards a.download').count(), 0);
  const cards = await page.locator('#cards .card').allInnerTexts();
  assert.ok(cards.every(value => value.includes('در حال توسعه')));
  console.log('REAL_CHROMIUM_PWA_UI_AND_OFFLINE_NO_DOWNLOAD_ACCEPTED');
} finally {
  await browser.close();
}
