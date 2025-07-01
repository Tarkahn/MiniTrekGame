from data import constants
from ship.base_ship import BaseShip


class Shield:
    def __init__(self, max_strength: int, ship: BaseShip):
        self.max_strength = max_strength
        self.current_strength = 0  # Shields start down/offline
        self.ship = ship
        self.energy_cost_per_level = constants.SHIELD_ENERGY_COST_PER_LEVEL
        self.regeneration_rate = constants.SHIELD_REGEN_RATE  # Regeneration per turn when active

    def activate(self, power_level: int) -> bool:
        """
        Activates shields to a specific power level, consuming energy.
        Returns True if activation is successful, False otherwise.
        """
        if power_level < 0 or power_level > self.max_strength:
            print(f"Invalid shield power level: {power_level}. Must be between 0 and {self.max_strength}.")
            return False

        energy_needed = power_level * self.energy_cost_per_level
        if not self.ship.consume_energy(energy_needed):
            print(f"Insufficient energy to activate shields to level {power_level}.")
            return False

        self.current_strength = power_level
        print(f"Shields activated to level {self.current_strength}. Energy remaining: {self.ship.warp_core_energy}")
        return True

    def absorb_damage(self, incoming_damage: int) -> int:
        """
        Absorbs incoming damage, reducing shield strength.
        Returns remaining damage after absorption.
        """
        absorbed = min(self.current_strength, incoming_damage)
        self.current_strength -= absorbed
        print(f"Shields absorbed {absorbed} damage. Current shield strength: {self.current_strength}")
        return incoming_damage - absorbed

    def recharge(self):
        """
        Recharges shields by a fixed rate, up to max_strength.
        """
        self.current_strength = min(self.max_strength, self.current_strength + self.regeneration_rate)
        print(f"Shields recharged. Current strength: {self.current_strength}")

    def deactivate(self):
        """
        Deactivates shields, setting current strength to 0.
        """
        self.current_strength = 0
        print("Shields deactivated.") 