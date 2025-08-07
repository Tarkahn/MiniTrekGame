"""
Weapon Animation Manager - Handles all weapon firing animations and combat logic
Separates combat mechanics from UI rendering, maintaining clean architecture
"""

import pygame
import random
import math
from data import constants


class WeaponAnimationManager:
    """
    Manages weapon animations, hit calculations, and damage application.
    Provides clean interface between UI and combat systems.
    """
    
    def __init__(self, combat_manager, player_ship):
        self.combat_manager = combat_manager
        self.player_ship = player_ship
        
        # Phaser animation state
        self.phaser_animating = False
        self.phaser_anim_start = 0
        self.phaser_anim_duration = 500  # ms
        self.phaser_target_enemy = None
        self.phaser_combat_result = None
        
        # Torpedo animation state
        self.torpedo_flying = False
        self.torpedo_anim_start = 0
        self.torpedo_start_pos = None
        self.torpedo_target_pos = None
        self.torpedo_target_enemy = None
        self.torpedo_target_distance = 0
        self.torpedo_combat_result = None
        self.torpedo_damage_shown = False
        
        # Animation constants
        self.torpedo_speed = 200  # pixels per second
        
    def fire_phaser(self, target_enemy, distance):
        """
        Fire phasers at target - calculates damage and starts animation.
        
        Args:
            target_enemy: Enemy object to target
            distance: Distance to target in hexes
            
        Returns:
            dict: Result containing success status and animation info
        """
        if self.phaser_animating:
            return {'success': False, 'reason': 'Phaser already firing'}
        
        # Calculate damage but don't apply it yet
        combat_result = self.combat_manager.calculate_phaser_damage(
            self.player_ship, target_enemy, distance
        )
        
        if combat_result['success']:
            # Store combat data for when animation completes
            self.phaser_target_enemy = target_enemy
            self.phaser_combat_result = combat_result
            
            # Start animation
            self.phaser_animating = True
            self.phaser_anim_start = pygame.time.get_ticks()
            
            return {
                'success': True,
                'animation_started': True,
                'damage_calculated': combat_result['damage_calculated']
            }
        else:
            return {'success': False, 'reason': 'Phaser fire failed'}
    
    def fire_torpedo(self, target_enemy, distance, start_pos, target_pos):
        """
        Fire torpedo at target - calculates damage and starts animation.
        
        Args:
            target_enemy: Enemy object to target
            distance: Distance to target in hexes
            start_pos: (x, y) pixel position where torpedo starts
            target_pos: (x, y) pixel position where torpedo goes
            
        Returns:
            dict: Result containing success status and animation info
        """
        if self.torpedo_flying:
            return {'success': False, 'reason': 'Torpedo already flying'}
        
        # Calculate damage but don't apply it yet
        combat_result = self.combat_manager.calculate_torpedo_damage(
            self.player_ship, target_enemy, distance
        )
        
        if combat_result['success']:
            # Store combat data for when torpedo hits
            self.torpedo_target_enemy = target_enemy
            self.torpedo_target_distance = distance
            self.torpedo_combat_result = combat_result
            self.torpedo_start_pos = start_pos
            self.torpedo_target_pos = target_pos
            self.torpedo_damage_shown = False
            
            # Start animation
            self.torpedo_flying = True
            self.torpedo_anim_start = pygame.time.get_ticks()
            
            return {
                'success': True,
                'animation_started': True,
                'damage_calculated': combat_result['damage_calculated']
            }
        else:
            return {'success': False, 'reason': 'Torpedo fire failed'}
    
    def update(self, current_time):
        """
        Update weapon animations and handle damage application when animations complete.
        
        Args:
            current_time: Current pygame time in milliseconds
            
        Returns:
            dict: Animation events that occurred (for UI feedback)
        """
        events = {
            'phaser_completed': None,
            'torpedo_hit': None,
            'torpedo_miss': None,
            'torpedo_completed': False
        }
        
        # Update phaser animation
        if self.phaser_animating:
            elapsed = current_time - self.phaser_anim_start
            if elapsed >= self.phaser_anim_duration:
                # Phaser animation complete - apply damage
                events['phaser_completed'] = self._complete_phaser_attack()
                self.phaser_animating = False
        
        # Update torpedo animation
        if self.torpedo_flying:
            events.update(self._update_torpedo_animation(current_time))
        
        return events
    
    def _complete_phaser_attack(self):
        """Apply phaser damage and return result for UI feedback."""
        if not self.phaser_target_enemy or not self.phaser_combat_result:
            return None
        
        # Apply the calculated damage
        updated_result = self.combat_manager.apply_damage_to_enemy(
            self.phaser_target_enemy, self.phaser_combat_result
        )
        
        # Prepare result for UI
        result = {
            'target_enemy': self.phaser_target_enemy,
            'combat_result': updated_result,
            'damage_info': self.phaser_combat_result
        }
        
        # Clean up
        self.phaser_target_enemy = None
        self.phaser_combat_result = None
        
        return result
    
    def _update_torpedo_animation(self, current_time):
        """Update torpedo animation and handle hit/miss logic."""
        events = {
            'torpedo_hit': None,
            'torpedo_miss': None,
            'torpedo_completed': False
        }
        
        elapsed = current_time - self.torpedo_anim_start
        
        # Calculate travel distance and time
        if self.torpedo_start_pos and self.torpedo_target_pos:
            dx = self.torpedo_target_pos[0] - self.torpedo_start_pos[0]
            dy = self.torpedo_target_pos[1] - self.torpedo_start_pos[1]
            total_distance = math.hypot(dx, dy)
            travel_time = (total_distance / self.torpedo_speed) * 1000  # Convert to ms
            
            if elapsed >= travel_time:
                # Torpedo reached target - determine hit/miss
                if not self.torpedo_damage_shown:
                    hit_chance = max(0, constants.PLAYER_TORPEDO_ACCURACY - (self.torpedo_target_distance * 0.05))
                    torpedo_hits = random.random() < hit_chance
                    
                    if self.torpedo_combat_result['success'] and torpedo_hits:
                        # Torpedo hits - apply damage
                        updated_result = self.combat_manager.apply_damage_to_enemy(
                            self.torpedo_target_enemy, self.torpedo_combat_result
                        )
                        
                        events['torpedo_hit'] = {
                            'target_enemy': self.torpedo_target_enemy,
                            'combat_result': updated_result,
                            'damage_info': self.torpedo_combat_result,
                            'hit_chance': hit_chance
                        }
                    else:
                        # Torpedo misses
                        events['torpedo_miss'] = {
                            'target_enemy': self.torpedo_target_enemy,
                            'hit_chance': hit_chance
                        }
                    
                    self.torpedo_damage_shown = True
                
                # Check if explosion animation is complete (additional time for visual effect)
                explosion_duration = 1000  # ms
                if elapsed >= travel_time + explosion_duration:
                    events['torpedo_completed'] = True
                    self._complete_torpedo_attack()
        
        return events
    
    def _complete_torpedo_attack(self):
        """Clean up torpedo animation state."""
        self.torpedo_flying = False
        self.torpedo_target_enemy = None
        self.torpedo_combat_result = None
        self.torpedo_start_pos = None
        self.torpedo_target_pos = None
        self.torpedo_damage_shown = False
    
    def get_torpedo_animation_data(self, current_time):
        """
        Get current torpedo position and animation state for UI rendering.
        
        Returns:
            dict: Animation data for UI layer to render
        """
        if not self.torpedo_flying or not self.torpedo_start_pos or not self.torpedo_target_pos:
            return None
        
        elapsed = current_time - self.torpedo_anim_start
        
        # Calculate travel progress
        dx = self.torpedo_target_pos[0] - self.torpedo_start_pos[0]
        dy = self.torpedo_target_pos[1] - self.torpedo_start_pos[1]
        total_distance = math.hypot(dx, dy)
        travel_time = (total_distance / self.torpedo_speed) * 1000
        
        if elapsed < travel_time:
            # Torpedo still traveling
            progress = elapsed / travel_time
            torpedo_x = self.torpedo_start_pos[0] + dx * progress
            torpedo_y = self.torpedo_start_pos[1] + dy * progress
            
            return {
                'position': (torpedo_x, torpedo_y),
                'state': 'traveling',
                'progress': progress
            }
        else:
            # Torpedo at target (explosion phase)
            explosion_elapsed = elapsed - travel_time
            explosion_radius = 15 + explosion_elapsed // 50
            
            return {
                'position': self.torpedo_target_pos,
                'state': 'exploding',
                'explosion_radius': min(explosion_radius, 25),
                'explosion_progress': min(explosion_elapsed / 1000, 1.0)
            }
    
    def get_phaser_animation_data(self, current_time):
        """
        Get phaser animation state for UI rendering.
        
        Returns:
            dict: Animation data for UI layer to render
        """
        if not self.phaser_animating:
            return None
        
        elapsed = current_time - self.phaser_anim_start
        progress = min(elapsed / self.phaser_anim_duration, 1.0)
        
        return {
            'target_enemy': self.phaser_target_enemy,
            'progress': progress,
            'active': True
        }
    
    def is_weapon_animating(self):
        """Check if any weapon animation is currently active."""
        return self.phaser_animating or self.torpedo_flying
    
    def stop_all_animations(self):
        """Force stop all weapon animations (emergency cleanup)."""
        self.phaser_animating = False
        self.torpedo_flying = False
        self._complete_torpedo_attack()
        self.phaser_target_enemy = None
        self.phaser_combat_result = None