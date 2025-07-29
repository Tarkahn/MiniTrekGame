import pygame
import sys


def show_orbit_dialog(screen, font):
    """Show a popup dialog asking if player wants to orbit the planet."""
    # Dialog dimensions
    dialog_width = 400
    dialog_height = 150
    screen_width, screen_height = screen.get_size()
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    # Colors
    dialog_bg = (50, 50, 50)
    dialog_border = (200, 200, 200)
    button_bg = (100, 100, 100)
    button_hover = (150, 150, 150)
    text_color = (255, 255, 255)
    
    # Button dimensions
    button_width = 80
    button_height = 40
    yes_button_x = dialog_x + 80
    no_button_x = dialog_x + 240
    button_y = dialog_y + 90
    
    clock = pygame.time.Clock()
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Check button hover states
        yes_hover = (yes_button_x <= mouse_pos[0] <= yes_button_x + button_width and
                    button_y <= mouse_pos[1] <= button_y + button_height)
        no_hover = (no_button_x <= mouse_pos[0] <= no_button_x + button_width and
                   button_y <= mouse_pos[1] <= button_y + button_height)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if yes_hover:
                        return True
                    elif no_hover:
                        return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    return False
        
        # Draw dialog background
        pygame.draw.rect(screen, dialog_bg, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(screen, dialog_border, (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Draw text
        title_text = font.render("Planet Detected", True, text_color)
        title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
        screen.blit(title_text, title_rect)
        
        query_text = font.render("Enter standard orbit?", True, text_color)
        query_rect = query_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 60))
        screen.blit(query_text, query_rect)
        
        # Draw buttons
        yes_color = button_hover if yes_hover else button_bg
        no_color = button_hover if no_hover else button_bg
        
        pygame.draw.rect(screen, yes_color, (yes_button_x, button_y, button_width, button_height))
        pygame.draw.rect(screen, dialog_border, (yes_button_x, button_y, button_width, button_height), 2)
        
        pygame.draw.rect(screen, no_color, (no_button_x, button_y, button_width, button_height))
        pygame.draw.rect(screen, dialog_border, (no_button_x, button_y, button_width, button_height), 2)
        
        # Draw button text
        yes_text = font.render("Yes (Y)", True, text_color)
        yes_rect = yes_text.get_rect(center=(yes_button_x + button_width // 2, button_y + button_height // 2))
        screen.blit(yes_text, yes_rect)
        
        no_text = font.render("No (N)", True, text_color)
        no_rect = no_text.get_rect(center=(no_button_x + button_width // 2, button_y + button_height // 2))
        screen.blit(no_text, no_rect)
        
        pygame.display.flip()
        clock.tick(60)