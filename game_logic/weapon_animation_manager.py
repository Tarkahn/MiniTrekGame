"""
Weapon Animation Manager - Handles all weapon firing animations and combat logic
Separates combat mechanics from UI rendering, maintaining clean architecture
"""

import pygame
import random
import math
from data import constants


def hex_distance(a, b):
    """Calculate hex grid distance between two positions (q, r)."""
    dq = abs(a[0] - b[0])
    dr = abs(a[1] - b[1])
    ds = abs((-a[0] - a[1]) - (-b[0] - b[1]))
    return max(dq, dr, ds)


class WeaponAnimationManager:
    """
    Manages weapon animations, hit calculations, and damage application.
    Provides clean interface between UI and combat systems.
    """
    
    def __init__(self, combat_manager, player_ship):
        self.combat_manager = combat_manager
        self.player_ship = player_ship
        self.system_objects = None  # Will be set by the game loop
        
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
        
        # Torpedo explosion state
        self.torpedo_explosion_center = None  # Pixel coordinates (x, y) of explosion
        self.torpedo_enemies_hit_by_ring = {}  # Track which enemies have been hit by which ring: {enemy_id: [ring_indices]}
        self.torpedo_explosion_pixel_center = None  # Pixel position of explosion center
        
        # Enemy weapon animation state
        self.enemy_phaser_animations = []  # List of active enemy phaser animations
        self.enemy_torpedo_animations = []  # List of active enemy torpedo animations
        
        # Animation constants
        self.torpedo_speed = 200  # pixels per second
        self.enemy_phaser_duration = 600  # ms - slightly longer than player phasers
        self.enemy_torpedo_speed = 150  # pixels per second - slightly slower than player
        
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
    
    def fire_torpedo(self, target_enemy, distance, start_pos, target_pos, target_hex_pos=None):
        """
        Fire torpedo at target - calculates damage and starts animation.
        
        Args:
            target_enemy: Enemy object to target
            distance: Distance to target in hexes
            start_pos: (x, y) pixel position where torpedo starts
            target_pos: (x, y) pixel position where torpedo goes
            target_hex_pos: (q, r) hex coordinates of target for explosion center
            
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
            
            # Store explosion center for proximity calculations
            self.torpedo_explosion_pixel_center = target_pos  # This is already in pixel coordinates
            self.torpedo_enemies_hit_by_ring = {}  # Reset hit tracking
            
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
    
    def update(self, current_time, hex_grid=None):
        """
        Update weapon animations and handle damage application when animations complete.
        
        Args:
            current_time: Current pygame time in milliseconds
            hex_grid: Hex grid object for position conversions (needed for ring collision)
            
        Returns:
            dict: Animation events that occurred (for UI feedback)
        """
        events = {
            'phaser_completed': None,
            'torpedo_explosion': None,
            'torpedo_ring_hits': None,
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
            torpedo_events = self._update_torpedo_animation(current_time)
            events.update(torpedo_events)
            
            # During explosion phase, continuously check for ring collisions
            if (hex_grid and self.torpedo_damage_shown and 
                self.torpedo_explosion_pixel_center and not events['torpedo_completed']):
                
                newly_hit = self._check_ring_collision(current_time, hex_grid)
                
                if newly_hit:
                    # Process ring hits and apply damage
                    ring_hit_results = []
                    for hit_data in newly_hit:
                        enemy = hit_data['enemy']
                        damage = hit_data['damage']
                        ring_index = hit_data['ring_index']
                        
                        # Create combat result for damage application
                        enemy_shields = getattr(enemy, 'shields', constants.ENEMY_SHIELD_CAPACITY)
                        shield_damage = min(damage, enemy_shields)
                        hull_damage = max(0, damage - enemy_shields)
                        
                        fake_combat_result = {
                            'success': True,
                            'damage_calculated': damage,
                            'shield_damage': shield_damage,
                            'hull_damage': hull_damage,
                            'ring_index': ring_index
                        }
                        
                        # Apply the damage
                        updated_result = self.combat_manager.apply_damage_to_enemy(enemy, fake_combat_result)
                        
                        ring_hit_results.append({
                            'enemy': enemy,
                            'ring_index': ring_index,
                            'damage': damage,
                            'distance_pixels': hit_data['distance_pixels'],
                            'enemy_pos': hit_data['enemy_pos'],
                            'combat_result': updated_result
                        })
                    
                    # Create ring hit event (separate from main explosion event)
                    events['torpedo_ring_hits'] = {
                        'explosion_center': self.torpedo_explosion_pixel_center,
                        'newly_hit_enemies': ring_hit_results
                    }
        
        return events
    
    def _check_ring_collision(self, current_time, hex_grid):
        """
        Check for real-time collision between explosion rings and moving enemies.
        Returns list of newly hit enemies with ring collision data.
        """
        if not self.torpedo_explosion_pixel_center or not self.system_objects:
            return []
        
        newly_hit = []
        explosion_center = self.torpedo_explosion_pixel_center
        
        # Get current animation data to know which rings are active
        anim_data = self.get_torpedo_animation_data(current_time)
        if not anim_data or anim_data['state'] != 'exploding':
            return newly_hit
        
        waves = anim_data.get('waves', [])
        
        # Find all enemies in the system
        enemies = [obj for obj in self.system_objects if obj.type == 'enemy']
        
        for enemy in enemies:
            enemy_id = id(enemy)  # Use object ID as unique identifier
            
            # Get enemy's current animated position (real-time)
            enemy_pos = self._get_enemy_real_time_position(enemy, hex_grid)
            if not enemy_pos:
                continue
            
            # Initialize hit tracking for this enemy if needed
            if enemy_id not in self.torpedo_enemies_hit_by_ring:
                self.torpedo_enemies_hit_by_ring[enemy_id] = []
            
            # Check collision with each active ring
            for wave in waves:
                ring_index = wave['wave_index']
                ring_radius = wave['radius']
                
                # Skip if this enemy was already hit by this ring
                if ring_index in self.torpedo_enemies_hit_by_ring[enemy_id]:
                    continue
                
                # Calculate distance from explosion center to enemy
                dx = enemy_pos[0] - explosion_center[0]
                dy = enemy_pos[1] - explosion_center[1]
                distance_pixels = math.hypot(dx, dy)
                
                # Check if enemy is within this ring's collision radius
                ring_thickness = max(5, ring_radius / 5)  # Rings have some thickness
                if abs(distance_pixels - ring_radius) <= ring_thickness:
                    # Hit! Calculate damage based on which ring hit the enemy
                    damage = self._calculate_ring_damage(ring_index, distance_pixels)
                    
                    newly_hit.append({
                        'enemy': enemy,
                        'ring_index': ring_index,
                        'damage': damage,
                        'distance_pixels': distance_pixels,
                        'enemy_pos': enemy_pos
                    })
                    
                    # Mark this enemy as hit by this ring
                    self.torpedo_enemies_hit_by_ring[enemy_id].append(ring_index)
        
        return newly_hit
    
    def _get_enemy_real_time_position(self, enemy, hex_grid):
        """Get enemy's current pixel position, accounting for movement animation."""
        # Use the same logic as get_enemy_current_position in wireframe
        if hasattr(enemy, 'anim_px') and hasattr(enemy, 'anim_py'):
            return (enemy.anim_px, enemy.anim_py)
        elif hasattr(enemy, 'system_q') and hasattr(enemy, 'system_r'):
            try:
                return hex_grid.get_hex_center(enemy.system_q, enemy.system_r)
            except:
                return None
        return None
    
    def _calculate_ring_damage(self, ring_index, distance_pixels):
        """Calculate damage based on which explosion ring hit the enemy."""
        base_damage = self.torpedo_combat_result.get('damage_calculated', constants.PLAYER_TORPEDO_POWER)
        
        # Different rings deal different damage
        if ring_index == 0:
            # Core explosion - maximum damage
            multiplier = constants.TORPEDO_DIRECT_HIT_MULTIPLIER
        elif ring_index == 1:
            # Primary blast wave - high damage
            multiplier = 1.4
        elif ring_index == 2:
            # Secondary blast - medium damage
            multiplier = 1.0
        elif ring_index == 3:
            # Tertiary blast - lower damage
            multiplier = 0.7
        elif ring_index == 4:
            # Pressure wave - minimal damage
            multiplier = 0.4
        else:
            # Outer rings - very low damage
            multiplier = 0.2
        
        return int(base_damage * multiplier)
    
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
        """Update torpedo animation and handle proximity explosion logic."""
        events = {
            'torpedo_explosion': None,
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
                # Torpedo explosion phase - no longer calculate damage once, but continuously
                # The explosion event will be handled by the update method checking for ring collisions
                self.torpedo_damage_shown = True  # Mark that explosion phase has started
                
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
        self.torpedo_explosion_center = None
        self.torpedo_enemies_hit_by_ring = {}
        self.torpedo_explosion_pixel_center = None
    
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
            explosion_progress = min(explosion_elapsed / 1000, 1.0)
            
            # Create multiple expanding waves for interesting visual effect
            waves = []
            for wave_index in range(constants.TORPEDO_EXPLOSION_ANIMATION_WAVES):
                wave_start_time = wave_index * constants.TORPEDO_EXPLOSION_WAVE_DELAY
                if explosion_elapsed >= wave_start_time:
                    wave_elapsed = explosion_elapsed - wave_start_time
                    wave_radius = min(10 + (wave_elapsed / 15), 40 - (wave_index * 5))
                    wave_opacity = max(0, 255 - (wave_elapsed / 3))
                    if wave_radius > 0 and wave_opacity > 0:
                        waves.append({
                            'radius': wave_radius,
                            'opacity': int(wave_opacity),
                            'wave_index': wave_index
                        })
            
            return {
                'position': self.torpedo_target_pos,
                'state': 'exploding',
                'explosion_progress': explosion_progress,
                'explosion_center': self.torpedo_explosion_pixel_center,
                'waves': waves
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
    
    def enemy_fire_phaser(self, enemy_ship, start_pos, target_pos, damage):
        """
        Start an enemy phaser animation targeting the player.
        
        Args:
            enemy_ship: Enemy ship object firing
            start_pos: Starting position in pixels (enemy position)
            target_pos: Target position in pixels (player position)
            damage: Damage amount to apply when animation completes
        """
        import time
        
        # Create enemy phaser animation
        animation = {
            'type': 'phaser',
            'start_time': time.time() * 1000,  # Convert to milliseconds
            'duration': self.enemy_phaser_duration,
            'enemy_ship': enemy_ship,
            'start_pos': start_pos,
            'target_pos': target_pos,
            'damage': damage,
            'applied': False
        }
        
        self.enemy_phaser_animations.append(animation)
        
        # Play enemy phaser sound
        from ui.sound_manager import get_sound_manager
        sound_manager = get_sound_manager()
        sound_manager.play_sound('phaser_shot')  # Reuse same sound for now
    
    def enemy_fire_torpedo(self, enemy_ship, start_pos, target_pos, damage):
        """
        Start an enemy torpedo animation targeting the player.
        
        Args:
            enemy_ship: Enemy ship object firing
            start_pos: Starting position in pixels (enemy position)
            target_pos: Target position in pixels (player position)
            damage: Damage amount to apply when torpedo hits
        """
        import time
        
        # Calculate torpedo flight time
        distance_pixels = math.hypot(target_pos[0] - start_pos[0], target_pos[1] - start_pos[1])
        flight_time = (distance_pixels / self.enemy_torpedo_speed) * 1000  # Convert to milliseconds
        
        # Create enemy torpedo animation
        animation = {
            'type': 'torpedo',
            'start_time': time.time() * 1000,  # Convert to milliseconds
            'duration': flight_time,
            'enemy_ship': enemy_ship,
            'start_pos': start_pos,
            'target_pos': target_pos,
            'current_pos': start_pos,
            'damage': damage,
            'applied': False
        }
        
        self.enemy_torpedo_animations.append(animation)
    
    def update_enemy_animations(self, current_time_ms):
        """
        Update all enemy weapon animations and apply damage when appropriate.
        
        Args:
            current_time_ms: Current time in milliseconds
        """
        # Update enemy phaser animations
        for animation in self.enemy_phaser_animations[:]:  # Copy list to avoid modification during iteration
            elapsed = current_time_ms - animation['start_time']
            progress = elapsed / animation['duration']
            
            if progress >= 1.0:
                # Phaser animation complete - apply damage
                if not animation['applied']:
                    self.player_ship.apply_damage(animation['damage'], animation['enemy_ship'])
                    animation['applied'] = True
                    print(f"Player hit by enemy phaser for {animation['damage']} damage!")
                
                # Remove completed animation
                self.enemy_phaser_animations.remove(animation)
        
        # Update enemy torpedo animations
        for animation in self.enemy_torpedo_animations[:]:  # Copy list to avoid modification during iteration
            elapsed = current_time_ms - animation['start_time']
            progress = elapsed / animation['duration']
            
            if progress >= 1.0:
                # Torpedo hits target - apply damage
                if not animation['applied']:
                    self.player_ship.apply_damage(animation['damage'], animation['enemy_ship'])
                    animation['applied'] = True
                    print(f"Player hit by enemy torpedo for {animation['damage']} damage!")
                
                # Remove completed animation
                self.enemy_torpedo_animations.remove(animation)
            else:
                # Update torpedo position during flight
                start_x, start_y = animation['start_pos']
                target_x, target_y = animation['target_pos']
                
                current_x = start_x + (target_x - start_x) * progress
                current_y = start_y + (target_y - start_y) * progress
                animation['current_pos'] = (current_x, current_y)
    
    def draw_enemy_weapon_animations(self, screen, current_time_ms):
        """
        Draw all enemy weapon animations.
        
        Args:
            screen: Pygame screen surface
            current_time_ms: Current time in milliseconds
        """
        # Draw enemy phaser animations
        for animation in self.enemy_phaser_animations:
            elapsed = current_time_ms - animation['start_time']
            progress = elapsed / animation['duration']
            
            if 0 <= progress <= 1.0:
                # Get enemy ship position from animation data
                start_pos = animation.get('start_pos', (400, 400))  # Fallback position
                
                # Draw red phaser beam (different from player's blue/yellow)
                target_pos = animation['target_pos']
                
                # Calculate beam properties
                alpha = int(255 * (1.0 - progress))  # Fade out over time
                thickness = max(1, int(4 * (1.0 - progress)))  # Thicken and fade
                
                # Draw red enemy phaser beam
                color = (255, 100, 100, alpha)  # Red color for enemy
                if alpha > 0:
                    pygame.draw.line(screen, color[:3], start_pos, target_pos, thickness)
        
        # Draw enemy torpedo animations
        for animation in self.enemy_torpedo_animations:
            elapsed = current_time_ms - animation['start_time']
            progress = elapsed / animation['duration']
            
            if 0 <= progress <= 1.0:
                current_pos = animation['current_pos']
                
                # Draw red enemy torpedo (different from player's blue/green)
                pygame.draw.circle(screen, (255, 100, 100), (int(current_pos[0]), int(current_pos[1])), 3)
                # Add red glow effect
                pygame.draw.circle(screen, (255, 150, 150, 100), (int(current_pos[0]), int(current_pos[1])), 6, 2)

    def stop_all_animations(self):
        """Force stop all weapon animations (emergency cleanup)."""
        self.phaser_animating = False
        self.torpedo_flying = False
        self._complete_torpedo_attack()
        self.phaser_target_enemy = None
        self.phaser_combat_result = None