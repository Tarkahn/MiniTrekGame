from data import constants
from ship.ship_systems.shield import Shield


class BaseShip:
    """
    Base class for all ships in the Star Trek Tactical Game.
    Defines common attributes and basic functionalities for ship systems.
    """

    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons, position):
        self.name = name
        self.shield_system = Shield(max_shield_strength, self)  # Use composition for shields
        self.max_hull_strength = hull_strength  # Initialize max_hull_strength
        self.hull_strength = hull_strength
        self.warp_core_energy = energy
        self.max_warp_core_energy = max_energy
        self.weapons = weapons or []
        self.position = position

    def apply_damage(self, raw_damage: int):
        """
        Applies damage to the ship, prioritizing shields then hull.
        """
        remaining_damage = self.shield_system.absorb_damage(raw_damage)

        # Apply any remaining damage to hull
        self.hull_strength -= remaining_damage
        self.hull_strength = max(0, self.hull_strength)  # Ensure hull doesn't go below 0

    def reset_damage(self):
        """
        Resets hull and shield integrity to their maximum values.
        Typically called when docking at a starbase.
        """
        self.hull_strength = self.max_hull_strength
        self.shield_system.current_strength = 0  # Reset shield system current strength

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