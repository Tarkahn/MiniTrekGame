from data import constants


class BaseShip:
    """
    Base class for all ships in the Star Trek Tactical Game.
    Defines common attributes and basic functionalities for ship systems.
    """

    def __init__(self, hull_integrity: int = 100, shield_integrity: int = 0):
        self.max_hull_integrity = 100
        self.hull_integrity = hull_integrity  # Current hull health (0-100)
        
        self.max_shield_integrity = 100
        self.shield_integrity = shield_integrity  # Current shield (0-100)
        
        self.warp_core_energy = 1000  # Current energy in Warp Core
        self.max_warp_core_energy = 1000  # Maximum energy capacity

    def calculate_damage(self, raw_damage: int, shield_power_level: int) -> int:
        """
        Calculates the effective damage after shield absorption.
        """
        absorbed_by_shields = shield_power_level * constants.SHIELD_ABSORPTION_PER_LEVEL
        effective_damage = max(0, raw_damage - absorbed_by_shields)
        return effective_damage

    def apply_damage(self, raw_damage: int, shield_power_level: int):
        """
        Applies damage to the ship, prioritizing shields then hull.
        """
        damage_after_shields = self.calculate_damage(raw_damage, shield_power_level)

        # Apply damage to hull
        self.hull_integrity -= damage_after_shields
        self.hull_integrity = max(0, self.hull_integrity)  # Ensure hull doesn't go below 0

    def reset_damage(self):
        """
        Resets hull and shield integrity to their maximum values.
        Typically called when docking at a starbase.
        """
        self.hull_integrity = self.max_hull_integrity
        self.shield_integrity = self.max_shield_integrity

    def allocate_energy(self, amount: int):
        """
        Adds energy to the Warp Core, up to its maximum capacity.
        """
        self.warp_core_energy = min(self.max_warp_core_energy, self.warp_core_energy + amount)

    def consume_energy(self, amount: int) -> bool:
        """
        Consumes energy from the Warp Core if available.
        Returns True if successful, False otherwise.
        """
        if self.warp_core_energy >= amount:
            self.warp_core_energy -= amount
            return True
        return False

    def regenerate_energy(self):
        """
        Instantly restores Warp Core energy to maximum capacity.
        Typically called when docking at a starbase.
        """
        self.warp_core_energy = self.max_warp_core_energy 