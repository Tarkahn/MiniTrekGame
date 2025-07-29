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
        PRD: Fires the phaser at a target, if not on cooldown and enough energy.
        Returns the damage dealt, or 0 if unable to fire.
        """
        if self.is_on_cooldown():
            print(f"Phasers on cooldown. Wait {self._last_fired_time + self.cooldown_seconds - time.time():.1f} seconds.")
            return 0

        if target_distance > self.range:
            print(f"Target is out of phaser range (max {self.range} hexes).")
            return 0

        # PRD: Check system integrity
        if hasattr(self.ship, 'system_integrity') and self.ship.system_integrity['phasers'] <= 0:
            print(f"Phaser system disabled on {self.ship.name}.")
            return 0

        if not self.ship.consume_energy(self.energy_cost_per_shot):
            print(f"Insufficient energy on {self.ship.name} to fire phasers.")
            return 0

        # PRD: Damage formula (Power Level × 10) − (Distance × 3)
        # Use power allocation to modify effectiveness
        power_modifier = 1.0
        if hasattr(self.ship, 'power_allocation'):
            power_level = self.ship.power_allocation.get('phasers', 5)
            power_modifier = power_level / 5.0  # Scale around default level 5
            
        base_damage = (self.power * power_modifier * 10) - (target_distance * 3)
        
        # PRD: Critical hits (15% chance, 1.5x damage)
        is_critical_hit = random.random() < constants.CRITICAL_HIT_CHANCE
        if is_critical_hit:
            base_damage *= constants.CRITICAL_HIT_MULTIPLIER
            print("Critical Hit!")

        actual_damage = max(0, int(base_damage))

        self._last_fired_time = time.time()
        print(f"{self.ship.name} fired phasers (power {power_modifier:.1f}x). Damage: {actual_damage}. Energy: {self.ship.warp_core_energy}")
        return actual_damage 