"""
Enemy Ship class for Klingon warships.

This module contains the EnemyShip class which represents a Klingon warship
with dynamic AI behavior controlled by the EnemyAI class.
"""

import random
import math
import time
from .base_ship import BaseShip
from data import constants
from ship.ship_systems.shield import Shield
from ship.ship_systems.repair_system import RepairSystem
from game_logic.enemy_ai import EnemyAI, EnemyPersonality


class EnemyShip(BaseShip):
    """Dynamic Klingon warship with intelligent AI and randomized personality."""

    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy,
                 weapons=None, position=None):
        enemy_shield = Shield(max_shield_strength, self)
        super().__init__(name, enemy_shield, hull_strength, energy, max_energy,
                         weapons, position)

        # Position and movement state
        self.position = position if position else (0, 0)
        self.target_position = None
        self.is_moving = False
        self.current_destination = None
        self.movement_progress = 0.0
        self.movement_start_time = 0
        self.movement_duration = 2000  # Base movement time in ms

        # Combat compatibility properties
        self._shields = max_shield_strength
        self._max_shields = max_shield_strength
        self._health = hull_strength

        # Weapon state
        self.weapon_cooldown = 0
        self.last_weapon_fire_time = 0
        self.pending_weapon_animations = []

        # Initialize AI controller with personality
        self._personality = EnemyPersonality()
        self.ai = EnemyAI(self, self._personality)

        # Initialize repair system (same as player ship)
        self.repair_system = RepairSystem(self)

        # Track last update time for delta calculations
        self._last_system_update_time = time.time()

        print(f"[KLINGON] {name} warship created with personality: "
              f"Aggression={self._personality.aggression:.2f}, "
              f"Courage={self._personality.courage:.2f}, "
              f"Speed={self._personality.movement_speed:.2f}")

    @property
    def personality(self):
        """Get personality dict for backwards compatibility."""
        return self._personality.to_dict()

    @property
    def ai_state(self):
        """Get AI state for backwards compatibility."""
        return self.ai.state

    @ai_state.setter
    def ai_state(self, value):
        """Set AI state for backwards compatibility."""
        self.ai.state = value

    @property
    def target(self):
        """Get target for backwards compatibility."""
        return self.ai.target

    @target.setter
    def target(self, value):
        """Set target for backwards compatibility."""
        self.ai.set_target(value)

    @property
    def system_objects(self):
        """Get system objects for backwards compatibility."""
        return self.ai.system_objects

    @system_objects.setter
    def system_objects(self, value):
        """Set system objects for backwards compatibility."""
        self.ai.set_system_objects(value)

    @property
    def shields(self):
        """
        Shield strength for combat system compatibility.
        Returns effective shield capacity based on power level and integrity.
        """
        if hasattr(self, 'shield_system') and self.shield_system:
            power_level = self.shield_system.current_power_level
            integrity = self.shield_system.current_integrity
            absorption_per_level = self.shield_system.absorption_per_level
            # Effective shields = power level * absorption per level * integrity factor
            return int(power_level * absorption_per_level * (integrity / 100.0))
        return self._shields

    @shields.setter
    def shields(self, value):
        """Set shield strength for combat system compatibility."""
        old_shields = self.shields  # Use property to get current value
        self._shields = max(0, value)
        if old_shields > value:
            damage = old_shields - value
            self.ai.record_damage(damage)

    @property
    def health(self):
        """Hull health for combat system compatibility."""
        # Return actual hull_strength from BaseShip if available
        if hasattr(self, 'hull_strength'):
            return self.hull_strength
        return self._health

    @health.setter
    def health(self, value):
        """Set hull health for combat system compatibility."""
        old_health = self.health  # Use property to get current value
        self._health = max(0, value)
        # Also sync with hull_strength
        if hasattr(self, 'hull_strength'):
            self.hull_strength = max(0, value)
            self.system_integrity['hull'] = max(0, value)
        if old_health > value:
            damage = old_health - value
            self.ai.record_damage(damage)

    @property
    def max_shields(self):
        """
        Maximum shield strength for combat system compatibility.
        Returns max possible shield capacity at full power and integrity.
        """
        if hasattr(self, 'shield_system') and self.shield_system:
            # Max shields = max power level * absorption per level (at 100% integrity)
            return self.shield_system.max_power_level * self.shield_system.absorption_per_level
        return self._max_shields

    @property
    def preferred_range(self):
        """Get preferred attack range from AI."""
        return self.ai.preferred_range

    @property
    def under_attack(self):
        """Check if ship is in retaliation mode."""
        return self.ai.under_attack

    @property
    def last_player_position(self):
        """Get last known player position from AI."""
        return self.ai.last_player_position

    def get_health_percentage(self):
        """Get current health as percentage of maximum."""
        max_health = self.max_hull_strength
        return self._health / max_health if max_health > 0 else 0

    def get_shield_percentage(self):
        """Get current shields as percentage of maximum."""
        return self._shields / self._max_shields if self._max_shields > 0 else 0

    def set_target(self, target):
        """Set the player ship as our target."""
        self.ai.set_target(target)

    def set_system_objects(self, system_objects):
        """Set all objects in the current system for tactical awareness."""
        self.ai.set_system_objects(system_objects)

    def update_ai(self, delta_time):
        """Main AI update loop - delegates to AI controller."""
        # Update movement animation
        self._update_movement_animation()

        # Update weapon cooldowns
        self._update_weapon_cooldowns()

        # Update shield system (regeneration and energy consumption)
        if hasattr(self, 'shield_system') and self.shield_system:
            self.shield_system.update(delta_time)

        # Update repair system if repairs are active
        if hasattr(self, 'repair_system'):
            self.repair_system.update(delta_time)

        # Delegate to AI controller
        self.ai.update(delta_time)

    def _update_movement_animation(self):
        """Update position if currently moving."""
        if not self.is_moving or not self.target_position:
            return

        current_time = time.time() * 1000
        elapsed = current_time - self.movement_start_time
        progress = min(elapsed / self.movement_duration, 1.0)

        if progress >= 1.0:
            # Movement complete
            self.position = self.target_position
            self.is_moving = False
            self.target_position = None
            self.current_destination = None
        else:
            # Interpolate position
            start_x, start_y = self.position
            target_x, target_y = self.target_position
            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress
            self.current_destination = (current_x, current_y)

    def _update_weapon_cooldowns(self):
        """Update weapon system cooldowns."""
        if self.weapon_cooldown > 0:
            current_time = time.time() * 1000
            time_since_last_shot = current_time - self.last_weapon_fire_time
            self.weapon_cooldown = max(0, self.weapon_cooldown - time_since_last_shot)

    def start_movement(self, target_position):
        """Begin movement animation to target position."""
        constrained_position = self._constrain_to_grid(target_position)
        self.target_position = constrained_position
        self.is_moving = True
        self.movement_start_time = time.time() * 1000
        self.movement_duration = 2000 / self._personality.movement_speed

    def _constrain_to_grid(self, position):
        """Constrain position to stay within hex grid boundaries."""
        x, y = position
        hex_x = int(round(x))
        hex_y = int(round(y))

        constrained_x = max(0, min(hex_x, constants.GRID_COLS - 1))
        constrained_y = max(0, min(hex_y, constants.GRID_ROWS - 1))

        return (constrained_x, constrained_y)

    def get_render_position(self):
        """Get current position for rendering (includes animation)."""
        if self.is_moving and self.current_destination:
            return self.current_destination
        return self.position

    def get_pending_weapon_animations(self):
        """Return list of weapon animations for the combat system."""
        animations = self.pending_weapon_animations.copy()
        self.pending_weapon_animations.clear()
        return animations

    # Backwards compatibility methods that delegate to AI
    def _trigger_retaliation_mode(self):
        """Trigger retaliation mode - delegates to AI."""
        self.ai.trigger_retaliation_mode()

    def _move_toward_target(self):
        """Move toward target - delegates to AI."""
        self.ai.move_toward_target()

    def _move_away_from_target(self):
        """Move away from target - delegates to AI."""
        self.ai.move_away_from_target()

    def _move_to_flank_position(self):
        """Move to flank position - delegates to AI."""
        self.ai.move_to_flank_position()

    def _move_randomly(self):
        """Random movement - delegates to AI."""
        self.ai.move_randomly()

    # Repair system methods (same interface as PlayerShip)
    def toggle_repairs(self) -> bool:
        """
        Toggle the ship's repair system on/off.

        Returns:
            True if repairs are now active, False if stopped or couldn't start
        """
        return self.repair_system.toggle_repairs()

    def start_repairs(self) -> bool:
        """
        Start the repair process.

        Returns:
            True if repairs started successfully
        """
        return self.repair_system.start_repairs()

    def stop_repairs(self):
        """Stop the repair process."""
        self.repair_system.stop_repairs()

    def update_repairs(self, delta_time_seconds: float) -> dict:
        """
        Update repair progress. Should be called each frame.

        Args:
            delta_time_seconds: Time elapsed since last update

        Returns:
            Dictionary of systems that were repaired
        """
        return self.repair_system.update(delta_time_seconds)

    def is_repairing(self) -> bool:
        """Check if repairs are currently in progress."""
        return self.repair_system.is_repairing

    def get_repair_status(self) -> dict:
        """Get current repair status for UI display."""
        return self.repair_system.get_repair_status()

    def needs_repair(self) -> bool:
        """Check if the ship has any systems that need repair."""
        return self.repair_system._needs_repair()

    def should_ai_repair(self) -> bool:
        """
        Determine if the AI should start repairs based on damage level.
        AI will repair when not in active combat and has significant damage.

        Returns:
            True if AI should begin repairs
        """
        # Don't repair if already repairing
        if self.is_repairing():
            return False

        # Don't repair if no damage
        if not self.needs_repair():
            return False

        # Check if in active combat (under attack recently)
        if self.under_attack:
            return False

        # Check damage levels - repair if any system below 70%
        for system, integrity in self.system_integrity.items():
            if system == 'hull':
                if integrity < self.max_hull_strength * 0.7:
                    return True
            elif system != 'shields':  # Shields regenerate automatically
                if integrity < 70:
                    return True

        return False
