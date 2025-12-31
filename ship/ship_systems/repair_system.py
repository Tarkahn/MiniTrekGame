"""
Ship Repair System - Handles active repairs to ship systems.

This module allows the player to actively repair damaged ship systems
at the same rate as shield regeneration (10 units/minute).
Repairs work on all systems simultaneously and can be used in or out of combat.
"""

from data import constants


class RepairSystem:
    """
    Manages active ship repairs for all systems.

    Repairs:
    - Hull integrity
    - Phasers
    - Engines
    - Warp core

    Note: Shield integrity is handled separately by the Shield class's
    automatic regeneration system.
    """

    def __init__(self, ship):
        """
        Initialize the repair system.

        Args:
            ship: The ship this repair system belongs to
        """
        self.ship = ship
        self.is_repairing = False
        self.repair_start_time = None

        # Use same rate as shield regeneration (10 units/minute)
        # This is defined in constants.SHIELD_REGEN_RATE_PER_MINUTE
        self.repair_rate_per_minute = getattr(constants, 'SHIELD_REGEN_RATE_PER_MINUTE', 10)
        self.repair_rate_per_second = self.repair_rate_per_minute / 60.0

        # Energy cost per repair point (same as shields)
        self.energy_cost_per_point = 2

        # Track last repair message to avoid spam
        self._last_repair_message_time = 0
        self._repair_message_interval = 1.0  # Show message every 1 second

    def start_repairs(self) -> bool:
        """
        Start the active repair process.

        Returns:
            True if repairs started, False if already repairing or ship is destroyed
        """
        import time

        # Can't repair a destroyed ship
        if self.ship.ship_state in ["warp_core_breach", "destroyed"]:
            print("Cannot repair - ship is destroyed!")
            return False

        # Can't repair during hull breach
        if self.ship.ship_state == "hull_breach":
            print("Cannot repair - critical hull breach! Evacuate or seal breaches first!")
            return False

        # Check if any systems need repair
        if not self._needs_repair():
            print("All systems are fully operational. No repairs needed.")
            return False

        if self.is_repairing:
            print("Repairs already in progress.")
            return False

        self.is_repairing = True
        self.repair_start_time = time.time()
        print("Repair crews dispatched. Beginning system repairs...")
        return True

    def stop_repairs(self):
        """Stop the active repair process."""
        if self.is_repairing:
            self.is_repairing = False
            self.repair_start_time = None
            print("Repair operations halted.")

    def toggle_repairs(self) -> bool:
        """
        Toggle repairs on/off.

        Returns:
            True if repairs are now active, False if stopped
        """
        if self.is_repairing:
            self.stop_repairs()
            return False
        else:
            return self.start_repairs()

    def update(self, delta_time_seconds: float) -> dict:
        """
        Update repair progress for all systems.

        Args:
            delta_time_seconds: Time elapsed since last update

        Returns:
            Dictionary of systems that were repaired and their new values
        """
        import time

        if not self.is_repairing:
            return {}

        # Stop repairs if ship is in critical state
        if self.ship.ship_state in ["hull_breach", "warp_core_breach", "destroyed"]:
            print("CRITICAL: Repairs halted - ship in critical state!")
            self.stop_repairs()
            return {}

        # Check if repairs are still needed
        if not self._needs_repair():
            print("All repairs complete! Systems restored to full operational status.")
            self.stop_repairs()
            return {}

        # Calculate repair amount for this time period
        repair_amount = self.repair_rate_per_second * delta_time_seconds

        # Calculate total energy cost for repairs
        # Cost scales with number of systems being repaired
        systems_needing_repair = self._get_systems_needing_repair()
        total_energy_cost = int(repair_amount * self.energy_cost_per_point * len(systems_needing_repair))

        # Check if we have enough energy
        if total_energy_cost > 0:
            if self.ship.warp_core_energy < total_energy_cost:
                # Not enough energy - reduce repair rate proportionally
                available_ratio = self.ship.warp_core_energy / total_energy_cost
                repair_amount *= available_ratio
                total_energy_cost = self.ship.warp_core_energy

                if total_energy_cost <= 0:
                    print("Insufficient energy for repairs. Halting repair operations.")
                    self.stop_repairs()
                    return {}

            # Consume energy for repairs
            self.ship.warp_core_energy -= total_energy_cost

        # Apply repairs to all damaged systems simultaneously
        repaired_systems = {}

        for system in systems_needing_repair:
            old_value = self.ship.system_integrity[system]

            if system == 'hull':
                # Hull repairs toward max_hull_strength
                max_value = self.ship.max_hull_strength
                new_value = min(max_value, old_value + repair_amount)
                self.ship.system_integrity['hull'] = new_value
                self.ship.hull_strength = new_value
            else:
                # Other systems repair toward 100
                new_value = min(100, old_value + repair_amount)
                self.ship.system_integrity[system] = new_value

            if new_value != old_value:
                repaired_systems[system] = new_value

        # Show repair progress periodically
        current_time = time.time()
        if current_time - self._last_repair_message_time >= self._repair_message_interval:
            self._show_repair_status()
            self._last_repair_message_time = current_time

        return repaired_systems

    def _needs_repair(self) -> bool:
        """Check if any systems need repair."""
        for system, integrity in self.ship.system_integrity.items():
            if system == 'hull':
                if integrity < self.ship.max_hull_strength:
                    return True
            elif system != 'shields':  # Shields handled by Shield class
                if integrity < 100:
                    return True
        return False

    def _get_systems_needing_repair(self) -> list:
        """Get list of systems that need repair."""
        systems = []
        for system, integrity in self.ship.system_integrity.items():
            if system == 'shields':
                continue  # Shields handled separately
            if system == 'hull':
                if integrity < self.ship.max_hull_strength:
                    systems.append(system)
            elif integrity < 100:
                systems.append(system)
        return systems

    def _show_repair_status(self):
        """Print current repair status."""
        systems = self._get_systems_needing_repair()
        if not systems:
            return

        status_parts = []
        for system in systems:
            integrity = self.ship.system_integrity[system]
            if system == 'hull':
                max_val = self.ship.max_hull_strength
                status_parts.append(f"{system.upper()}: {integrity:.0f}/{max_val}")
            else:
                status_parts.append(f"{system.upper()}: {integrity:.0f}%")

        print(f"Repair progress: {', '.join(status_parts)}")

    def get_repair_status(self) -> dict:
        """
        Get current repair status for UI display.

        Returns:
            Dictionary with repair status information
        """
        return {
            'is_repairing': self.is_repairing,
            'needs_repair': self._needs_repair(),
            'systems_needing_repair': self._get_systems_needing_repair(),
            'repair_rate': self.repair_rate_per_minute,
            'energy_cost': self.energy_cost_per_point
        }

    def get_repair_time_estimate(self) -> float:
        """
        Estimate time to complete all repairs in seconds.

        Returns:
            Estimated repair time in seconds, or 0 if no repairs needed
        """
        if not self._needs_repair():
            return 0.0

        max_repair_needed = 0

        for system, integrity in self.ship.system_integrity.items():
            if system == 'shields':
                continue
            if system == 'hull':
                repair_needed = self.ship.max_hull_strength - integrity
            else:
                repair_needed = 100 - integrity
            max_repair_needed = max(max_repair_needed, repair_needed)

        if self.repair_rate_per_second > 0:
            return max_repair_needed / self.repair_rate_per_second
        return 0.0
