from data import constants
from ship.base_ship import BaseShip


class Sensor:
    def __init__(self, long_range: int, short_range: int, ship: BaseShip):
        self.long_range = long_range
        self.short_range = short_range
        self.ship = ship
        self.scan_energy_cost = constants.SENSOR_ENERGY_COST_PER_SCAN

    def _perform_scan(self, scan_type: str, scan_range: int) -> list:
        if not self.ship.consume_energy(self.scan_energy_cost):
            print(f"Insufficient energy on {self.ship.name} to perform {scan_type} scan.")
            return []

        print(f"{self.ship.name} performing {scan_type} scan up to {scan_range} units. Energy remaining: {self.ship.warp_core_energy}")
        # Placeholder for actual detection logic. Returns dummy data for now.
        detected_objects = [
            {"type": "Klingon", "position": (10, 15), "distance": 120},
            {"type": "Starbase", "position": (50, 70), "distance": 600},
            {"type": "Anomaly", "position": (30, 45), "distance": 300}
        ]
        # Filter objects based on scan_range for demonstration
        filtered_objects = [obj for obj in detected_objects if obj["distance"] <= scan_range]
        return filtered_objects

    def long_range_scan(self) -> list:
        """
        Performs a long-range scan, suitable for galaxy map exploration.
        """
        return self._perform_scan("long-range", self.long_range)

    def short_range_scan(self) -> list:
        """
        Performs a short-range scan, suitable for local sector tactical awareness.
        """
        return self._perform_scan("short-range", self.short_range) 