import pygame

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 48
BUTTON_MARGIN = 16
PANEL_X = 1040  # Right side of 1280px window
PANEL_Y = 40

BUTTON_LABELS = ["Move", "Fire", "Torpedo", "Scan", "Repairs"]

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
    toggle_btn_y_param
):
    """
    Draws all control panel buttons and the map mode toggle button at the bottom.
    Returns: (button_rects, toggle_btn_rect)
    """
    button_rects = []
    # Regular buttons with proper spacing from Control Panel label
    # Using 40px offset to fit 5 buttons in the control panel area
    for i, label in enumerate(BUTTON_LABELS):
        bx = event_log_width + 40
        by = bottom_pane_y + 40 + i * (button_h + button_gap)  # Use 40px spacing from top
        btn_rect = pygame.Rect(bx, by, button_w, button_h)
        button_rects.append(btn_rect)
        pygame.draw.rect(surface, color, btn_rect, border_radius=6)
        btn_label = font.render(label, True, color_text)
        # Center text vertically in smaller button
        text_y = by + (button_h - btn_label.get_height()) // 2
        surface.blit(btn_label, (bx + 18, text_y))
    # Toggle map mode button - place it to the right of the main buttons
    toggle_btn_x = event_log_width + 40 + button_w + 20  # Next to the regular buttons
    # Use the passed-in y position
    toggle_btn_y = toggle_btn_y_param
    # Use short labels
    label = 'System Map' if map_mode == 'sector' else 'Sector Map'
    toggle_btn_rect = pygame.Rect(toggle_btn_x, toggle_btn_y, toggle_btn_w, toggle_btn_h)
    pygame.draw.rect(surface, color, toggle_btn_rect, border_radius=8)
    # Use a smaller sans-serif font for the toggle button
    small_font = pygame.font.SysFont('arial', 14)
    btn_label = small_font.render(label, True, color_text)
    # Center the label in the button
    label_rect = btn_label.get_rect(center=toggle_btn_rect.center)
    surface.blit(btn_label, label_rect)
    # Debug: Draw a bright yellow rectangle at the toggle button's position
    # pygame.draw.rect(surface, (255, 255, 0), toggle_btn_rect, 3)
    # Print the toggle button's position and size
    # print(
    #     f"Toggle button at x={toggle_btn_x}, y={toggle_btn_y}, "
    #     f"w={button_w}, h={button_h}"
    # )
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
        self.font = pygame.font.SysFont('arial', 16)  # Sans-serif font
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