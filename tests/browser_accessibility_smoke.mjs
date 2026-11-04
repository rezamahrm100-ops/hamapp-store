import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const browser = await chromium.launch({headless: true});
const context = await browser.newContext({
  locale: 'fa-IR',
  viewport: {width: 390, height: 844},
  deviceScaleFactor: 1,
  isMobile: true,
  hasTouch: true,
});
const page = await context.newPage();
page.setDefaultTimeout(20000);
const tags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

async function checkA11y(label) {
  const result = await new AxeBuilder({page}).withTags(tags).analyze();
  const violations = result.violations.filter(v => ['critical', 'serious'].includes(v.impact));
  for (const violation of violations) {
    console.error('ACCESSIBILITY_FAIL', label, violation.id,
                  violation.impact, violation.nodes.slice(0,4).map(n=>({target:n.target,reason:n.failureSummary})));
  }
  assert.equal(violations.length, 0, 'Serious/critical accessibility violations in ' + label);
  console.log('ACCESSIBILITY_ACCEPTED', label, 'rules', result.passes.length);
}

try {
  await page.goto('http://127.0.0.1:8765/', {waitUntil: 'networkidle', timeout:20000});
  await page.locator('#cards .card').first().waitFor();
  assert.equal(await page.locator('#cards .card').count(), 3);
  assert.equal(await page.locator('#cards a.download').count(), 0);
  assert.equal(await page.locator('html').getAttribute('dir'), 'rtl');
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  assert.ok(width <= 390, 'Mobile viewport overflows horizontally: ' + width);
  await checkA11y('mobile-dark');
  await page.locator('#toggleTheme').click();
  console.log('LIGHT_FILTER_COMPUTED', await page.locator('button[data-filter="android"]').evaluate(el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor, opacity: getComputedStyle(el).opacity, root: document.documentElement.className})));
  await checkA11y('mobile-light');

  const button = page.locator('#cards .detail-button').first();
  await button.focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#detailsDialog').isVisible(), true);
  await checkA11y('mobile-detail-dialog');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#detailsDialog').isVisible(), false);
  console.log('REAL_MOBILE_CHROMIUM_WCAG21_AA_SMOKE_PASSED');
} finally {
  await browser.close();
}
