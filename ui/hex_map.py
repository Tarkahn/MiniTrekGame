import pygame
import math


class HexGrid:
    """A flat-topped hex grid that creates a proper honeycomb pattern."""
    
    def __init__(self, rows, cols, map_x, map_y, map_size):
        self.rows = rows
        self.cols = cols
        self.map_x = map_x
        self.map_y = map_y
        self.map_size = map_size
        
        # For flat-topped hexes:
        # Width = 2 * radius
        # Height = sqrt(3) * radius
        # Horizontal spacing = 3/2 * radius (hexes overlap horizontally)
        # Vertical spacing = sqrt(3) * radius (hexes touch vertically)
        
        # Calculate the radius that fits the grid perfectly
        # Grid width = radius * (3 * cols + 1) / 2
        # Grid height = radius * sqrt(3) * (rows + 0.5)
        
        radius_by_width = (map_size * 0.95) / ((3 * cols + 1) / 2)
        radius_by_height = (map_size * 0.95) / \
            (math.sqrt(3) * (rows + 0.5))
        
        self.radius = min(radius_by_width, radius_by_height)
        
        # Calculate actual grid dimensions
        self.grid_width = self.radius * (3 * cols + 1) / 2
        self.grid_height = self.radius * math.sqrt(3) * (rows + 0.5)
        
        # Center the grid in the map area
        self.offset_x = map_x + (map_size - self.grid_width) / 2
        self.offset_y = map_y + (map_size - self.grid_height) / 2

    @property
    def hex_size(self):
        """Return the radius of a hex (for compatibility with code expecting hex_size)."""
        return self.radius
    
    def get_hex_center(self, col, row):
        """Get the pixel coordinates of a hex center for flat-topped hexes."""
        x = self.offset_x + self.radius + col * 1.5 * self.radius
        y = (self.offset_y + self.radius * math.sqrt(3) / 2 +
             row * self.radius * math.sqrt(3))
        
        # Offset odd columns up by half a hex height
        if col % 2 == 1:
            y -= self.radius * math.sqrt(3) / 2
            
        return x, y
    
    def draw_hex(self, surface, center_x, center_y, color, filled=False):
        """Draw a single flat-topped hexagon."""
        points = []
        for i in range(6):
            # For flat-topped hex, start at 0 degrees
            angle = math.pi / 3 * i
            x = center_x + self.radius * math.cos(angle)
            y = center_y + self.radius * math.sin(angle)
            points.append((x, y))
        
        if filled:
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.polygon(surface, color, points, 2)
    
    def draw_grid(self, surface, outline_color=(180, 180, 220), alpha=255):
        """Draw the entire hex grid with optional transparency."""
        if alpha < 255:
            # Create a temporary surface for alpha blending
            temp_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            for row in range(self.rows):
                for col in range(self.cols):
                    cx, cy = self.get_hex_center(col, row)
                    # Draw on temp surface with alpha
                    color_with_alpha = (*outline_color, alpha)
                    self.draw_hex_with_alpha(temp_surface, cx, cy, color_with_alpha)
            # Blit the temp surface to the main surface
            surface.blit(temp_surface, (0, 0))
        else:
            # Original drawing method for full opacity
            for row in range(self.rows):
                for col in range(self.cols):
                    cx, cy = self.get_hex_center(col, row)
                    self.draw_hex(surface, cx, cy, outline_color)
    
    def draw_hex_with_alpha(self, surface, center_x, center_y, color_with_alpha):
        """Draw a single flat-topped hexagon with alpha."""
        points = []
        for i in range(6):
            # For flat-topped hex, start at 0 degrees
            angle = math.pi / 3 * i
            x = center_x + self.radius * math.cos(angle)
            y = center_y + self.radius * math.sin(angle)
            points.append((x, y))
        
        # Draw with alpha
        pygame.draw.polygon(surface, color_with_alpha, points, 2)
    
    def pixel_to_hex(self, px, py):
        """Convert pixel coordinates to hex grid coordinates."""
        # Adjust for grid offset
        px -= self.offset_x
        py -= self.offset_y
        
        # For flat-topped hexes
        # This is an approximation that works well enough for clicking
        col = int((px - self.radius / 2) / (1.5 * self.radius))
        
        if col % 2 == 0:
            row = int((py - self.radius * math.sqrt(3) / 2) /
                      (self.radius * math.sqrt(3)))
        else:
            row = int(py / (self.radius * math.sqrt(3)))
        
        # Bounds check
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return None, None
            
        # Refine by checking distance to nearby hex centers
        best_col, best_row = col, row
        best_dist = float('inf')
        
        # Check current hex and immediate neighbors
        for dc in range(-1, 2):
            for dr in range(-1, 2):
                check_col = col + dc
                check_row = row + dr

                if (0 <= check_col < self.cols and
                        0 <= check_row < self.rows):
                    cx, cy = self.get_hex_center(check_col, check_row)
                    dist = math.hypot(px + self.offset_x - cx,
                                      py + self.offset_y - cy)
                    if dist < best_dist:
                        best_dist = dist
                        best_col = check_col
                        best_row = check_row
        
        return best_col, best_row
    
    def draw_fog_hex(self, surface, center_x, center_y, color=(200, 200, 200), alpha=153):
        """Draw a filled hexagon with alpha (for fog-of-war), efficiently."""
        # Create a small surface just large enough for the hex
        hex_diameter = int(self.radius * 2) + 4  # +4 for anti-aliasing margin
        fog_surf = pygame.Surface((hex_diameter, hex_diameter), pygame.SRCALPHA)
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = hex_diameter // 2 + self.radius * math.cos(angle)
            y = hex_diameter // 2 + self.radius * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(
            fog_surf, (*color, alpha), points
        )
        # Blit the fog surface centered on the hex
        blit_x = int(center_x - hex_diameter // 2)
        blit_y = int(center_y - hex_diameter // 2)
        surface.blit(fog_surf, (blit_x, blit_y))


def create_hex_grid_for_map(map_x, map_y, map_size, rows=20, cols=20):
    """Create a hex grid that fits nicely in the given map area."""
    return HexGrid(rows, cols, map_x, map_y, map_size)


# Test the grid
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((900, 900))
    pygame.display.set_caption("Hex Grid Test - Honeycomb Pattern")
    clock = pygame.time.Clock()
    
    # Create a test grid
    grid = create_hex_grid_for_map(50, 50, 800)
    
    running = True
    hover_hex = (None, None)
    
    print("Hex grid test running - move mouse to highlight hexes")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                hover_hex = grid.pixel_to_hex(mx, my)
        
        screen.fill((40, 40, 60))
        
        # Draw a border around the map area
        pygame.draw.rect(screen, (0, 255, 0), (50, 50, 800, 800), 2)
        
        # Draw the grid
        grid.draw_grid(screen)
        
        # Highlight hovered hex
        if hover_hex[0] is not None:
            cx, cy = grid.get_hex_center(hover_hex[0], hover_hex[1])
            grid.draw_hex(screen, cx, cy, (255, 255, 0), filled=True)
            # Show coordinates
            font = pygame.font.SysFont('arial', 14)  # Use smaller sans-serif font
            text = font.render(
                f"({hover_hex[0]}, {hover_hex[1]})", True, (255, 255, 255))
            screen.blit(text, (10, 10))
            
        # Draw some test objects at specific positions
        test_positions = [(0, 0), (19, 0), (0, 19), (19, 19), (10, 10)]
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                  (255, 255, 0), (255, 0, 255)]
        for (col, row), color in zip(test_positions, colors):
            cx, cy = grid.get_hex_center(col, row)
            pygame.draw.circle(screen, color, (int(cx), int(cy)), 8)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("Test complete") 