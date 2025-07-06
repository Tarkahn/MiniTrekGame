import pygame
from fonts import get_font

BOX_X = 20
BOX_Y = 650
BOX_WIDTH = 1240
BOX_HEIGHT = 130
PADDING = 12
MAX_MESSAGES = 100

class MessageBox:
    def __init__(self):
        self.font = get_font(20)
        self.messages = []
        self.scroll = 0  # 0 = bottom (latest)

    def add_message(self, text):
        self.messages.append(text)
        if len(self.messages) > MAX_MESSAGES:
            self.messages = self.messages[-MAX_MESSAGES:]
        self.scroll = 0  # Auto-scroll to bottom

    def draw(self, surface):
        pygame.draw.rect(
            surface, (20, 20, 30), (BOX_X, BOX_Y, BOX_WIDTH, BOX_HEIGHT), border_radius=10
        )
        pygame.draw.rect(
            surface, (255, 204, 0), (BOX_X, BOX_Y, BOX_WIDTH, BOX_HEIGHT), 2, border_radius=10
        )
        # Calculate visible lines
        line_height = self.font.get_height() + 2
        max_lines = (BOX_HEIGHT - 2 * PADDING) // line_height
        start = max(0, len(self.messages) - max_lines - self.scroll)
        end = max(0, len(self.messages) - self.scroll)
        visible = self.messages[start:end]
        y = BOX_Y + PADDING
        for msg in visible:
            text = self.font.render(msg, True, (255, 204, 0))
            x = BOX_X + PADDING
            pos = (x, y)
            surface.blit(text, pos)
            y += line_height

    def handle_mouse_wheel(self, dy):
        # dy: +1 for up, -1 for down
        line_height = self.font.get_height() + 2
        max_lines = (BOX_HEIGHT - 2 * PADDING) // line_height
        max_scroll = max(0, len(self.messages) - max_lines)
        self.scroll = min(max(0, self.scroll + dy), max_scroll) 