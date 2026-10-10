import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const sample = fileURLToPath(new URL('../../../examples/cedar-handbook.pdf', import.meta.url));
const backend = 'http://127.0.0.1:8010';

test.beforeEach(async ({ request, page }) => {
  await request.post(`${backend}/documents/reset`, { data: { confirm: 'ARCHIVE ALL' } });
  await page.goto('/');
  await expect(page.getByRole('status')).toContainText('Backend ready');
  await expect(page.locator('body')).toHaveCSS('margin', '0px');
});

async function upload(page: import('@playwright/test').Page) {
  await page.getByLabel('Text-based PDF').setInputFiles(sample);
  await page.getByRole('button', { name: 'Upload PDF', exact: true }).click();
  await expect(page.getByRole('checkbox')).toBeVisible();
}

test('ingestion, scoped answer, citations, source PDF, archive and reset', async ({ page }) => {
  await upload(page);
  await page.getByRole('checkbox').check();
  await page.getByLabel('Your question').fill('How many days of annual leave are available?');
  await page.getByLabel('Your question').press('Enter');
  await expect(page.getByRole('article')).toContainText('20 days');
  await expect(page.getByRole('article')).toContainText('Page 1 · cited');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download source PDF · page 1' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('source.pdf');
  expect((await readFile((await download.path())!)).subarray(0, 5).toString()).toBe('%PDF-');
  await page.screenshot({ path: '../docs/screenshots/synthetic-desktop.png', fullPage: true });
  page.on('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Archive cedar-handbook.pdf' }).click();
  await expect(page.getByText('No documents yet.', { exact: false })).toBeVisible();
  await upload(page);
  await page.getByRole('button', { name: 'Archive all documents' }).click();
  await expect(page.getByRole('checkbox')).toHaveCount(0);
});

test('duplicate upload, unanswerable query, API failure and overlap guard', async ({ page }) => {
  await upload(page); await upload(page);
  await expect(page.getByRole('status')).toContainText('no duplicate');
  await expect(page.getByRole('checkbox')).toHaveCount(1);
  await page.getByLabel('Your question').fill('What is the salary of the president of Mars?');
  await page.getByRole('button', { name: 'Ask question' }).click();
  await expect(page.getByRole('article')).toContainText('insufficient evidence');
  let queries = 0;
  await page.route('**/query', async route => { queries++; await new Promise(resolve => setTimeout(resolve, 300)); await route.fulfill({ status: 503, json: { detail: 'Ollama is unavailable.' } }); });
  await page.getByLabel('Your question').fill('annual leave');
  await page.getByLabel('Your question').press('Enter');
  await page.locator('form').evaluate(form => { form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
  await expect(page.getByRole('alert')).toContainText('Ollama is unavailable');
  expect(queries).toBe(1);
});

test('cancellation, mobile layout, dark mode and accessibility', async ({ page }) => {
  await upload(page);
  await page.route('**/query', async route => { await new Promise(resolve => setTimeout(resolve, 1500)); await route.fulfill({ json: {} }).catch(() => {}); });
  await page.getByLabel('Your question').fill('annual leave');
  await page.getByRole('button', { name: 'Ask question' }).click();
  await page.getByRole('button', { name: 'Cancel request' }).click();
  await expect(page.getByRole('alert')).toContainText('cancelled');
  await page.setViewportSize({ width: 375, height: 812 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const light = await new AxeBuilder({ page }).analyze();
  expect(light.violations).toEqual([]);
  await page.getByRole('button', { name: 'Toggle dark mode' }).click();
  await expect(page.locator('html')).toHaveCSS('background-color', 'rgb(17, 30, 34)');
  const dark = await new AxeBuilder({ page }).analyze();
  expect(dark.violations).toEqual([]);
  await page.screenshot({ path: '../docs/screenshots/synthetic-mobile-dark.png', fullPage: true });
});
