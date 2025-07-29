import time


class GameState:
    """Centralized game state management."""
    
    def __init__(self):
        # Core game data
        self.systems = {}
        self.star_coords = {}
        self.lazy_object_coords = []
        self.planet_orbits = []
        self.current_system = None
        self.player_ship = None
        
        # Animation states
        self.planet_anim_state = {}
        
        # System map movement state
        self.system_ship_anim_x = None
        self.system_ship_anim_y = None
        self.system_dest_q = None
        self.system_dest_r = None
        self.system_ship_moving = False
        self.system_move_start_time = None
        self.system_move_duration_ms = 1000  # 1 second for system moves
        self.system_move_start_x = None
        self.system_move_start_y = None
        
        # Player ship orbital state
        self.player_orbiting_planet = False
        self.player_orbit_center = None  # Planet position (px, py)
        self.player_orbit_key = None     # (star, planet) key to track which planet we're orbiting
        self.player_orbit_radius = 60    # Orbit radius in pixels
        self.player_orbit_angle = 0.0    # Current angle
        self.player_orbit_speed = 0.4    # Radians per second
        
        # Phaser firing state
        self.selected_enemy = None
        self.phaser_animating = False
        self.phaser_anim_start = 0
        self.phaser_anim_duration = 500  # ms
        self.phaser_pulse_count = 5
        self.phaser_damage = 40
        self.phaser_range = 9
        
        # UI state
        self.last_debug_system = None
        self.show_orbit_dialog = False
        self.show_code_window = False
        self.code_window = None
        
        # Enemy tracking
        self.enemy_popups = {}
        self.targeted_enemies = {}
        self.next_enemy_id = 1
    
    def update_system_movement(self, current_time):
        """Update system movement animation state."""
        if self.system_ship_moving and self.system_move_start_time:
            elapsed = current_time - self.system_move_start_time
            progress = min(elapsed / self.system_move_duration_ms, 1.0)
            
            if progress >= 1.0:
                # Movement complete
                self.system_ship_moving = False
                self.system_move_start_time = None
                return True
            return False
        return False
    
    def start_system_movement(self, start_x, start_y, dest_q, dest_r):
        """Initialize system movement animation."""
        self.system_move_start_x = start_x
        self.system_move_start_y = start_y
        self.system_dest_q = dest_q
        self.system_dest_r = dest_r
        self.system_ship_moving = True
        self.system_move_start_time = time.time() * 1000
    
    def get_movement_progress(self):
        """Get current movement animation progress (0.0 to 1.0)."""
        if not self.system_ship_moving or not self.system_move_start_time:
            return 1.0
        
        current_time = time.time() * 1000
        elapsed = current_time - self.system_move_start_time
        return min(elapsed / self.system_move_duration_ms, 1.0)
    
    def update_orbital_state(self, delta_time):
        """Update player orbital motion around a planet."""
        if self.player_orbiting_planet and self.player_orbit_center:
            self.player_orbit_angle += self.player_orbit_speed * delta_time
            if self.player_orbit_angle > 2 * 3.14159:
                self.player_orbit_angle -= 2 * 3.14159
    
    def start_phaser_animation(self, target_enemy):
        """Start phaser firing animation."""
        self.selected_enemy = target_enemy
        self.phaser_animating = True
        self.phaser_anim_start = time.time() * 1000
    
    def update_phaser_animation(self, current_time):
        """Update phaser animation state. Returns True if animation complete."""
        if self.phaser_animating:
            elapsed = current_time - self.phaser_anim_start
            if elapsed >= self.phaser_anim_duration:
                self.phaser_animating = False
                return True
        return False