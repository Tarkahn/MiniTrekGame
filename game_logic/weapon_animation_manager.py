"""
Weapon Animation Manager - Handles all weapon firing animations and combat logic
Separates combat mechanics from UI rendering, maintaining clean architecture
"""

import pygame
import random
import math
from data import constants
from utils.geometry import hex_distance


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
        self.torpedo_player_hit_by_ring = []  # Track which rings have hit the player ship
        self.torpedo_player_start_pos = None  # Player's position when torpedo was fired (for self-damage calc)
        
        # Enemy weapon animation state
        self.enemy_phaser_animations = []  # List of active enemy phaser animations
        self.enemy_torpedo_animations = []  # List of active enemy torpedo animations
        
        # Animation constants
        self.torpedo_speed = 200  # pixels per second
        self.enemy_phaser_duration = 600  # ms - normal animation duration
        self.enemy_torpedo_speed = 150  # pixels per second - slightly slower than player

        # Event log callback (set by wireframe)
        self.add_event_log = None

    def _check_player_evasion(self, weapon_type='phaser'):
        """
        Check if player evades enemy weapon based on engine power allocation.
        High engine power (7+) gives evasion chance: 7=20%, 8=35%, 9=50%
        Torpedoes are harder to evade (guided weapons) - half the chance.

        Args:
            weapon_type: 'phaser' or 'torpedo'

        Returns:
            True if player evades (damage should NOT be applied)
        """
        engine_power = self.player_ship.power_allocation.get('engines', 5)
        if engine_power < constants.ENGINE_EVASION_MIN_POWER:
            print(f"[EVASION] Engine power {engine_power} < {constants.ENGINE_EVASION_MIN_POWER}, no evasion possible")
            return False

        # Calculate evasion chance (7=20%, 8=35%, 9=50%)
        base_evasion = constants.ENGINE_EVASION_BASE_CHANCE + \
                       (engine_power - constants.ENGINE_EVASION_MIN_POWER + 1) * constants.ENGINE_EVASION_PER_LEVEL

        # Apply engine integrity modifier - damaged engines reduce evasion
        engine_integrity = self.player_ship.system_integrity.get('engines', 100)
        effective_evasion = base_evasion * (engine_integrity / 100)

        # Torpedoes are guided weapons - harder to evade
        if weapon_type == 'torpedo':
            effective_evasion *= constants.ENGINE_EVASION_TORPEDO_MODIFIER

        roll = random.random()
        evaded = roll < effective_evasion
        print(f"[EVASION] Engine power {engine_power}, evasion chance {effective_evasion*100:.0f}%, roll {roll:.2f} -> {'EVADED!' if evaded else 'HIT'}")
        return evaded

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
            self.torpedo_player_hit_by_ring = []  # Reset player hit tracking
            self.torpedo_player_start_pos = start_pos  # Store player position for self-damage
            
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
            'torpedo_player_hit': None,  # Player ship caught in explosion
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

                collision_result = self._check_ring_collision(current_time, hex_grid)
                newly_hit = collision_result.get('enemies', [])
                player_hit = collision_result.get('player_hit', None)

                if newly_hit:
                    # Process ring hits and apply damage
                    ring_hit_results = []
                    for hit_data in newly_hit:
                        enemy = hit_data['enemy']
                        damage = hit_data['damage']
                        ring_index = hit_data['ring_index']

                        # Get or create proper EnemyShip instance for this enemy MapObject
                        # Must do this FIRST to get correct shield values
                        enemy_ship = self.combat_manager.get_or_create_enemy_ship(enemy, self.player_ship)

                        # Get shields from the EnemyShip, not the MapObject
                        if hasattr(enemy_ship, 'shield_system'):
                            shield_power = enemy_ship.shield_system.current_power_level
                            shield_integrity = enemy_ship.shield_system.current_integrity
                            enemy_shields = int((shield_power * enemy_ship.shield_system.absorption_per_level) * (shield_integrity / 100.0))
                        elif hasattr(enemy_ship, 'shields'):
                            enemy_shields = enemy_ship.shields
                        else:
                            enemy_shields = constants.ENEMY_SHIELD_CAPACITY

                        shield_damage = min(damage, enemy_shields)
                        hull_damage = max(0, damage - enemy_shields)

                        fake_combat_result = {
                            'success': True,
                            'damage': damage,  # This is what apply_damage_to_enemy looks for
                            'damage_calculated': damage,
                            'shield_damage': shield_damage,
                            'hull_damage': hull_damage,
                            'ring_index': ring_index
                        }

                        # Apply the damage
                        updated_result = self.combat_manager.apply_damage_to_enemy(enemy_ship, fake_combat_result)

                        # Trigger torpedo hit flash for cloaked Romulans
                        if hasattr(enemy_ship, 'trigger_torpedo_hit_flash') and hasattr(enemy_ship, 'is_cloak_capable'):
                            if enemy_ship.is_cloak_capable:
                                enemy_ship.trigger_torpedo_hit_flash()

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

                # Handle player ship damage from own torpedo
                if player_hit:
                    damage = player_hit['damage']

                    # Apply damage to player ship
                    self.player_ship.apply_damage(damage)

                    events['torpedo_player_hit'] = {
                        'damage': damage,
                        'distance_pixels': player_hit['distance_pixels'],
                        'ring_index': player_hit['ring_index'],
                        'player_pos': player_hit['player_pos']
                    }
        
        return events
    
    def _check_ring_collision(self, current_time, hex_grid):
        """
        Check for real-time collision between explosion rings and ships.
        Returns dict with 'enemies' list and 'player_hit' data if player was caught in blast.
        """
        result = {'enemies': [], 'player_hit': None}

        if not self.torpedo_explosion_pixel_center:
            return result

        explosion_center = self.torpedo_explosion_pixel_center

        # Get current animation data to know which rings are active
        anim_data = self.get_torpedo_animation_data(current_time)
        if not anim_data or anim_data['state'] != 'exploding':
            return result

        waves = anim_data.get('waves', [])

        # Find all enemies in the system (only if system_objects is set)
        enemies = [obj for obj in self.system_objects if obj.type == 'enemy'] if self.system_objects else []

        for enemy in enemies:
            enemy_id = id(enemy)  # Use object ID as unique identifier

            # Get enemy's current animated position (real-time)
            enemy_pos = self._get_enemy_real_time_position(enemy, hex_grid)
            if not enemy_pos:
                continue

            # Initialize hit tracking for this enemy if needed
            if enemy_id not in self.torpedo_enemies_hit_by_ring:
                self.torpedo_enemies_hit_by_ring[enemy_id] = []

            # Calculate distance from explosion center to enemy
            dx = enemy_pos[0] - explosion_center[0]
            dy = enemy_pos[1] - explosion_center[1]
            distance_pixels = math.hypot(dx, dy)

            # Get maximum explosion radius for damage range check
            max_radius_pixels = getattr(constants, 'TORPEDO_EXPLOSION_MAX_VISUAL_RADIUS', 160)

            # Only check enemies within blast radius
            if distance_pixels <= max_radius_pixels:
                # Check if enemy hasn't been hit yet - enemy inside blast radius takes damage once
                # Damage is applied immediately when explosion starts - no need to wait for visual wave
                if len(self.torpedo_enemies_hit_by_ring[enemy_id]) == 0:
                    # Hit! Calculate damage based on distance from explosion center
                    damage = self._calculate_ring_damage(0, distance_pixels)

                    result['enemies'].append({
                        'enemy': enemy,
                        'ring_index': 0,
                        'damage': damage,
                        'distance_pixels': distance_pixels,
                        'enemy_pos': enemy_pos
                    })

                    # Mark this enemy as hit
                    self.torpedo_enemies_hit_by_ring[enemy_id].append(0)

        # Check if player ship is caught in the explosion
        # Use the stored player position from when the torpedo was fired
        player_pos = self.torpedo_player_start_pos
        if player_pos:
            # Calculate distance to explosion
            dx = player_pos[0] - explosion_center[0]
            dy = player_pos[1] - explosion_center[1]
            distance_to_explosion = math.hypot(dx, dy)

            # Get maximum explosion radius for damage range check
            max_radius_pixels = getattr(constants, 'TORPEDO_EXPLOSION_MAX_VISUAL_RADIUS', 160)

            # Only check for player damage if within blast radius
            if distance_to_explosion <= max_radius_pixels:
                # Check if player hasn't been hit yet - player inside blast radius takes damage once
                # Damage is applied immediately when explosion starts
                if len(self.torpedo_player_hit_by_ring) == 0:
                    # Player caught in own torpedo blast!
                    damage = self._calculate_ring_damage(0, distance_to_explosion)

                    result['player_hit'] = {
                        'ring_index': 0,
                        'damage': damage,
                        'distance_pixels': distance_to_explosion,
                        'player_pos': player_pos
                    }

                    # Mark player as hit
                    self.torpedo_player_hit_by_ring.append(0)

        return result

    def _get_player_real_time_position(self, player_obj, hex_grid):
        """Get player's current pixel position, accounting for movement animation."""
        # Check for animated position first
        if hasattr(player_obj, 'anim_px') and hasattr(player_obj, 'anim_py'):
            return (player_obj.anim_px, player_obj.anim_py)
        elif hasattr(player_obj, 'system_q') and hasattr(player_obj, 'system_r'):
            try:
                return hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
            except:
                return None
        return None
    
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
        """Calculate damage based on distance from explosion center with flat-then-drop falloff.

        Uses a flattened curve that maintains high damage in the inner blast zone,
        then drops off more steeply near the edge. This makes torpedoes deadly at close range.

        With 160px radius and 80 base damage:
        - Distance 0 (direct hit): 80 * 1.25 = 100 damage
        - Distance 25px (~1 hex): 80 * 0.97 = ~78 damage (almost full!)
        - Distance 50px (~2 hex): 80 * 0.90 = ~72 damage
        - Distance 80px (~3 hex): 80 * 0.75 = ~60 damage
        - Distance 120px (~5 hex): 80 * 0.44 = ~35 damage
        - Distance 160px (edge): 0 damage
        """
        base_damage = self.torpedo_combat_result.get('damage_calculated', constants.PLAYER_TORPEDO_POWER)
        max_radius_pixels = getattr(constants, 'TORPEDO_EXPLOSION_MAX_VISUAL_RADIUS', 160)

        # Calculate falloff based on actual pixel distance from center
        if distance_pixels <= 0:
            # Direct hit - bonus damage but not instant-kill
            multiplier = constants.TORPEDO_DIRECT_HIT_MULTIPLIER
        elif distance_pixels >= max_radius_pixels:
            # Beyond blast radius - no damage
            multiplier = 0.0
        else:
            # Quadratic falloff (x^2 curve): stays HIGH at close range, drops steeply at edge
            # Formula: 1.0 - (distance_ratio)^2 keeps damage high until you're far away
            distance_ratio = distance_pixels / max_radius_pixels
            multiplier = 1.0 - (distance_ratio * distance_ratio)

        return int(base_damage * multiplier)
    
    def _complete_phaser_attack(self):
        """Apply phaser damage and return result for UI feedback."""
        if not self.phaser_target_enemy or not self.phaser_combat_result:
            return None
        
        # Get or create proper EnemyShip instance for this enemy MapObject
        enemy_ship = self.combat_manager.get_or_create_enemy_ship(
            self.phaser_target_enemy, self.player_ship
        )
        
        # Apply the calculated damage
        updated_result = self.combat_manager.apply_damage_to_enemy(
            enemy_ship, self.phaser_combat_result
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
        """Update torpedo animation and handle direct hit damage for static enemies."""
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

            # Handle zero distance case (firing at own position or very close)
            if total_distance < 1:
                travel_time = 0  # Immediate explosion
            else:
                travel_time = (total_distance / self.torpedo_speed) * 1000  # Convert to ms

            if elapsed >= travel_time and not self.torpedo_damage_shown:
                # Torpedo hits target - apply direct damage for static enemies
                self.torpedo_damage_shown = True  # Mark that explosion phase has started
                
                # Apply direct hit damage to the target enemy
                events['torpedo_explosion'] = self._apply_torpedo_direct_hit()

                # Check if explosion animation is complete (additional time for visual effect)
                # Longer duration for larger explosion radius
                explosion_duration = 1500  # ms (increased for larger explosion)
                if elapsed >= travel_time + explosion_duration:
                    events['torpedo_completed'] = True
                    self._complete_torpedo_attack()
            elif elapsed >= travel_time:
                # In explosion phase, check if animation should complete
                explosion_duration = 1500  # ms (increased for larger explosion)
                if elapsed >= travel_time + explosion_duration:
                    events['torpedo_completed'] = True
                    self._complete_torpedo_attack()
        
        return events
    
    def _apply_torpedo_direct_hit(self):
        """Apply direct hit torpedo damage to static enemy target."""
        if not self.torpedo_target_enemy or not self.torpedo_combat_result:
            return None
        
        # Get or create proper EnemyShip instance for this enemy MapObject
        enemy_ship = self.combat_manager.get_or_create_enemy_ship(
            self.torpedo_target_enemy, self.player_ship
        )
        
        # Apply maximum torpedo damage (direct hit)
        updated_result = self.combat_manager.apply_damage_to_enemy(
            enemy_ship, self.torpedo_combat_result
        )

        # Trigger torpedo hit flash for cloaked Romulans
        if hasattr(enemy_ship, 'trigger_torpedo_hit_flash') and hasattr(enemy_ship, 'is_cloak_capable'):
            if enemy_ship.is_cloak_capable:
                enemy_ship.trigger_torpedo_hit_flash()

        # Return explosion event for UI
        result = {
            'target_enemy': self.torpedo_target_enemy,
            'combat_result': updated_result,
            'explosion_center': self.torpedo_explosion_pixel_center,
            'direct_hit': True
        }
        return result
    
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
        self.torpedo_player_hit_by_ring = []
        self.torpedo_player_start_pos = None
    
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

        # Handle zero distance case (firing at own position or very close)
        if total_distance < 1:
            # Immediate explosion at target
            travel_time = 0
        else:
            travel_time = (total_distance / self.torpedo_speed) * 1000

        if travel_time > 0 and elapsed < travel_time:
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

            # Get maximum explosion radius from constants
            max_visual_radius = getattr(constants, 'TORPEDO_EXPLOSION_MAX_VISUAL_RADIUS', 80)
            num_waves = constants.TORPEDO_EXPLOSION_ANIMATION_WAVES

            # Create multiple expanding waves for interesting visual effect
            waves = []
            for wave_index in range(num_waves):
                wave_start_time = wave_index * constants.TORPEDO_EXPLOSION_WAVE_DELAY
                if explosion_elapsed >= wave_start_time:
                    wave_elapsed = explosion_elapsed - wave_start_time
                    # Each wave expands from 10 to max_visual_radius, with outer waves smaller
                    max_wave_radius = max_visual_radius - (wave_index * (max_visual_radius / (num_waves + 2)))
                    wave_radius = min(10 + (wave_elapsed / 8), max_wave_radius)  # Faster expansion for larger radius
                    wave_opacity = max(0, 255 - (wave_elapsed / 4))  # Slightly slower fade for larger effect
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
    
    def enemy_fire_phaser(self, enemy_ship, start_pos, target_pos, damage, weapon_type='disruptor'):
        """
        Start an enemy phaser/disruptor animation targeting the player.
        
        Args:
            enemy_ship: Enemy ship object firing
            start_pos: Starting position in pixels (enemy position)
            target_pos: Target position in pixels (player position)
            damage: Damage amount to apply when animation completes
            weapon_type: Type of weapon ('disruptor' or 'phaser')
        """
        import pygame
        
        # Create enemy phaser/disruptor animation
        animation = {
            'type': weapon_type,  # Keep track of weapon type for visual differentiation
            'start_time': pygame.time.get_ticks(),  # Use pygame time consistently
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
        import pygame

        # Calculate torpedo flight time
        distance_pixels = math.hypot(target_pos[0] - start_pos[0], target_pos[1] - start_pos[1])
        flight_time = (distance_pixels / self.enemy_torpedo_speed) * 1000  # Convert to milliseconds
        explosion_duration = 1200  # ms - Duration for explosion animation

        # Create enemy torpedo animation
        animation = {
            'type': 'torpedo',
            'state': 'traveling',  # 'traveling' or 'exploding'
            'start_time': pygame.time.get_ticks(),
            'flight_duration': flight_time,
            'explosion_duration': explosion_duration,
            'explosion_start_time': None,
            'enemy_ship': enemy_ship,
            'start_pos': start_pos,
            'target_pos': target_pos,
            'current_pos': start_pos,
            'damage': damage,
            'applied': False
        }

        self.enemy_torpedo_animations.append(animation)

        # Play enemy torpedo sound
        from ui.sound_manager import get_sound_manager
        sound_manager = get_sound_manager()
        sound_manager.play_sound('torpedo')  # Reuse torpedo sound
    
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
                # Phaser animation complete - check evasion then apply damage
                if not animation['applied']:
                    if self._check_player_evasion('phaser'):
                        # Evasion successful - log it
                        if self.add_event_log:
                            self.add_event_log("Evasive maneuvers! Enemy disruptor missed!")
                    else:
                        # No evasion - apply damage
                        self.player_ship.apply_damage(animation['damage'], animation['enemy_ship'])
                    animation['applied'] = True

                # Remove completed animation
                self.enemy_phaser_animations.remove(animation)
        
        # Update enemy torpedo animations
        for animation in self.enemy_torpedo_animations[:]:  # Copy list to avoid modification during iteration
            elapsed = current_time_ms - animation['start_time']

            # Handle state-based animation
            if animation.get('state') == 'traveling':
                flight_duration = animation.get('flight_duration', animation.get('duration', 1000))
                progress = elapsed / flight_duration

                if progress >= 1.0:
                    # Torpedo reached target - transition to explosion
                    animation['state'] = 'exploding'
                    animation['explosion_start_time'] = current_time_ms
                    animation['current_pos'] = animation['target_pos']

                    # Play explosion sound
                    from ui.sound_manager import get_sound_manager
                    sound_manager = get_sound_manager()
                    sound_manager.play_sound('explosion')

                    # Mark that we need to check for damage (will be done in draw phase with current player pos)
                    animation['damage_check_pending'] = True
                else:
                    # Update torpedo position during flight
                    start_x, start_y = animation['start_pos']
                    target_x, target_y = animation['target_pos']

                    current_x = start_x + (target_x - start_x) * progress
                    current_y = start_y + (target_y - start_y) * progress
                    animation['current_pos'] = (current_x, current_y)

            elif animation.get('state') == 'exploding':
                # Check if explosion animation is complete
                explosion_elapsed = current_time_ms - animation['explosion_start_time']
                explosion_duration = animation.get('explosion_duration', 1200)

                if explosion_elapsed >= explosion_duration:
                    # Remove completed animation
                    self.enemy_torpedo_animations.remove(animation)
            else:
                # Legacy handling for animations without state (backwards compatibility)
                # Upgrade to new state-based system
                animation['state'] = 'traveling'
                animation['flight_duration'] = animation.get('duration', 1000)
                animation['explosion_duration'] = 1200
    
    def draw_enemy_weapon_animations(self, screen, current_time_ms, hex_grid=None, player_render_pos=None):
        """
        Draw all enemy weapon animations.
        
        Args:
            screen: Pygame screen surface
            current_time_ms: Current time in milliseconds
            hex_grid: Hex grid for coordinate conversion (needed for real-time targeting)
            player_render_pos: Actual pixel position where player is rendered (for accurate targeting)
        """
        # Draw enemy phaser/disruptor animations
        for animation in self.enemy_phaser_animations:
            elapsed = current_time_ms - animation['start_time']
            progress = elapsed / animation['duration']
            
            
            if 0 <= progress <= 1.0:
                # Get real-time enemy ship position
                if hex_grid and 'enemy_ship' in animation:
                    enemy_ship = animation['enemy_ship']
                    enemy_hex_pos = enemy_ship.get_render_position()
                    start_pos = hex_grid.get_hex_center(enemy_hex_pos[0], enemy_hex_pos[1])
                else:
                    # Fallback to stored position if hex_grid not available
                    start_pos = animation.get('start_pos', (400, 400))
                
                # Get real-time player position for accurate targeting
                if player_render_pos:
                    # Use the actual pixel position where player is rendered
                    target_pos = player_render_pos
                elif hex_grid and self.player_ship:
                    # Fallback to hex coordinate conversion
                    player_hex_pos = getattr(self.player_ship, 'position', (10, 10))
                    target_pos = hex_grid.get_hex_center(player_hex_pos[0], player_hex_pos[1])
                else:
                    # Fallback to stored position if neither available
                    target_pos = animation['target_pos']
                
                weapon_type = animation.get('type', 'disruptor')
                
                # Calculate beam properties
                alpha = int(255 * (1.0 - progress))  # Fade out over time
                
                thickness = max(1, int(5 * (1.0 - progress)))  # Thicker for disruptors
                
                # Choose color based on weapon type
                if weapon_type == 'disruptor':
                    # Green disruptor beam for Klingon ships
                    color = (100, 255, 100, alpha)  # Bright green
                else:
                    # Red phaser beam for other enemy types
                    color = (255, 100, 100, alpha)  # Red
                
                if alpha > 0:
                    pygame.draw.line(screen, color[:3], start_pos, target_pos, thickness)
        
        # Draw enemy torpedo animations with distinct red/crimson style
        for animation in self.enemy_torpedo_animations:
            current_pos = animation['current_pos']
            state = animation.get('state', 'traveling')

            if state == 'traveling':
                # Draw TARGET INDICATOR at the torpedo's destination
                # This warns the player where the torpedo is aimed
                target_x, target_y = animation['target_pos']
                target_x, target_y = int(target_x), int(target_y)

                # Pulsing effect for target reticle
                pulse = abs(math.sin(current_time_ms / 150.0))
                reticle_alpha = int(100 + pulse * 80)  # Pulsing transparency

                # Calculate time remaining for urgency indication
                flight_duration = animation.get('flight_duration', 1000)
                elapsed = current_time_ms - animation['start_time']
                progress = min(1.0, elapsed / flight_duration)
                time_remaining_ratio = 1.0 - progress

                # Reticle shrinks as torpedo approaches (more urgent)
                base_radius = 40
                reticle_radius = int(base_radius * (0.5 + time_remaining_ratio * 0.5))

                # Color becomes more intense (brighter red) as torpedo approaches
                red_intensity = int(150 + (1.0 - time_remaining_ratio) * 105)
                reticle_color = (red_intensity, 30, 30)

                # Draw outer targeting circle
                pygame.draw.circle(screen, reticle_color, (target_x, target_y), reticle_radius, 2)

                # Draw inner crosshairs
                crosshair_size = int(reticle_radius * 0.6)
                pygame.draw.line(screen, reticle_color,
                    (target_x - crosshair_size, target_y),
                    (target_x + crosshair_size, target_y), 2)
                pygame.draw.line(screen, reticle_color,
                    (target_x, target_y - crosshair_size),
                    (target_x, target_y + crosshair_size), 2)

                # Draw corner brackets for tactical look
                bracket_size = int(reticle_radius * 0.3)
                bracket_offset = reticle_radius - 5
                # Top-left bracket
                pygame.draw.line(screen, reticle_color,
                    (target_x - bracket_offset, target_y - bracket_offset),
                    (target_x - bracket_offset + bracket_size, target_y - bracket_offset), 2)
                pygame.draw.line(screen, reticle_color,
                    (target_x - bracket_offset, target_y - bracket_offset),
                    (target_x - bracket_offset, target_y - bracket_offset + bracket_size), 2)
                # Top-right bracket
                pygame.draw.line(screen, reticle_color,
                    (target_x + bracket_offset, target_y - bracket_offset),
                    (target_x + bracket_offset - bracket_size, target_y - bracket_offset), 2)
                pygame.draw.line(screen, reticle_color,
                    (target_x + bracket_offset, target_y - bracket_offset),
                    (target_x + bracket_offset, target_y - bracket_offset + bracket_size), 2)
                # Bottom-left bracket
                pygame.draw.line(screen, reticle_color,
                    (target_x - bracket_offset, target_y + bracket_offset),
                    (target_x - bracket_offset + bracket_size, target_y + bracket_offset), 2)
                pygame.draw.line(screen, reticle_color,
                    (target_x - bracket_offset, target_y + bracket_offset),
                    (target_x - bracket_offset, target_y + bracket_offset - bracket_size), 2)
                # Bottom-right bracket
                pygame.draw.line(screen, reticle_color,
                    (target_x + bracket_offset, target_y + bracket_offset),
                    (target_x + bracket_offset - bracket_size, target_y + bracket_offset), 2)
                pygame.draw.line(screen, reticle_color,
                    (target_x + bracket_offset, target_y + bracket_offset),
                    (target_x + bracket_offset, target_y + bracket_offset - bracket_size), 2)

                # Draw menacing red/orange enemy torpedo projectile
                # Distinct from player's white/yellow torpedo
                tx, ty = int(current_pos[0]), int(current_pos[1])

                # Pulsing effect based on time
                pulse = abs(math.sin(current_time_ms / 100.0))

                # Outer crimson glow (larger, semi-transparent)
                glow_radius = int(10 + pulse * 3)
                pygame.draw.circle(screen, (180, 30, 30), (tx, ty), glow_radius, 3)

                # Middle orange ring
                pygame.draw.circle(screen, (255, 100, 0), (tx, ty), 7, 2)

                # Inner red core
                pygame.draw.circle(screen, (255, 50, 50), (tx, ty), 5)

                # Bright center highlight
                pygame.draw.circle(screen, (255, 200, 150), (tx, ty), 2)

                # Draw trajectory line from torpedo to target (faint)
                pygame.draw.line(screen, (100, 30, 30), (tx, ty), (target_x, target_y), 1)

            elif state == 'exploding':
                # Check for damage based on actual player position (only once when explosion starts)
                if animation.get('damage_check_pending') and not animation.get('applied'):
                    explosion_center = current_pos
                    damage_radius = 120  # pixels - same as visual max_radius

                    # Get current player position
                    if player_render_pos:
                        player_pos = player_render_pos
                    elif hex_grid and self.player_ship:
                        player_hex_pos = getattr(self.player_ship, 'position', (10, 10))
                        player_pos = hex_grid.get_hex_center(player_hex_pos[0], player_hex_pos[1])
                    else:
                        player_pos = None

                    if player_pos:
                        # Calculate distance from explosion to player
                        dx = player_pos[0] - explosion_center[0]
                        dy = player_pos[1] - explosion_center[1]
                        distance = math.hypot(dx, dy)

                        # Only apply damage if player is within explosion radius
                        if distance <= damage_radius:
                            # Damage falls off with distance (quadratic falloff)
                            distance_ratio = distance / damage_radius
                            damage_multiplier = max(0, 1.0 - (distance_ratio * distance_ratio))
                            actual_damage = int(animation['damage'] * damage_multiplier)

                            if actual_damage > 0:
                                # Check evasion before applying torpedo damage
                                if self._check_player_evasion('torpedo'):
                                    # Evasion successful - log it
                                    if self.add_event_log:
                                        self.add_event_log("Evasive maneuvers! Avoided torpedo blast!")
                                else:
                                    # No evasion - apply damage
                                    self.player_ship.apply_damage(actual_damage, animation['enemy_ship'])

                    animation['applied'] = True
                    animation['damage_check_pending'] = False

                # Draw distinctive enemy torpedo explosion
                # Uses crimson/red expanding rings (vs player's white/yellow/orange)
                explosion_elapsed = current_time_ms - animation['explosion_start_time']
                explosion_duration = animation.get('explosion_duration', 1200)
                explosion_progress = min(1.0, explosion_elapsed / explosion_duration)

                ex, ey = int(current_pos[0]), int(current_pos[1])

                # Draw multiple expanding crimson rings
                num_rings = 6
                max_radius = 120  # Maximum explosion radius

                for ring_idx in range(num_rings):
                    # Stagger ring appearance
                    ring_delay = ring_idx * 80  # ms between each ring
                    ring_elapsed = explosion_elapsed - ring_delay

                    if ring_elapsed > 0:
                        # Calculate ring properties
                        ring_progress = min(1.0, ring_elapsed / (explosion_duration * 0.7))
                        ring_radius = int(10 + ring_progress * max_radius)

                        # Fade out as ring expands
                        ring_alpha = int(255 * (1.0 - ring_progress))

                        if ring_alpha > 0:
                            # Color gradient: bright crimson center to dark red outer
                            if ring_idx == 0:
                                color = (255, 100, 50)   # Orange-red center
                            elif ring_idx == 1:
                                color = (255, 50, 50)    # Bright red
                            elif ring_idx == 2:
                                color = (200, 30, 30)    # Crimson
                            elif ring_idx == 3:
                                color = (150, 20, 50)    # Dark crimson
                            else:
                                color = (100, 10, 30)    # Deep maroon

                            # Draw ring with thickness decreasing as it expands
                            thickness = max(1, int(4 * (1.0 - ring_progress)))
                            pygame.draw.circle(screen, color, (ex, ey), ring_radius, thickness)

                # Draw central flash at start of explosion
                if explosion_progress < 0.3:
                    flash_intensity = 1.0 - (explosion_progress / 0.3)
                    flash_radius = int(15 + explosion_progress * 30)
                    flash_alpha = int(200 * flash_intensity)
                    if flash_alpha > 0:
                        pygame.draw.circle(screen, (255, 200, 100), (ex, ey), flash_radius)
                        pygame.draw.circle(screen, (255, 255, 200), (ex, ey), int(flash_radius * 0.5))

    def stop_all_animations(self):
        """Force stop all weapon animations (emergency cleanup)."""
        self.phaser_animating = False
        self.torpedo_flying = False
        self._complete_torpedo_attack()
        self.phaser_target_enemy = None
        self.phaser_combat_result = None