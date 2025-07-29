import os
import pygame

# Font paths
FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'assets', 'fonts'
)

FONT_REGULAR = os.path.join(FONTS_DIR, 'EdgeOfTheGalaxyRegular-OVEa6.otf')
FONT_ITALIC = os.path.join(FONTS_DIR, 'EdgeOfTheGalaxyItalic-ZVJB3.otf')
FONT_POSTER = os.path.join(FONTS_DIR, 'EdgeOfTheGalaxyPoster-3zRAp.otf')
FONT_POSTER_ITALIC = os.path.join(FONTS_DIR, 'EdgeOfTheGalaxyPosterItalic-x3o1m.otf')

_font_cache = {}
_font_manager = None


def get_font(size, variant='regular'):
    """Get a font with the specified size and variant.
    
    Args:
        size: Font size
        variant: 'regular', 'italic', 'poster', or 'poster_italic'
    
    Returns:
        pygame.font.Font object
    """
    cache_key = (size, variant)
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    
    font_map = {
        'regular': FONT_REGULAR,
        'italic': FONT_ITALIC,
        'poster': FONT_POSTER,
        'poster_italic': FONT_POSTER_ITALIC
    }
    
    font_path = font_map.get(variant, FONT_REGULAR)
    
    try:
        font = pygame.font.Font(font_path, size)
        _font_cache[cache_key] = font
        return font
    except Exception as e:
        print(f"[FONTS] Failed to load {variant} font: {e}")
        # Fallback to system font
        font = pygame.font.SysFont('arial', size)
        _font_cache[cache_key] = font
        return font


class FontManager:
    """Manages fonts for the UI."""
    
    def __init__(self):
        # Font sizes
        self.sizes = {
            'small': 14,
            'medium': 18,
            'large': 24,
            'title': 32,
            'code': 16
        }
        
        # Load fonts
        self.fonts = {}
        self._load_fonts()
        
    def _load_fonts(self):
        """Load all font variants and sizes."""
        for size_name, size_value in self.sizes.items():
            if size_name == 'code':
                # Use monospace font for code
                try:
                    self.fonts['code'] = pygame.font.SysFont('consolas', size_value)
                except:
                    self.fonts['code'] = pygame.font.SysFont('monospace', size_value)
            else:
                self.fonts[size_name] = get_font(size_value, 'regular')
                
    def render_text(self, text: str, size: str = 'medium', 
                   color: tuple = (255, 255, 255)) -> pygame.Surface:
        """Render text with the specified size and color."""
        font = self.fonts.get(size, self.fonts['medium'])
        return font.render(text, True, color)
        
    def get_text_size(self, text: str, size: str = 'medium') -> tuple:
        """Get the size of rendered text."""
        font = self.fonts.get(size, self.fonts['medium'])
        return font.size(text)


def get_font_manager():
    """Get the global font manager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager