import os
import pygame

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'assets', 'fonts', 'EdgeOfTheGalaxyRegular-OVEa6.otf'
)

_fallback_font = None


def get_font(size):
    global _fallback_font
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        if _fallback_font is None:
            _fallback_font = pygame.font.SysFont('arial', size)
        return _fallback_font 