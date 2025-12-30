from ship.base_ship import BaseShip
from data import constants
from game_logic.navigation import warp_to_sector
from game_logic.combat_manager import CombatManager
from ship.ship_systems.phaser import Phaser
from ship.ship_systems.torpedo import Torpedo
from ship.ship_systems.shield import Shield
from ship.ship_systems.repair_system import RepairSystem


class PlayerShip(BaseShip):
    """
    Represents the player's Starfleet vessel.
    Extends BaseShip with player-specific actions and controls.
    """

    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons=None, position=None):
        player_shield = Shield(max_shield_strength, self)
        super().__init__(name, player_shield, hull_strength, energy, max_energy, weapons, position)
        self.phaser_system = Phaser(power=constants.PLAYER_PHASER_POWER, range=constants.PLAYER_PHASER_RANGE, ship=self)
        self.torpedo_system = Torpedo(power=constants.PLAYER_TORPEDO_POWER, speed=constants.PLAYER_TORPEDO_SPEED, accuracy=constants.PLAYER_TORPEDO_ACCURACY, ship=self)
        self.combat_manager = CombatManager()
        self.repair_system = RepairSystem(self)

    def move_ship(self, hex_count: int, shield_power: int = 0) -> bool:
        """
        Moves the ship a specified number of hexes using Impulse Engines.
        Consumes energy.
        Returns True if movement is successful, False otherwise.
        """
        energy_cost = hex_count * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
        if not self.consume_energy(energy_cost):
            print("Insufficient energy for impulse movement.")
            return False
        
        # Removed automatic shield activation during movement as shield management is a separate player action.
        # self.shield_system.activate(shield_power)
        # Actual map movement logic would go here, which is outside this class's scope
        print(f"Moved {hex_count} hexes. Energy remaining: {self.warp_core_energy}")
        return True

    def fire_phasers(self, target_ship, target_distance: int) -> int:
        """
        Fires phasers at a target, delegating to the phaser system.
        Returns damage dealt.
        """
        damage_dealt = self.phaser_system.fire(target_distance)
        if damage_dealt > 0:
            target_ship.apply_damage(damage_dealt)
        return damage_dealt

    def initiate_warp(self, sectors_to_travel: int) -> bool:
        """
        Initiates warp travel to a distant sector using the navigation module.
        Returns True if warp is successful, False otherwise.
        """
        # The energy consumption logic is now handled by warp_to_sector
        if not warp_to_sector(self, sectors_to_travel):
            return False
        
        print(f"Initiated warp travel for {sectors_to_travel} sectors. Energy remaining: {self.warp_core_energy}")
        # Turn consumption and actual map transition logic handled by game loop
        return True

    def fire_phasers_at_target(self, target_enemy, distance):
        """
        Fire phasers at a target enemy using the combat manager.
        This method provides a clean interface for UI code to initiate combat
        without handling damage calculations directly.
        
        Args:
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes to target
            
        Returns:
            dict: Combat result from CombatManager.fire_phasers()
        """
        return self.combat_manager.fire_phasers(self, target_enemy, distance)
    
    def fire_torpedoes_at_target(self, target_enemy, distance):
        """
        Fire torpedoes at a target enemy using the combat manager.
        
        Args:
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes to target
            
        Returns:
            dict: Combat result from CombatManager.fire_torpedoes()
        """
        return self.combat_manager.fire_torpedoes(self, target_enemy, distance)
    
    def calculate_phaser_damage_at_target(self, target_enemy, distance):
        """
        Calculate phaser damage without applying it to the target.
        
        Args:
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes to target
            
        Returns:
            dict: Combat calculation from CombatManager.calculate_phaser_damage()
        """
        return self.combat_manager.calculate_phaser_damage(self, target_enemy, distance)
    
    def calculate_torpedo_damage_at_target(self, target_enemy, distance):
        """
        Calculate torpedo damage without applying it to the target.
        
        Args:
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes to target
            
        Returns:
            dict: Combat calculation from CombatManager.calculate_torpedo_damage()
        """
        return self.combat_manager.calculate_torpedo_damage(self, target_enemy, distance)
    
    def apply_damage_to_enemy(self, target_enemy, combat_result):
        """
        Apply calculated damage to an enemy.

        Args:
            target_enemy: Enemy map object to damage
            combat_result: Result from calculate_phaser_damage_at_target or calculate_torpedo_damage_at_target

        Returns:
            dict: Updated combat result with actual enemy status after damage
        """
        return self.combat_manager.apply_damage_to_enemy(target_enemy, combat_result)

    def toggle_repairs(self) -> bool:
        """
        Toggle the ship's repair system on/off.

        Returns:
            True if repairs are now active, False if stopped or couldn't start
        """
        return self.repair_system.toggle_repairs()

    def update_repairs(self, delta_time_seconds: float) -> dict:
        """
        Update repair progress. Should be called each frame.

        Args:
            delta_time_seconds: Time elapsed since last update

        Returns:
            Dictionary of systems that were repaired
        """
        return self.repair_system.update(delta_time_seconds)

    def update(self, delta_time_seconds: float):
        """
        Main update method - handles all time-based updates for the player ship.
        Should be called each frame.

        Args:
            delta_time_seconds: Time elapsed since last update
        """
        # Update shield system (regeneration and energy consumption)
        if hasattr(self, 'shield_system') and self.shield_system:
            self.shield_system.update(delta_time_seconds)

        # Update warp core energy regeneration
        self._update_energy_regeneration(delta_time_seconds)

        # Update repairs
        self.repair_system.update(delta_time_seconds)

    def _update_energy_regeneration(self, delta_time: float):
        """Regenerate warp core energy over time."""
        # Only regenerate if below max
        if self.warp_core_energy >= self.max_warp_core_energy:
            return

        # Calculate energy to regenerate based on delta_time
        regen_rate = constants.WARP_CORE_REGEN_RATE_PER_SECOND
        energy_to_add = regen_rate * delta_time

        # Add energy, capped at max
        self.warp_core_energy = min(
            self.max_warp_core_energy,
            self.warp_core_energy + energy_to_add
        )

    def is_repairing(self) -> bool:
        """Check if repairs are currently in progress."""
        return self.repair_system.is_repairing

    def get_repair_status(self) -> dict:
        """Get current repair status for UI display."""
        return self.repair_system.get_repair_status() 