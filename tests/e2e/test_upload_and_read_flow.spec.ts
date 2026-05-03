/**
 * E2E тест: Загрузка книги и начало чтения.
 *
 * Сценарий:
 * 1. Открыть страницу загрузки
 * 2. Выбрать файл книги для загрузки
 * 3. Дождаться успешной загрузки
 * 4. Перейти в библиотеку
 * 5. Открыть книгу для чтения
 * 6. Убедиться, что контент чанков загружен
 */

import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:5173';

test.describe('Upload and Read Flow', () => {
  test('пользователь загружает книгу и открывает её для чтения', async ({
    page,
  }) => {
    // 1. Открыть страницу загрузки
    await page.goto(`${FRONTEND_URL}/upload`);
    await expect(page.locator('h1, h2')).toContainText(
      ['Загрузить книгу', 'Upload', /загруз/i],
      { timeout: 10000 }
    );

    // 2. Выбрать файл книги (drag-and-drop или input)
    // Используем тестовый файл из fixtures
    const filePath = 'fixtures/pg84.epub';
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('input[type="file"]').setInputFiles(filePath);
    // Если fileChooser не пойман, пробуем через drag-and-drop
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);

    // 3. Дождаться успешной загрузки
    // Ожидаем сообщение об успехе или переход в библиотеку
    await page.waitForURL(`${FRONTEND_URL}/library`, { timeout: 30000 });
    await expect(page.locator('table tbody tr, .book-card')).first().toBeVisible({
      timeout: 15000,
    });

    // 4. Убедиться, что книга появилась в списке
    const firstBook = page.locator('table tbody tr, .book-card').first();
    await expect(firstBook).toBeVisible();

    // 5. Кликнуть "Читать" на карточке книги
    const readButton = firstBook.locator('button:has-text("Читать"), [aria-label*="read"], [data-testid*="read"]');
    if (await readButton.count() > 0) {
      await readButton.click();
    } else {
      // Клик по названию книги
      await firstBook.locator('a:has-text("Читать"), a:has-text("read"), a:has-text("Читать")').first().click();
    }

    // 6. Дождаться загрузки ReaderPage
    await page.waitForURL(/\/books\/[a-f0-9-]+\/read/, { timeout: 15000 });
    await expect(page.locator('.reader-page, #reader, [data-testid="reader"]')).toBeVisible({
      timeout: 15000,
    });

    // 7. Убедиться, что чанки загружены (есть контент)
    const contentArea = page.locator('.reader-content, [data-testid="reader-content"], .chunk-container').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 8. Проверить индикатор прогресса чтения
    const progress = page.locator('.reading-progress, [data-testid="reading-progress"]');
    if (await progress.count() > 0) {
      await expect(progress).toBeVisible();
    }
  });

  test('ошибка при загрузке неподдерживаемого формата', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);

    // Попытка загрузить файл с неподдерживаемым расширением
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content'),
    });
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content'),
    });

    // Ожидаем сообщение об ошибке
    await expect(page.locator('.toast-error, [role="alert"], .error-message')).toBeVisible({
      timeout: 10000,
    });
  });

  test('ошибка при превышении размера файла', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);

    // Создаём большой файл (>50MB)
    const largeBuffer = Buffer.alloc(52 * 1024 * 1024 + 1024, 0); // 50MB + 1KB

    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('input[type="file"]').setInputFiles({
      name: 'large.epub',
      mimeType: 'application/epub+zip',
      buffer: largeBuffer,
    });
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'large.epub',
      mimeType: 'application/epub+zip',
      buffer: largeBuffer,
    });

    // Ожидаем сообщение об ошибке
    await expect(page.locator('.toast-error, [role="alert"], .error-message')).toBeVisible({
      timeout: 10000,
    });
  });
});
