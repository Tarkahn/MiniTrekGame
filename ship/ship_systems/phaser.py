import time
import random
from data import constants
from ship.base_ship import BaseShip


class Phaser:
    def __init__(self, power: int, range: int, ship: BaseShip):
        self.power = power
        self.range = range
        self.ship = ship  # The ship this phaser belongs to
        self.energy_cost_per_shot = constants.PHASER_ENERGY_COST
        self.cooldown_seconds = constants.PHASER_COOLDOWN_SECONDS
        self._last_fired_time = 0

    def is_on_cooldown(self) -> bool:
        return time.time() < self._last_fired_time + self.cooldown_seconds

    def fire(self, target_distance: int) -> int:
        """
        Fires the phaser at a target, if not on cooldown and enough energy.
        Returns the damage dealt, or 0 if unable to fire.
        """
        if self.is_on_cooldown():
            print(f"Phasers on cooldown. Wait {self._last_fired_time + self.cooldown_seconds - time.time():.1f} seconds.")
            return 0

        if target_distance > self.range:
            print(f"Target is out of phaser range (max {self.range} hexes).")
            return 0

        if not self.ship.consume_energy(self.energy_cost_per_shot):
            print(f"Insufficient energy on {self.ship.name} to fire phasers.")
            return 0

        damage = (self.power * 10) - (target_distance * 3)  # Example damage calculation
        
        is_critical_hit = random.random() < constants.CRITICAL_HIT_CHANCE
        if is_critical_hit:
            damage *= constants.CRITICAL_HIT_MULTIPLIER
            print("Critical Hit!")

        actual_damage = max(0, damage)

        self._last_fired_time = time.time()
        print(f"{self.ship.name} fired phasers. Damage dealt: {actual_damage}. Energy remaining: {self.ship.warp_core_energy}")
        return actual_damage 