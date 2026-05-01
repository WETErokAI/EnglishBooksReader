---
name: ReaderPage virtualization with react-window v2
description: Виртуализация скролла в ReaderPage через react-window v2 List + AutoSizer + useDynamicRowHeight
type: project
---

Реализована виртуализация скролла для ReaderPage с использованием react-window v2.

**Зависимости:**
- `react-window@2.2.7` — виртуализированный список
- `react-virtualized-auto-sizer` — автоматический расчёт размеров контейнера

**Архитектура:**

1. **ReaderPage** — основной компонент:
   - `AutoSizer` (через `renderProp`) измеряет доступную высоту/ширину
   - `List` из react-window v2 рендерит только видимые чанки
   - `useDynamicRowHeight({ defaultRowHeight: 600 })` — переменные высоты строк
   - `listApiRef` — ref с методом `scrollToRow()` для клавиатурной навигации
   - `chunkRefs` — Map<chunk_index, DOM element> для IntersectionObserver
   - `IntersectionObserver` с `threshold: 0.3` определяет активный чанк

2. **VirtualChunkRow** — строка списка:
   - Принимает `style` от react-window (top, width, height)
   - Передаёт DOM-элемент родителю через `registerRef`
   - Содержит `data-chunk-index` для IntersectionObserver

3. **useChunkLoader** — остаётся без изменений (загружает все чанки одним запросом)

**react-window v2 API отличия от v1:**
- `List` вместо `FixedSizeList`/`VariableSizeList`
- `rowComponent` вместо `children` для рендера строк
- `rowHeight` принимает объект от `useDynamicRowHeight`
- `scrollToRow({ index, align, behavior })` вместо `scrollToItem(index, align)`
- `listRef` вместо `ref`
- `renderProp` вместо `children` у `AutoSizer`
- `style={{ width, height }}` вместо пропсов `width`/`height`

**Клавиатурная навигация:**
- `ArrowRight/Down` → `scrollToRow({ index: next, align: 'start', behavior: 'smooth' })`
- `ArrowLeft/Up` → `scrollToRow({ index: prev, align: 'start', behavior: 'smooth' })`
- `Escape` → возврат в `/library`

**Производительность:**
- В DOM только видимые чанки (+ буфер react-window)
- Скролл-бар полный (знаем totalChunks)
- Высота каждого чанка измеряется автоматически через `observeRowElements`
