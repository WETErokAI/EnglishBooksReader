"""
Сервис обработки изображений обложек.

Функциональность:
- Сохранение оригинальной обложки
- Создание миниатюры 200x300 через Pillow
"""

from pathlib import Path
from typing import Optional

from PIL import Image
import io

# Размер миниатюры
THUMBNAIL_SIZE = (200, 300)


class CoverProcessor:
    """Обработчик обложек книг."""

    @staticmethod
    def save_cover(cover_data: bytes, output_path: Path, base_path: Path) -> str:
        """Сохранить обложку на диск.

        Args:
            cover_data: Байты изображения.
            output_path: Полный путь для сохранения.
            base_path: Базовый путь хранилища обложек (для относительного пути).

        Returns:
            Относительный путь к сохранённому файлу относительно base_path.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(cover_data)
        # Возвращаем относительный путь от base_path
        return str(output_path.relative_to(base_path))

    @staticmethod
    def create_thumbnail(
        cover_data: bytes,
        output_path: Path,
        base_path: Path,
        size: tuple[int, int] = THUMBNAIL_SIZE,
    ) -> Optional[str]:
        """Создать и сохранить миниатюру обложки.

        Args:
            cover_data: Байты оригинального изображения.
            output_path: Путь для сохранения миниатюры.
            base_path: Базовый путь хранилища обложек (для относительного пути).
            size: Целевой размер (width, height).

        Returns:
            Относительный путь к миниатюре или None если не удалось создать.
        """
        try:
            image = Image.open(io.BytesIO(cover_data))

            # Конвертируем в RGB если необходимо (RGBA, P mode и т.д.)
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Thumbnail сохраняет aspect ratio
            image.thumbnail(size, Image.Resampling.LANCZOS)

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Сохраняем как JPEG
            if output_path.suffix.lower() not in (".jpg", ".jpeg"):
                output_path = output_path.with_suffix(".jpg")

            image.save(str(output_path), "JPEG", quality=85)
            return str(output_path.relative_to(base_path))

        except Exception:
            # Если не удалось создать миниатюру — не критично
            return None

    @staticmethod
    def process_cover(
        cover_data: bytes,
        cover_path: Path,
        thumbnail_path: Path,
        base_path: Path,
    ) -> tuple[Optional[str], Optional[str]]:
        """Полная обработка обложки: сохранение + миниатюра.

        Args:
            cover_data: Байты изображения.
            cover_path: Путь для оригинальной обложки.
            thumbnail_path: Путь для миниатюры.
            base_path: Базовый путь хранилища (для относительных путей).

        Returns:
            Кортеж (cover_path, thumbnail_path) или (None, None).
        """
        saved_cover = CoverProcessor.save_cover(cover_data, cover_path, base_path)
        saved_thumb = CoverProcessor.create_thumbnail(cover_data, thumbnail_path, base_path)
        return saved_cover, saved_thumb
