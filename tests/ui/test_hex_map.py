import pygame
import sys
import os

ui_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../ui')
)
sys.path.insert(0, ui_path)
from hex_map import HexMap

pygame.init()

WIDTH, HEIGHT = 1280, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Hex Map Test')

hex_map = HexMap()
highlighted = None

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            hex_coords = hex_map.pixel_to_hex(*pos)
            if hex_coords:
                if event.button == 1:  # Left click
                    highlighted = hex_coords
                    print(f"Left click: {hex_coords}")
                elif event.button == 3:  # Right click
                    hex_map.set_object(*hex_coords, 'X')
                    print(f"Right click: {hex_coords} (placed 'X')")

    screen.fill((20, 20, 30))
    hex_map.draw(screen)
    # Draw highlight
    if highlighted:
        x, y = hex_map.hex_to_pixel(*highlighted)
        pygame.draw.circle(screen, (0, 255, 255), (x, y), 10, 2)
    pygame.display.flip()

pygame.quit() 