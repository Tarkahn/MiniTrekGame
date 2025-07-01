from ship.base_ship import BaseShip
from data import constants
import time


class PlayerShip(BaseShip):
    """
    Represents the player's Starfleet vessel.
    Extends BaseShip with player-specific actions and controls.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phaser_cooldown_end_time = 0
        self.shield_power_level = 0 # Player-controlled shield power

    def move_ship(self, hex_count: int, shield_power: int = 0) -> bool:
        """
        Moves the ship a specified number of hexes using Impulse Engines.
        Consumes energy and updates shield power if provided.
        Returns True if movement is successful, False otherwise.
        """
        energy_cost = hex_count * constants.WARP_ENERGY_COST  # Assuming 10 energy per hex for warp.
        if not self.consume_energy(energy_cost):
            print("Insufficient energy for impulse movement.")
            return False
        
        self.shield_power_level = shield_power  # Set shield power level for this move
        # Actual map movement logic would go here, which is outside this class's scope
        print(f"Moved {hex_count} hexes. Energy remaining: {self.warp_core_energy}")
        return True

    def fire_phasers(self, target_distance: int, phaser_power_level: int) -> int:
        """
        Fires phasers at a target, considering range, power, and cooldown.
        Returns damage dealt.
        """
        if time.time() < self.phaser_cooldown_end_time:
            print(f"Phasers on cooldown. Wait {self.phaser_cooldown_end_time - time.time():.1f} seconds.")
            return 0
        
        if phaser_power_level == 0:
            print("Phasers are at power level 0 and cannot fire.")
            return 0

        if target_distance > 9:
            print("Target is out of phaser range (max 9 hexes).")
            return 0

        # Energy cost per shot
        if not self.consume_energy(constants.PHASER_ENERGY_COST):
            print("Insufficient energy to fire phasers.")
            return 0

        damage = (phaser_power_level * 10) - (target_distance * 3)
        actual_damage = max(0, damage)

        self.phaser_cooldown_end_time = time.time() + constants.PHASER_COOLDOWN_SECONDS
        print(f"Fired phasers. Damage dealt: {actual_damage}. Energy remaining: {self.warp_core_energy}")
        return actual_damage

    def initiate_warp(self, sectors_to_travel: int) -> bool:
        """
        Initiates warp travel to a distant sector.
        Consumes energy and turns.
        Returns True if warp is successful, False otherwise.
        """
        initiation_cost = 20  # from PRD
        energy_per_sector = constants.WARP_ENERGY_COST  # 10 units per sector hex
        total_energy_cost = initiation_cost + (sectors_to_travel * energy_per_sector)

        if not self.consume_energy(total_energy_cost):
            print("Insufficient energy for warp travel.")
            return False
        
        print(f"Initiated warp travel for {sectors_to_travel} sectors. Energy remaining: {self.warp_core_energy}")
        # Turn consumption and actual map transition logic handled by game loop
        return True

    # Player-specific methods will be added here
    pass 