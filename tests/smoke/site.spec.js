const { test, expect } = require('@playwright/test');

const REPRESENTATIVE_PATHS = [
  '/',
  '/zpp/',
  '/zpp/praktika/nekachestvennyy-tovar/',
  '/zpp/praktika/vozvrat-deneg-za-uslugu/',
  '/zpp/dela/9xUCtLJ9m3HR/',
  '/zpp/dela/xyw1pNsfewV8/',
];

const FORBIDDEN_UI_TOKENS = [
  'Прототип',
  'refund',
  'penalty_fine',
  'goods_defect_art18',
  'service_refusal_art32',
  'non_consumer_hold',
];

async function visibleText(page) {
  return (await page.locator('body').innerText()).replace(/\s+/g, ' ');
}

async function sitemapPaths(request, baseURL) {
  const response = await request.get('/sitemap.xml');
  expect(response.ok()).toBeTruthy();
  const xml = await response.text();
  const paths = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((match) => {
    const url = new URL(match[1]);
    return url.pathname;
  });
  expect(paths.length).toBeGreaterThan(200);
  expect(paths).toContain('/');
  expect(paths).toContain('/zpp/');
  expect(paths.some((path) => path.startsWith('/zpp/praktika/'))).toBeTruthy();
  expect(paths.some((path) => path.startsWith('/zpp/dela/'))).toBeTruthy();
  expect(paths.some((path) => path.startsWith('/praktika/'))).toBeFalsy();
  expect(paths.some((path) => path.startsWith('/dela/'))).toBeFalsy();
  expect(new Set(paths).size).toBe(paths.length);
  expect(baseURL).toBeTruthy();
  return paths;
}

test.describe('SSG smoke tests', () => {
  test('robots and sitemap are available', async ({ request, baseURL }) => {
    const robots = await request.get('/robots.txt');
    expect(robots.ok()).toBeTruthy();
    await expect(await robots.text()).toContain('Sitemap: https://sudpraktika-online.ru/sitemap.xml');

    const paths = await sitemapPaths(request, baseURL);
    expect(paths.length).toBeGreaterThanOrEqual(250);
  });

  test('all sitemap pages return successful responses', async ({ request, baseURL }) => {
    const paths = await sitemapPaths(request, baseURL);
    for (const path of paths) {
      const response = await request.get(path);
      expect(response.status(), `${path} should be available`).toBe(200);
    }
  });

  test('representative pages have one h1, canonical and no service tokens in visible UI', async ({ page }) => {
    for (const path of REPRESENTATIVE_PATHS) {
      await page.goto(path);
      await expect(page.locator('h1'), `${path} should have one h1`).toHaveCount(1);
      await expect(page.locator('link[rel="canonical"]'), `${path} should have canonical`).toHaveCount(1);

      const text = await visibleText(page);
      for (const token of FORBIDDEN_UI_TOKENS) {
        expect(text.includes(token), `${path} should not expose ${token}`).toBeFalsy();
      }
    }
  });

  test('home page exposes ZPP section', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Судпрактика Онлайн');
    await expect(page.getByRole('link', { name: /Дела о защите прав потребителей/ })).toBeVisible();
  });

  test('ZPP section page exposes situation navigation', async ({ page }) => {
    await page.goto('/zpp/');
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Первые страницы судебной практики');
    await expect(page.getByRole('link', { name: /Некачественный товар/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /Как вернуть товар, купленный онлайн/ })).toBeVisible();
  });

  test('situation page exposes filters, summary, recommendations and case cards', async ({ page }) => {
    await page.goto('/zpp/praktika/nekachestvennyy-tovar/');
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Некачественный товар');
    await expect(page.getByRole('heading', { name: 'Фильтры по делам' })).toBeVisible();
    await expect(page.locator('[data-filter]')).toHaveCount(5);
    await expect(page.getByRole('heading', { name: 'Краткое резюме практики' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Что показывает выборка и на что обратить внимание' })).toBeVisible();
    expect(await page.locator('[data-case-card]').count()).toBeGreaterThan(0);
    await expect(page.getByRole('link', { name: /Разобрать это дело/ }).first()).toBeVisible();
  });

  test('case page exposes story, result, source and legal analysis blocks', async ({ page }) => {
    await page.goto('/zpp/dela/9xUCtLJ9m3HR/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Итог дела' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'История дела простым языком' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Подробный правовой разбор' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Что важно учитывать' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Открыть судебный акт' })).toHaveAttribute('href', /sudact\.ru/);

    const text = await visibleText(page);
    expect(text.includes('Ошибки и риски')).toBeFalsy();
  });

  test('case story labels are rendered as headings consistently', async ({ page }) => {
    const paths = [
      '/zpp/dela/yz0M6YZip7Qn/',
      '/zpp/dela/GMjXio3dnCrR/',
    ];
    const labels = [
      'Кто участвовал',
      'Обстоятельства и развитие событий',
      'Результат для потребителя',
      'Итог суда',
      'Что сделано не так и как поступить правильно',
    ];

    for (const path of paths) {
      await page.goto(path);
      const story = page.locator('section.story-content').filter({ hasText: 'История дела простым языком' }).first();
      for (const label of labels) {
        await expect(story.getByRole('heading', { level: 4, name: label }), `${path}: ${label}`).toBeVisible();
        const plainParagraphExists = await story.locator('p').evaluateAll(
          (paragraphs, expectedLabel) => paragraphs.some((paragraph) => paragraph.textContent.trim() === `${expectedLabel}:`),
          label
        );
        expect(plainParagraphExists, `${path}: ${label} should not be rendered as a plain paragraph`).toBeFalsy();
      }
    }
  });

  test('legacy norm bullets render as legal notes with left rail', async ({ page }) => {
    await page.goto('/zpp/dela/BRRlQN72V9V6/');
    const legalAnalysis = page.locator('section.story-content').filter({ hasText: 'Подробный правовой разбор' }).first();
    await expect(legalAnalysis.getByRole('heading', { name: 'Нормы, на которые сослался суд' })).toBeVisible();

    const notes = legalAnalysis.locator('.md-note');
    expect(await notes.count()).toBeGreaterThan(10);
    await expect(notes.first()).toContainText('Значение в деле');

    const border = await notes.first().evaluate((node) => {
      const style = window.getComputedStyle(node);
      return {
        style: style.borderLeftStyle,
        width: style.borderLeftWidth,
      };
    });
    expect(border.style).not.toBe('none');
    expect(parseFloat(border.width)).toBeGreaterThan(0);
  });

  test('internal links on representative pages do not point to missing local pages', async ({ page, request, baseURL }) => {
    for (const path of REPRESENTATIVE_PATHS) {
      await page.goto(path);
      const hrefs = await page.locator('a[href]').evaluateAll((links) => links.map((link) => link.getAttribute('href')));
      const localPaths = [...new Set(
        hrefs
          .filter(Boolean)
          .filter((href) => !href.startsWith('http') && !href.startsWith('#') && !href.startsWith('mailto:'))
          .map((href) => new URL(href, new URL(path, baseURL)).pathname)
      )];

      for (const localPath of localPaths) {
        const response = await request.get(localPath);
        expect(response.status(), `${path} -> ${localPath}`).toBe(200);
      }
    }
  });
});
