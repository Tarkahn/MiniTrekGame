from data import constants


class BaseShip:
    """
    Base class for all ships in the Star Trek Tactical Game.
    Defines common attributes and basic functionalities for ship systems.
    """

    def __init__(self, name, shield_strength, hull_strength, energy, max_energy, weapons, position):
        self.name = name
        self.shield_strength = shield_strength
        self.max_hull_strength = hull_strength  # Initialize max_hull_strength
        self.hull_strength = hull_strength
        self.warp_core_energy = energy
        self.max_warp_core_energy = max_energy
        self.weapons = weapons or []
        self.position = position

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
        self.hull_strength -= damage_after_shields
        self.hull_strength = max(0, self.hull_strength)  # Ensure hull doesn't go below 0

    def reset_damage(self):
        """
        Resets hull and shield integrity to their maximum values.
        Typically called when docking at a starbase.
        """
        self.hull_strength = self.max_hull_strength
        self.shield_strength = 0

    def allocate_energy(self, system, amount: int):
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

    def regenerate_energy_per_turn(self):
        """
        Regenerates a small amount of Warp Core energy each turn.
        """
        self.warp_core_energy = min(self.max_warp_core_energy, self.warp_core_energy + constants.ENERGY_REGEN_RATE_PER_TURN)

    def is_alive(self):
        return self.hull_strength > 0 