from data import constants
from ship.base_ship import BaseShip


class Shield:
    def __init__(self, max_power_level: int, ship: BaseShip):
        self.max_power_level = max_power_level  # PRD: Power level 0-9 scale
        self.current_integrity = 100  # PRD: Integrity 0-100 scale (for regeneration)
        self.ship = ship
        self.energy_cost_per_level = constants.SHIELD_ENERGY_COST_PER_LEVEL
        self.absorption_per_level = constants.SHIELD_ABSORPTION_PER_LEVEL  # PRD: 10 damage per level
        self.last_energy_drain_time = 0  # For tracking energy consumption over time

    @property
    def current_power_level(self):
        """Get current shield power level from ship's power allocation"""
        if hasattr(self.ship, 'power_allocation'):
            return self.ship.power_allocation.get('shields', 0)
        return 0

    def set_power_level(self, power_level: int) -> bool:
        """
        Sets shields to a specific power level (0-9) via ship's power allocation.
        PRD: Power allocation doesn't consume energy - only actual shield operation does.
        Returns True if successful, False otherwise.
        """
        if power_level < 0 or power_level > self.max_power_level:
            print(f"Invalid shield power level: {power_level}. Must be between 0 and {self.max_power_level}.")
            return False

        # Use the ship's power allocation system
        if hasattr(self.ship, 'allocate_power'):
            return self.ship.allocate_power('shields', power_level)
        else:
            # Fallback: set directly if power allocation system not available
            if hasattr(self.ship, 'power_allocation'):
                self.ship.power_allocation['shields'] = power_level
                print(f"Shields set to power level {power_level}.")
                return True
            return False
    
    def update(self, delta_time_seconds: float) -> bool:
        """
        Update shield system - handle energy consumption and regeneration.
        
        Args:
            delta_time_seconds: Time elapsed since last update in seconds
            
        Returns:
            True if shields are operational, False if energy depleted
        """
        import time
        current_time = time.time()
        
        # Only consume energy if shields are powered and operational
        power_level = self.current_power_level
        if power_level > 0 and self.is_operational():
            # Calculate energy needed for this time period
            energy_per_second = power_level * self.energy_cost_per_level
            energy_needed = int(energy_per_second * delta_time_seconds)
            
            # Consume energy if needed
            if energy_needed > 0:
                if not self.ship.consume_energy(energy_needed):
                    # Not enough energy - reduce shield power automatically
                    print(f"Insufficient energy for shield level {power_level}. Reducing power.")
                    # Try to find a sustainable power level
                    for lower_level in range(power_level - 1, -1, -1):
                        needed_energy = int(lower_level * self.energy_cost_per_level * delta_time_seconds)
                        if needed_energy == 0 or self.ship.warp_core_energy >= needed_energy:
                            self.ship.power_allocation['shields'] = lower_level
                            if needed_energy > 0:
                                self.ship.consume_energy(needed_energy)
                            break
                    else:
                        # Can't sustain any shield power
                        self.ship.power_allocation['shields'] = 0
                        print("Shields powered down - insufficient energy.")
                        return False
        
        # Handle shield regeneration if not at full integrity
        if self.current_integrity < 100:
            self.regenerate_integrity(delta_time_seconds, energy_cost=False)
        
        return True

    def absorb_damage(self, incoming_damage: int) -> int:
        """
        PRD: Absorbs incoming damage based on power level and integrity.
        Each shield level absorbs 10 units of damage per attack, scaled by integrity.
        Returns remaining damage after absorption.
        """
        power_level = self.current_power_level
        
        # No absorption if shields are powered down or no integrity
        if power_level == 0 or self.current_integrity <= 0:
            print(f"Shields offline - no protection. Full damage: {incoming_damage}")
            return incoming_damage
        
        # Calculate base absorption capacity from power level
        base_absorption = power_level * self.absorption_per_level
        
        # Scale absorption by integrity (damaged shields are less effective)
        integrity_factor = self.current_integrity / 100.0
        effective_absorption = int(base_absorption * integrity_factor)
        
        # Absorb damage up to capacity
        absorbed = min(effective_absorption, incoming_damage)
        
        # Reduce shield integrity based on damage absorbed (shields take wear from use)
        if absorbed > 0:
            # Each point of damage absorbed reduces integrity slightly
            integrity_loss = absorbed * 0.5  # 50% of absorbed damage becomes integrity loss
            self.current_integrity = max(0, self.current_integrity - integrity_loss)
            
            # Update ship's system integrity display
            if hasattr(self.ship, 'system_integrity'):
                self.ship.system_integrity['shields'] = max(0, self.current_integrity)
        
        # Enhanced logging with more detail
        if absorbed > 0:
            print(f"Shields (level {power_level}) absorbed {absorbed}/{incoming_damage} damage. Integrity: {self.current_integrity:.1f}")
        else:
            print(f"Shields overwhelmed! Level {power_level} could not absorb {incoming_damage} damage.")
            
        return incoming_damage - absorbed

    def regenerate_integrity(self, delta_time: float, energy_cost: bool = True) -> bool:
        """
        PRD: Regenerates shield integrity based on elapsed time.
        PRD: 10 units/minute real-time while idle or activated by player.
        """
        if self.current_integrity >= 100:
            return True  # Already at full integrity
            
        # PRD: 10 units per minute = 10/60 units per second
        regen_rate_per_second = constants.SHIELD_REGEN_RATE_PER_MINUTE / 60.0
        regen_amount = regen_rate_per_second * delta_time
        
        # Optional: Consume energy for regeneration
        if energy_cost:
            energy_needed = int(regen_amount * 2)  # 2 energy per integrity point
            if not self.ship.consume_energy(energy_needed):
                return False  # Not enough energy
        
        self.current_integrity = min(100, self.current_integrity + regen_amount)
        print(f"Shield integrity regenerated by {regen_amount:.1f}. Current: {self.current_integrity:.1f}")
        return True

    def set_power_off(self):
        """
        Sets shield power to 0 (deactivated).
        """
        if hasattr(self.ship, 'power_allocation'):
            self.ship.power_allocation['shields'] = 0
        print("Shields powered down.")
        
    def is_operational(self) -> bool:
        """
        Returns True if shields have integrity > 0.
        """
        return self.current_integrity > 0 