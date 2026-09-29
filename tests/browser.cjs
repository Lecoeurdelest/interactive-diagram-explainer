const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { spawnSync } = require('node:child_process');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'test-results');
fs.mkdirSync(output, { recursive: true });
const fixtures = Object.fromEntries(['queue-vi', 'regions-en', 'order-review-en'].map(name => {
  const modelPath = path.join(root, 'examples', name + '.json');
  const htmlPath = path.join(output, name + '.html');
  const result = spawnSync('python3', [path.join(root, 'skills/interactive-diagram-explainer/scripts/build_explainer.py'), modelPath, htmlPath, '--force'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  return [name, { model: JSON.parse(fs.readFileSync(modelPath, 'utf8')), url: pathToFileURL(htmlPath).href }];
}));

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.EXPLAINER_BROWSER_CHANNEL ? { channel: process.env.EXPLAINER_BROWSER_CHANNEL } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 736, height: 900 }, colorScheme: 'dark' });
    const errors = [];
    const remoteRequests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => { if (/^https?:/.test(request.url())) remoteRequests.push(request.url()); });
    await page.goto(fixtures['queue-vi'].url);
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator('.ide-root').getAttribute('data-selected'), 'producer');
    assert.equal(await page.locator('.ide-explanation').textContent(), fixtures['queue-vi'].model.items[0].explanation);
    assert(await page.locator('.ide-previous').isDisabled());
    await page.getByRole('button', { name: 'Tiếp', exact: true }).click();
    assert.equal(await page.locator('.ide-root').getAttribute('data-selected'), 'queue');
    assert.equal(await page.locator('.ide-packet').count(), 1, 'next should visibly trace the actual edge');
    assert.equal(await page.locator('.ide-explanation').textContent(), fixtures['queue-vi'].model.items[1].explanation);
    await page.waitForFunction(() => document.querySelector('.ide-root').dataset.animating === 'false');
    assert.equal(await page.locator('.ide-packet').count(), 0);
    await page.evaluate(() => {
      for (const id of ['worker', 'record', 'producer', 'queue']) document.querySelector(`[data-item="${id}"]`).click();
    });
    await page.waitForFunction(() => document.querySelector('.ide-root').dataset.animating === 'false');
    assert.equal(await page.locator('[aria-pressed="true"]').count(), 1);
    assert.equal(await page.locator('.ide-root').getAttribute('data-selected'), 'queue');
    await page.locator('[data-item="worker"]').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.ide-detail-title').textContent(), 'Chạy process_job()');
    await page.getByRole('button', { name: 'Tiếp', exact: true }).click();
    assert(await page.locator('.ide-next').isDisabled());
    assert.equal(await page.locator('.ide-count').textContent(), 'Bước 4 / 4');
    await page.screenshot({ path: path.join(output, 'flow-dark.png'), fullPage: true });

    await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: 'light' });
    await page.locator('[data-item="producer"]').click();
    await page.locator('.ide-next').click();
    assert.equal(await page.locator('.ide-packet').count(), 0);
    assert.equal(await page.locator('.ide-root').getAttribute('data-animating'), 'false');
    assert.equal(await page.evaluate(() => document.getAnimations().length), 0);
    await page.setViewportSize({ width: 320, height: 900 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert(await page.evaluate(() => [...document.querySelectorAll('button')].filter(e => e.getBoundingClientRect().width).every(e => { const r = e.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth && r.height >= 44; })));
    await page.screenshot({ path: path.join(output, 'flow-narrow-light.png'), fullPage: true });

    await page.goto(fixtures['regions-en'].url);
    assert(await page.locator('.ide-controls').isHidden(), 'unordered charts must not have step controls');
    const beforeWidths = await page.locator('.ide-fill').evaluateAll(elements => elements.map(e => e.style.width));
    await page.locator('[data-item="south"]').click();
    assert.equal(await page.locator('.ide-explanation').textContent(), fixtures['regions-en'].model.items[2].explanation);
    assert.equal(await page.locator('.ide-detail-title').textContent(), 'South');
    assert.deepEqual(await page.locator('.ide-fill').evaluateAll(elements => elements.map(e => e.style.width)), beforeWidths, 'selection must not change numerical values or scale');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: path.join(output, 'bars-narrow-light.png'), fullPage: true });
    await page.setViewportSize({ width: 736, height: 900 });
    await page.emulateMedia({ reducedMotion: 'no-preference', colorScheme: 'dark' });
    await page.locator('[data-item="central"]').focus();
    await page.keyboard.press('Space');
    assert.equal(await page.locator('.ide-root').getAttribute('data-selected'), 'central');
    assert.equal(await page.locator('.ide-root').getAttribute('data-animating'), 'true');
    await page.waitForFunction(() => document.querySelector('.ide-root').dataset.animating === 'false');
    await page.screenshot({ path: path.join(output, 'bars-dark.png'), fullPage: true });

    await page.goto(fixtures['order-review-en'].url);
    await page.setViewportSize({ width: 320, height: 900 });
    await page.locator('[data-item="notify-customer"]').click();
    assert.equal(await page.locator('.ide-explanation').textContent(), fixtures['order-review-en'].model.items[3].explanation);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const crossesUnrelatedNode = await page.evaluate(() => {
      const nodes = [...document.querySelectorAll('[data-item]')];
      return [...document.querySelectorAll('.ide-edge')].some(edge => {
        const matrix = edge.getScreenCTM();
        const length = edge.getTotalLength();
        const unrelated = nodes.filter(node => node.dataset.item !== edge.dataset.from && node.dataset.item !== edge.dataset.to).map(node => node.getBoundingClientRect());
        for (let distance = 0; distance <= length; distance += 2) {
          const point = edge.getPointAtLength(distance).matrixTransform(matrix);
          if (unrelated.some(rect => point.x > rect.left && point.x < rect.right && point.y > rect.top && point.y < rect.bottom)) return true;
        }
        return false;
      });
    });
    assert.equal(crossesUnrelatedNode, false, 'branch edges must bypass unrelated nodes after wrapping');
    await page.screenshot({ path: path.join(output, 'branch-narrow.png'), fullPage: true });

    const statePage = await browser.newPage();
    await statePage.addInitScript(() => {
      window.savedStates = [];
      window.openai = { widgetState: { modelContent: { explainer: { title: 'Orders by region', language: 'en', selectedId: 'south' } } }, setWidgetState: state => { window.savedStates.push(state); return Promise.resolve(); } };
    });
    await statePage.goto(fixtures['regions-en'].url);
    assert.equal(await statePage.locator('.ide-root').getAttribute('data-selected'), 'south');
    assert.equal(await statePage.evaluate(() => window.savedStates.length), 0, 'do not save on initial rendering');
    await statePage.locator('[data-item="central"]').click();
    assert.equal(await statePage.evaluate(() => window.savedStates.at(-1).modelContent.explainer.selectedId), 'central');
    assert.deepEqual(errors, []);
    assert.deepEqual(remoteRequests, [], 'examples must be self-contained');
    console.log('PASS: flow, chart, branching, animation, rapid selection, keyboard, reduced motion, 320px, host state, no network');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
