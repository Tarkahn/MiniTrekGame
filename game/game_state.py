"""
Game State Manager - Centralized state management for the Star Trek game
Replaces global variables with a structured state management system
"""

import pygame
from typing import Dict, Set, Tuple, Optional, Any, List
from dataclasses import dataclass


@dataclass
class AnimationState:
    """Manages animation-related state"""
    ship_anim_x: float = 0.0
    ship_anim_y: float = 0.0
    ship_moving: bool = False
    move_start_time: Optional[int] = None
    move_duration_ms: int = 2000
    move_ship_speed: Optional[float] = None
    move_frames: int = 120  # 2 seconds at 60 FPS
    dest_q: Optional[int] = None
    dest_r: Optional[int] = None


@dataclass
class CombatState:
    """Manages combat-related state"""
    selected_enemy: Optional[Any] = None
    phaser_animating: bool = False
    phaser_anim_start: int = 0
    phaser_range: int = 18
    targeted_enemies: Dict[str, Any] = None
    # Torpedo targeting - separate from enemy selection
    torpedo_target_hex: Optional[Tuple[int, int]] = None  # (q, r) hex coordinates for torpedo target
    torpedo_targeting_mode: bool = False  # True when player is selecting torpedo target
    # Torpedo animation
    torpedo_flying: bool = False
    torpedo_start_pos: Optional[Tuple[float, float]] = None
    torpedo_target_pos: Optional[Tuple[float, float]] = None
    torpedo_anim_start: int = 0
    torpedo_speed: float = 100.0  # pixels per second
    torpedo_target_enemy: Optional[Any] = None
    torpedo_target_distance: float = 0.0
    torpedo_combat_result: Optional[Dict] = None

    def __post_init__(self):
        if self.targeted_enemies is None:
            self.targeted_enemies = {}


@dataclass
class OrbitalState:
    """Manages orbital mechanics state"""
    player_orbiting_planet: bool = False
    player_orbit_center: Optional[Tuple[float, float]] = None
    orbital_angle: float = 0.0
    orbital_radius: float = 50.0
    orbital_speed: float = 0.02


@dataclass
class ScanState:
    """Manages scanning and exploration state"""
    sector_scan_active: bool = False
    scanned_systems: Set[Tuple[int, int]] = None
    enemy_popups: Dict[str, Dict[str, Any]] = None
    next_enemy_id: int = 1
    
    def __post_init__(self):
        if self.scanned_systems is None:
            self.scanned_systems = set()
        if self.enemy_popups is None:
            self.enemy_popups = {}


@dataclass
class UIState:
    """Manages UI-specific state"""
    button_pressed: List[bool] = None
    toggle_btn_pressed: List[bool] = None
    event_log: List[str] = None
    
    def __post_init__(self):
        if self.button_pressed is None:
            self.button_pressed = [False, False, False, False, False]  # Move, Fire, Torpedo, Scan, Repairs
        if self.toggle_btn_pressed is None:
            self.toggle_btn_pressed = [False]
        if self.event_log is None:
            self.event_log = []


class GameState:
    """
    Centralized game state manager that replaces global variables
    """
    
    def __init__(self):
        # Core game state
        self.map_mode: str = 'sector'  # 'sector' or 'system'
        self.current_system: Tuple[int, int] = (0, 0)
        self.ship_q: int = 0
        self.ship_r: int = 0
        
        # State components
        self.animation = AnimationState()
        self.combat = CombatState()
        self.orbital = OrbitalState()
        self.scan = ScanState()
        self.ui = UIState()
        
        # Weapon animation manager (initialized later when combat systems are ready)
        self.weapon_animation_manager = None
        
        # System and object management
        self.system_object_states: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.last_debug_system: Optional[Tuple[int, int]] = None
        
        # Initialize animation position
        self._update_animation_position()
    
    def initialize_weapon_system(self, combat_manager, player_ship):
        """Initialize the weapon animation manager with combat systems"""
        from game_logic.weapon_animation_manager import WeaponAnimationManager
        self.weapon_animation_manager = WeaponAnimationManager(combat_manager, player_ship)
        # Set the weapon animation manager reference in combat manager for enemy weapons
        combat_manager.set_weapon_animation_manager(self.weapon_animation_manager)
    
    def _update_animation_position(self):
        """Update animation position based on current ship position"""
        # This will be called when ship position changes
        # For now, we'll let the caller handle hex_grid access
        pass
    
    def set_ship_position(self, q: int, r: int, hex_grid=None):
        """Set ship position and update related state"""
        self.ship_q = q
        self.ship_r = r
        if hex_grid:
            self.animation.ship_anim_x, self.animation.ship_anim_y = hex_grid.get_hex_center(q, r)
    
    def set_current_system(self, system: Tuple[int, int]):
        """Set current system and update related state"""
        self.current_system = system
        self.scan.scanned_systems.add(system)
    
    def start_movement(self, dest_q: int, dest_r: int, start_time: int, speed: float):
        """Start ship movement animation"""
        self.animation.ship_moving = True
        self.animation.dest_q = dest_q
        self.animation.dest_r = dest_r
        self.animation.move_start_time = start_time
        self.animation.move_ship_speed = speed
    
    def stop_movement(self):
        """Stop ship movement animation"""
        self.animation.ship_moving = False
        self.animation.dest_q = None
        self.animation.dest_r = None
        self.animation.move_start_time = None
        self.animation.move_ship_speed = None
    
    def start_phaser_animation(self, start_time: int):
        """Start phaser firing animation"""
        self.combat.phaser_animating = True
        self.combat.phaser_anim_start = start_time
    
    def stop_phaser_animation(self):
        """Stop phaser firing animation"""
        self.combat.phaser_animating = False
        self.combat.phaser_anim_start = 0
    
    def start_torpedo_animation(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], start_time: int):
        """Start torpedo flight animation"""
        self.combat.torpedo_flying = True
        self.combat.torpedo_start_pos = start_pos
        self.combat.torpedo_target_pos = target_pos
        self.combat.torpedo_anim_start = start_time
    
    def stop_torpedo_animation(self):
        """Stop torpedo flight animation"""
        self.combat.torpedo_flying = False
        self.combat.torpedo_start_pos = None
        self.combat.torpedo_target_pos = None
        self.combat.torpedo_anim_start = 0
        self.combat.torpedo_target_enemy = None
        self.combat.torpedo_target_distance = 0.0
        self.combat.torpedo_combat_result = None
    
    def select_enemy(self, enemy):
        """Select an enemy for targeting (phasers)"""
        self.combat.selected_enemy = enemy

    def clear_enemy_selection(self):
        """Clear enemy selection"""
        self.combat.selected_enemy = None

    def set_torpedo_target_hex(self, q: int, r: int):
        """Set torpedo target hex coordinates"""
        self.combat.torpedo_target_hex = (q, r)
        self.combat.torpedo_targeting_mode = False  # Exit targeting mode after selection

    def clear_torpedo_target(self):
        """Clear torpedo target hex"""
        self.combat.torpedo_target_hex = None
        self.combat.torpedo_targeting_mode = False

    def enter_torpedo_targeting_mode(self):
        """Enter torpedo targeting mode - player will select a hex"""
        self.combat.torpedo_targeting_mode = True

    def exit_torpedo_targeting_mode(self):
        """Exit torpedo targeting mode without selecting"""
        self.combat.torpedo_targeting_mode = False

    def is_torpedo_targeting(self) -> bool:
        """Check if player is in torpedo targeting mode"""
        return self.combat.torpedo_targeting_mode

    def get_torpedo_target_hex(self) -> Optional[Tuple[int, int]]:
        """Get current torpedo target hex coordinates"""
        return self.combat.torpedo_target_hex
    
    def add_targeted_enemy(self, enemy_id: str, enemy_obj):
        """Add an enemy to the targeting system"""
        self.combat.targeted_enemies[enemy_id] = enemy_obj
    
    def remove_targeted_enemy(self, enemy_id: str):
        """Remove an enemy from the targeting system"""
        if enemy_id in self.combat.targeted_enemies:
            del self.combat.targeted_enemies[enemy_id]
    
    def get_next_enemy_id(self) -> str:
        """Get next unique enemy ID"""
        enemy_id = f"enemy_{self.scan.next_enemy_id}"
        self.scan.next_enemy_id += 1
        return enemy_id
    
    def add_enemy_popup(self, enemy_id: str, popup_info: Dict[str, Any]):
        """Add enemy popup information"""
        self.scan.enemy_popups[enemy_id] = popup_info
    
    def remove_enemy_popup(self, enemy_id: str):
        """Remove enemy popup information"""
        if enemy_id in self.scan.enemy_popups:
            del self.scan.enemy_popups[enemy_id]
    
    def set_orbital_state(self, orbiting: bool, center: Optional[Tuple[float, float]] = None):
        """Set orbital state"""
        self.orbital.player_orbiting_planet = orbiting
        self.orbital.player_orbit_center = center
        if not orbiting:
            self.orbital.orbital_angle = 0.0
    
    def update_orbital_angle(self, delta: float):
        """Update orbital angle for animation"""
        self.orbital.orbital_angle += delta
        if self.orbital.orbital_angle > 2 * 3.14159:  # 2*pi
            self.orbital.orbital_angle -= 2 * 3.14159
    
    def add_event_log(self, message: str, max_lines: int = 25):
        """Add message to event log"""
        self.ui.event_log.append(message)
        if len(self.ui.event_log) > max_lines:
            self.ui.event_log.pop(0)
    
    def clear_event_log(self):
        """Clear event log"""
        self.ui.event_log.clear()
    
    def set_button_pressed(self, button_index: int, pressed: bool):
        """Set button pressed state"""
        if 0 <= button_index < len(self.ui.button_pressed):
            self.ui.button_pressed[button_index] = pressed
    
    def set_toggle_pressed(self, toggle_index: int, pressed: bool):
        """Set toggle button pressed state"""
        if 0 <= toggle_index < len(self.ui.toggle_btn_pressed):
            self.ui.toggle_btn_pressed[toggle_index] = pressed
    
    def is_movement_active(self) -> bool:
        """Check if ship is currently moving"""
        return self.animation.ship_moving
    
    def is_phaser_animating(self) -> bool:
        """Check if phaser animation is active"""
        return self.combat.phaser_animating
    
    def is_orbiting(self) -> bool:
        """Check if player is orbiting a planet"""
        return self.orbital.player_orbiting_planet
    
    def get_animation_position(self) -> Tuple[float, float]:
        """Get current animation position"""
        return self.animation.ship_anim_x, self.animation.ship_anim_y
    
    def set_animation_position(self, x: float, y: float):
        """Set animation position"""
        self.animation.ship_anim_x = x
        self.animation.ship_anim_y = y
    
    def get_movement_destination(self) -> Optional[Tuple[int, int]]:
        """Get movement destination coordinates"""
        if self.animation.dest_q is not None and self.animation.dest_r is not None:
            return self.animation.dest_q, self.animation.dest_r
        return None
    
    def get_movement_progress(self, current_time: int) -> float:
        """Get movement progress as a value between 0.0 and 1.0"""
        if not self.animation.ship_moving or self.animation.move_start_time is None:
            return 1.0
        
        elapsed = current_time - self.animation.move_start_time
        progress = elapsed / self.animation.move_duration_ms
        return min(1.0, max(0.0, progress))
    
    def reset(self):
        """Reset all state to initial values"""
        self.__init__()