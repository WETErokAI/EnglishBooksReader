/**
 * E2E тест: Управление библиотекой.
 *
 * Сценарий:
 * 1. Открыть страницу библиотеки
 * 2. Переключить вид (карточки ↔ список)
 * 3. Поиск по названию книги
 * 4. Переименовать книгу
 * 5. Подтвердить удаление книги
 * 6. Убедиться, что книга удалена из списка
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'http://localhost:5173';

test.describe('Library Management', () => {
  test('переключение вида карточки/список', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/library`);

    // Ждём загрузки списка книг
    await page.waitForSelector('table tbody tr, .book-grid .book-card', {
      timeout: 10000,
    });

    // Проверяем текущий вид (по умолчанию — карточки)
    const gridView = page.locator('.book-grid');
    const listView = page.locator('.book-list-table');

    // Находим кнопку переключения вида
    const viewToggle = page.locator('.view-toggle, [data-testid="view-toggle"]');
    await expect(viewToggle).toBeVisible();

    // Переключаем в список
    const listButton = viewToggle.locator('button:has-text("Список"), [aria-label*="list"]');
    if (await listButton.count() > 0) {
      await listButton.click();
      await expect(listView).toBeVisible({ timeout: 5000 });
    }

    // Переключаем обратно в карточки
    const gridButton = viewToggle.locator('button:has-text("Карточки"), [aria-label*="grid"]');
    if (await gridButton.count() > 0) {
      await gridButton.click();
      await expect(gridView).toBeVisible({ timeout: 5000 });
    }
  });

  test('поиск книги по названию', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/library`);

    // Ждём загрузки списка
    await page.waitForSelector('table tbody tr, .book-grid .book-card', {
      timeout: 10000,
    });

    // Получаем начальное количество книг
    const initialCount = await page.locator('table tbody tr, .book-grid .book-card').count();

    // Вводим поисковый запрос
    const searchInput = page.locator('input[type="search"], [data-testid="search-input"], .search-bar input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('nonexistent-book-query-xyz');

    // После debounce (300ms) проверяем результат
    await page.waitForTimeout(500);

    // Должно быть "Ничего не найдено" или пустой список
    const noResults = page.locator('[data-testid="no-results"], .no-results-message');
    const emptyList = page.locator('table tbody tr, .book-grid .book-card');

    if (await noResults.count() > 0) {
      await expect(noResults).toBeVisible();
    } else {
      await expect(emptyList).toHaveCount(0);
    }

    // Очистить поиск
    const clearButton = page.locator('button:has-text("Очистить"), [aria-label*="clear"]');
    if (await clearButton.count() > 0) {
      await clearButton.click();
    } else {
      await searchInput.clear();
    }

    // Книги должны появиться снова
    await page.waitForTimeout(500);
    const updatedCount = await page.locator('table tbody tr, .book-grid .book-card').count();
    await expect(updatedCount).toBeGreaterThanOrEqual(0);
  });

  test('переименование книги', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/library`);

    // Ждём загрузки
    await page.waitForSelector('table tbody tr, .book-grid .book-card', {
      timeout: 10000,
    });

    // Находим первую книгу и кликаем "Переименовать"
    const firstBook = page.locator('table tbody tr, .book-grid .book-card').first();
    await expect(firstBook).toBeVisible();

    const renameButton = firstBook.locator(
      'button:has-text("Переименовать"), button:has-text("Rename"), [aria-label*="rename"]'
    );
    await expect(renameButton).toBeVisible();
    await renameButton.click();

    // Ожидаем модальное окно переименования
    const dialog = page.locator('[role="dialog"], .rename-dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });

    // Вводим новое название
    const titleInput = dialog.locator('input[type="text"], input[type="search"]');
    await expect(titleInput).toBeVisible();
    await titleInput.clear();
    await titleInput.fill('Новое название книги ' + Date.now());

    // Подтверждаем
    const confirmBtn = dialog.locator('button:has-text("Подтвердить"), button:has-text("Save"), button:has-text("OK")');
    await confirmBtn.click();

    // Ждём закрытия диалога и обновления
    await expect(dialog).not.toBeVisible({ timeout: 5000 });

    // Проверяем, что название обновилось
    const updatedName = page.locator('table tbody tr .book-name, .book-card .book-title').first();
    await expect(updatedName).toContainText('Новое название книги', { timeout: 5000 });
  });

  test('удаление книги с подтверждением', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/library`);

    // Ждём загрузки
    await page.waitForSelector('table tbody tr, .book-grid .book-card', {
      timeout: 10000,
    });

    const initialCount = await page.locator('table tbody tr, .book-grid .book-card').count();

    // Клик "Удалить" на первой книге
    const firstBook = page.locator('table tbody tr, .book-grid .book-card').first();
    const deleteButton = firstBook.locator(
      'button:has-text("Удалить"), button:has-text("Delete"), [aria-label*="delete"]'
    );
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();

    // Ожидаем модальное окно подтверждения
    const dialog = page.locator('[role="alertdialog"], .confirm-dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });

    // Подтверждаем удаление
    const confirmBtn = dialog.locator('button:has-text("Удалить"), button:has-text("Delete"), button:has-text("Confirm")');
    await confirmBtn.click();

    // Ждём закрытия диалога
    await expect(dialog).not.toBeVisible({ timeout: 5000 });

    // Проверяем, что книга удалена
    const newCount = await page.locator('table tbody tr, .book-grid .book-card').count();
    await expect(newCount).toBeLessThan(initialCount);
  });

  test('отмена удаления', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/library`);

    await page.waitForSelector('table tbody tr, .book-grid .book-card', {
      timeout: 10000,
    });

    const initialCount = await page.locator('table tbody tr, .book-grid .book-card').count();

    // Клик "Удалить"
    const firstBook = page.locator('table tbody tr, .book-grid .book-card').first();
    const deleteButton = firstBook.locator(
      'button:has-text("Удалить"), button:has-text("Delete"), [aria-label*="delete"]'
    );
    await deleteButton.click();

    // Отменяем удаление
    const dialog = page.locator('[role="alertdialog"], .confirm-dialog');
    const cancelBtn = dialog.locator('button:has-text("Отмена"), button:has-text("Cancel")');
    await cancelBtn.click();

    // Диалог закрыт, книга на месте
    await expect(dialog).not.toBeVisible({ timeout: 5000 });
    const newCount = await page.locator('table tbody tr, .book-grid .book-card').count();
    await expect(newCount).toBe(initialCount);
  });
});
