from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
FONT_DIR = ASSET_DIR / "fonts"
STORY_FONT_PATH = FONT_DIR / "LXGWWenKai-Regular.ttf"
UI_FONT_PATH = FONT_DIR / "ZCOOLKuaiLe-Regular.ttf"


def load_font(size, path=None, fallback_names=()):
    if path and path.exists():
        try:
            return pygame.font.Font(str(path), int(size))
        except pygame.error:
            pass
    for name in fallback_names:
        matched_path = pygame.font.match_font(name)
        if matched_path:
            return pygame.font.Font(matched_path, int(size))
    return pygame.font.Font(None, int(size))


def brand_font(size):
    return load_font(
        size,
        UI_FONT_PATH,
        (
            "ZCOOL KuaiLe",
            "LXGW WenKai",
            "PingFang SC",
            "Hiragino Sans GB",
            "Heiti SC",
            "Microsoft YaHei",
            "Arial Unicode MS",
        ),
    )


def story_font(size):
    return load_font(
        size,
        STORY_FONT_PATH,
        (
            "LXGW WenKai",
            "PingFang SC",
            "Hiragino Sans GB",
            "Heiti SC",
            "Microsoft YaHei",
            "Arial Unicode MS",
        ),
    )


def ui_font(size):
    return load_font(
        size,
        UI_FONT_PATH,
        (
            "ZCOOL KuaiLe",
            "LXGW WenKai",
            "PingFang SC",
            "Hiragino Sans GB",
            "Heiti SC",
            "Microsoft YaHei",
            "Arial Unicode MS",
        ),
    )
