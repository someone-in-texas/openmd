const fs = require('fs');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const {execFileSync} = require('child_process');
  const path = require('path');
  const output = execFileSync('python3', [path.join(__dirname, 'smoke.py'), '--keep-fixture'], {encoding:'utf8'});
  const fixture = JSON.parse(fs.readFileSync(output.trim().split('\n').pop()));
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(fixture.preview).href);
    await page.waitForSelector('#content h1', {timeout: 20000});
    assert.equal(await page.locator('#content h1').textContent(), 'Working copy');
    assert.match(await page.locator('#git-status').textContent(), /staged changes, unstaged changes, untracked files/);
    assert.equal(await page.locator('a', {hasText: 'CSV'}).evaluate(el => el.href), pathToFileURL(fixture.csv).href);
    assert.equal(await page.locator('a', {hasText: 'External'}).evaluate(el => el.href), 'https://example.com/test');
    await page.waitForFunction(() => [...document.querySelectorAll('#content img')].every(img => img.complete && img.naturalWidth === 20));
    const images = await page.locator('#content img').evaluateAll(imgs => imgs.map(i => i.currentSrc));
    assert.equal(images.length, 3);
    assert(images.every(url => url === pathToFileURL(fixture.image).href));
    assert.equal(await page.locator('a', {hasText: 'Section', exact:true}).evaluate(el => el.href), pathToFileURL(fixture.preview).href + '#results');
    await page.locator('a', {hasText: 'Section', exact:true}).click();
    assert(await page.locator('#results').evaluate(el => parseFloat(el.style.scrollMarginTop) > document.querySelector('header').getBoundingClientRect().height));
    assert.equal(page.url(), pathToFileURL(fixture.preview).href + '#results');
    await page.locator('a', {hasText: 'Malformed', exact:true}).click();
    await page.locator('#git-version').selectOption({label:'Last committed version (HEAD)'});
    assert.equal(await page.locator('#content h1').textContent(), 'Committed');
    assert.equal(await page.locator('#content #results').count(), 1);
    await page.locator('#git-version').selectOption({label:'Branch: feature/docs'});
    assert.equal(await page.locator('#content h1').textContent(), 'Branch version');
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', {value:{writeText: async text => {window.copied = text;}}});
    });
    await page.locator('[data-action="copy-markdown"]').click();
    assert.match(await page.evaluate(() => window.copied), /^# Branch version/);
    assert.equal(await page.locator('#git-version option', {hasText:'Branch: missing'}).isDisabled(), true);
    await page.locator('#git-version').selectOption('0');
    assert.equal(await page.locator('#content h1').textContent(), 'Working copy');
    await page.locator('[data-mode="dark"]').click();
    assert.equal(await page.locator('body').getAttribute('data-theme'), 'dark');
    const downloadPromise = page.waitForEvent('download');
    await page.locator('a', {hasText: 'CSV', exact:true}).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), 'results final.csv');
    assert.equal(await download.failure(), null);
    assert.deepEqual(errors, []);
    // With CDN requests blocked, versions still work using escaped plain text.
    const offline = await browser.newPage();
    offline.on('pageerror', e => errors.push(e.message));
    await offline.route('https://cdn.jsdelivr.net/**', route => route.abort());
    await offline.goto(pathToFileURL(fixture.preview).href);
    assert.match(await offline.locator('.fallback-markdown').textContent(), /^# Working copy/);
    await offline.locator('#git-version').selectOption({label:'Last committed version (HEAD)'});
    assert.match(await offline.locator('.fallback-markdown').textContent(), /^# Committed/);
    assert.match(await offline.locator('.fallback-markdown').textContent(), /__FILE_JSON__ and <\/script>/);
    assert.deepEqual(errors, []);

    // Regression: switching versions must not restore a stale bottom anchor
    // or let browser scroll anchoring move the view to the footer.
    for (const currentPage of [page, offline]) {
      await currentPage.evaluate(() => {
        SOURCE.git.versions.forEach((v, i) => {
          if (v.markdown !== null) v.markdown = '# Version ' + i + '\n' +
            'Paragraph of long content.\n\n'.repeat(i === 0 ? 200 : 100) + '\n## Bottom';
        });
      });
      await currentPage.locator('#git-version').selectOption('0');
      await currentPage.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      for (const hash of ['', '#bottom']) {
        await currentPage.evaluate(hash => {
          history.replaceState(null, '', location.pathname + hash);
          window.scrollTo(0, document.documentElement.scrollHeight * .6);
        }, hash);
        assert(await currentPage.evaluate(() => scrollY > 500));
        await currentPage.locator('#git-version').selectOption('1');
        await currentPage.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await currentPage.waitForFunction(() => scrollY === 0);
        assert.equal(await currentPage.evaluate(() => location.hash), '');
        await currentPage.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await currentPage.locator('#git-version').selectOption('0');
        await currentPage.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await currentPage.waitForFunction(() => scrollY === 0);
      }
    }
    assert.deepEqual(errors, []);
    console.log('PASS: Chromium rendering, local CSV download, Markdown/HTML/srcset images, anchors, branch/HEAD switching, selected-version copy, missing-file state, theme, CDN-offline fallback, scroll reset; no JS errors');
  } finally { await browser.close(); fs.rmSync(fixture.root, {recursive:true, force:true}); }
})().catch(e => { console.error(e); process.exitCode=1; });
