# coding: utf8

import io
import json
import pathlib
import zipfile

from typing import Dict, IO

from PIL import Image

__version__ = "0.1.0a0"

REQUIRED_FIELDS = [
    "name",
    "identifier",
    "publisher",
]

# how big the images are, in bytes
STICKER_MAX_SIZE = 100 * 1024
TRAY_MAX_SIZE = 50 * 1024

# how big the images are, in pixels
STICKER_MAX_PIXELS = (512, 512)
TRAY_MAX_PIXELS = (96, 96)

# min/max number of stickers in a pack
STICKERS_PER_PACK = (3, 30)
STRING_MAX_LEN = 128
# how many emojis can be used to ID a sticker
EMOJI_MAX = 3


class StickerPackError(Exception):
    pass


class StickerPack:
    """A sticker pack.

    Args:
        name: The name of the sticker pack.
        author: The person who made the sticker pack.
        tray_image: The image to use for the sticker pack's icon as raw bytes.

    Raises:
        StickerPackError, if name or author is empty.
    """

    def __init__(self, name: str, author: str, tray_image: bytes):
        if not (name and author):
            raise StickerPackError("blank names are not allowed")

        self.name = name
        self.author = author

        self.stickers = []
        self.tray_image_buf = io.BytesIO(tray_image)
        tray_image = Image.open(self.tray_image_buf)

        if tray_image.size != TRAY_MAX_PIXELS:
            tray_image = tray_image.resize(TRAY_MAX_PIXELS)

        tray_image.save(self.tray_image_buf, "PNG")

    def add_sticker(self, image_data: bytes) -> None:
        """Add a sticker to this pack.

        Args:
            image_data: The image to add.
                If the format is not WebP or PNG, it will be converted to PNG.

        Raises:
            StickerPackError, if there are too many in the pack already.
        """

        if not len(self.stickers) <= STICKERS_PER_PACK[1]:
            raise StickerPackError("too many stickers")

        img_buf = io.BytesIO(image_data)
        img = Image.open(img_buf)

        if img.size != STICKER_MAX_PIXELS:
            img = img.resize(STICKER_MAX_PIXELS)

        self.stickers.append(img)

    def export(self, fp: IO) -> None:
        """Export this sticker pack as a zipfile.
        The file to export to should have a '.wastickers' extension.

        Args:
            fp: The file-like object to export this pack to.
        """

        with zipfile.ZipFile(fp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # write metadata first
            zf.writestr("author.txt", self.author)
            zf.writestr("title.txt", self.name)

            # tray image will always be the first image
            zf.writestr("0.png", self.tray_image_buf.getvalue())

            for count, sticker in enumerate(self.stickers, start=1):
                if sticker.format not in ["PNG", "WEBP"]:
                    sticker_format = "PNG"
                else:
                    sticker_format = sticker.format

                with zf.open(f"{count}.{sticker_format.lower()}", "w") as f:
                    sticker.save(f, sticker_format)
