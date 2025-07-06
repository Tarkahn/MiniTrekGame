import pygame
import sys
import os

ui_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../ui')
)
sys.path.insert(0, ui_path)
from fonts import get_font

pygame.init()

WIDTH, HEIGHT = 600, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Font Test')

font = get_font(48)
text = font.render('EdgeOfTheGalaxy Font Test', True, (255, 204, 0))
rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
    screen.fill((20, 20, 30))
    screen.blit(text, rect)
    pygame.display.flip()

pygame.quit() 