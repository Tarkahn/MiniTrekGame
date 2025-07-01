from ship.base_ship import BaseShip
from data import constants
from game_logic.navigation import warp_to_sector
from ship.ship_systems.phaser import Phaser


class PlayerShip(BaseShip):
    """
    Represents the player's Starfleet vessel.
    Extends BaseShip with player-specific actions and controls.
    """

    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons=None, position=None):
        super().__init__(name, max_shield_strength, hull_strength, energy, max_energy, weapons, position)
        self.phaser_system = Phaser(power=50, range=9, ship=self)  # Example values for player phaser

    def move_ship(self, hex_count: int, shield_power: int = 0) -> bool:
        """
        Moves the ship a specified number of hexes using Impulse Engines.
        Consumes energy and updates shield power if provided.
        Returns True if movement is successful, False otherwise.
        """
        energy_cost = hex_count * constants.WARP_ENERGY_COST
        if not self.consume_energy(energy_cost):
            print("Insufficient energy for impulse movement.")
            return False
        
        self.shield_system.activate(shield_power)
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

    # Player-specific methods will be added here
    pass 