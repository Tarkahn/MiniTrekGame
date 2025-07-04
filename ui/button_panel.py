import pygame
from fonts import get_font

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 48
BUTTON_MARGIN = 16
PANEL_X = 1040  # Right side of 1280px window
PANEL_Y = 40

BUTTON_LABELS = ["Move", "Fire", "Scan", "End Turn"]

# Draws all control panel buttons and the map mode toggle button at the bottom
# Returns: (button_rects, toggle_btn_rect)
def draw_button_panel(
    surface,
    event_log_width,
    bottom_pane_y,
    button_w,
    button_h,
    button_gap,
    font,
    color,
    color_text,
    map_mode,
    toggle_btn_w,
    toggle_btn_h,
    toggle_btn_y
):
    """
    Draws all control panel buttons and the map mode toggle button at the bottom.
    Returns: (button_rects, toggle_btn_rect)
    """
    button_rects = []
    # Regular buttons at the top
    for i, label in enumerate(BUTTON_LABELS):
        bx = event_log_width + 40
        by = bottom_pane_y + 30 + i * (button_h + button_gap)
        btn_rect = pygame.Rect(bx, by, button_w, button_h)
        button_rects.append(btn_rect)
        pygame.draw.rect(surface, color, btn_rect, border_radius=8)
        btn_label = font.render(label, True, color_text)
        surface.blit(btn_label, (bx + 18, by + 8))
    # Toggle map mode button at the bottom
    toggle_btn_x = event_log_width + 40
    toggle_btn_y = (
        bottom_pane_y + 30 + len(BUTTON_LABELS) * (button_h + button_gap)
        + button_gap
    )
    # Use short labels
    label = 'System Map' if map_mode == 'sector' else 'Sector Map'
    toggle_btn_rect = pygame.Rect(toggle_btn_x, toggle_btn_y, button_w, button_h)
    pygame.draw.rect(surface, color, toggle_btn_rect, border_radius=8)
    # Use a smaller font for the toggle button
    small_font = pygame.font.SysFont(None, 22)
    btn_label = small_font.render(label, True, color_text)
    # Center the label in the button
    label_rect = btn_label.get_rect(center=toggle_btn_rect.center)
    surface.blit(btn_label, label_rect)
    # Debug: Draw a bright yellow rectangle at the toggle button's position
    pygame.draw.rect(surface, (255, 255, 0), toggle_btn_rect, 3)
    # Print the toggle button's position and size
    print(
        f"Toggle button at x={toggle_btn_x}, y={toggle_btn_y}, "
        f"w={button_w}, h={button_h}"
    )
    return button_rects, toggle_btn_rect

# Handles button press/release events
# Returns: (button_pressed, toggle_btn_pressed, clicked_index, toggle_clicked)
def handle_button_events(
    event,
    button_rects,
    toggle_btn_rect,
    button_pressed,
    toggle_btn_pressed
):
    """
    Handles button press/release events.
    Returns: (button_pressed, toggle_btn_pressed, clicked_index, toggle_clicked)
    """
    clicked_index = None
    toggle_clicked = False
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_pos = pygame.mouse.get_pos()
        for i, btn_rect in enumerate(button_rects):
            if btn_rect.collidepoint(mouse_pos):
                button_pressed[i] = True
        if toggle_btn_rect.collidepoint(mouse_pos):
            toggle_btn_pressed[0] = True
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        mouse_pos = pygame.mouse.get_pos()
        for i, btn_rect in enumerate(button_rects):
            if button_pressed[i] and btn_rect.collidepoint(mouse_pos):
                clicked_index = i
            button_pressed[i] = False
        if toggle_btn_pressed[0] and toggle_btn_rect.collidepoint(mouse_pos):
            toggle_clicked = True
        toggle_btn_pressed[0] = False
    return button_pressed, toggle_btn_pressed, clicked_index, toggle_clicked

class ButtonPanel:
    def __init__(self):
        self.font = get_font(22)
        self.buttons = []
        for i, label in enumerate(BUTTON_LABELS):
            rect = pygame.Rect(
                PANEL_X,
                PANEL_Y + i * (BUTTON_HEIGHT + BUTTON_MARGIN),
                BUTTON_WIDTH,
                BUTTON_HEIGHT
            )
            self.buttons.append({'label': label, 'rect': rect, 'hover': False})

    def draw(self, surface):
        for btn in self.buttons:
            color = (80, 80, 120) if btn['hover'] else (40, 40, 60)
            pygame.draw.rect(surface, color, btn['rect'], border_radius=10)
            pygame.draw.rect(
                surface, (255, 204, 0), btn['rect'], 2, border_radius=10
            )
            text = self.font.render(btn['label'], True, (255, 204, 0))
            text_rect = text.get_rect(center=btn['rect'].center)
            surface.blit(text, text_rect)

    def handle_mouse_motion(self, pos):
        for btn in self.buttons:
            btn['hover'] = btn['rect'].collidepoint(pos)

    def handle_mouse_click(self, pos):
        for i, btn in enumerate(self.buttons):
            if btn['rect'].collidepoint(pos):
                return i, btn['label']  # Return index and label
        return None, None 