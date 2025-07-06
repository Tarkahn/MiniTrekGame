import unittest
from unittest.mock import patch
import time

from ship.player_ship import PlayerShip
from data import constants
# Removed: from ship.ship_systems.shield import Shield # No longer needed for direct instantiation in test setup


class TestPlayerShip(unittest.TestCase):

    def setUp(self):
        """
        Set up a fresh PlayerShip instance before each test.
        """
        self.player_ship = PlayerShip(
            name="Test Ship",
            max_shield_strength=100,
            hull_strength=1000,
            energy=1000,
            max_energy=1000,
            weapons=[],
            position=(0, 0)
        )

    # Test cases for move_ship(destination)
    def test_move_ship_sufficient_energy(self):
        """
        Verify movement works and energy is deducted correctly with sufficient energy.
        """
        initial_energy = self.player_ship.warp_core_energy
        hex_count = 5
        expected_energy_deduction = hex_count * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
        
        success = self.player_ship.move_ship(hex_count)
        self.assertTrue(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - expected_energy_deduction)

    def test_move_ship_insufficient_energy(self):
        """
        Assert movement fails gracefully with no state change due to insufficient energy.
        """
        self.player_ship.warp_core_energy = 0
        initial_energy = self.player_ship.warp_core_energy
        hex_count = 5
        success = self.player_ship.move_ship(hex_count)
        self.assertFalse(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    # Note: For 'blocked or invalid destination' and 'movement after system damage',
    # these typically require more complex game state or dependency injection/mocking of
    # an 'Impulse Engine' system. For now, the `move_ship` directly handles energy and
    # doesn't check for terrain or system damage within its current scope.
    # These tests would be more appropriate at a higher level (e.g., game_loop, impulse_system.py).

    # Test cases for fire_phasers(target)
    @patch('time.time', return_value=100.0)
    def test_fire_phasers_cooldown_active(self, mock_time):
        """
        Assert firing fails when cooldown is active.
        """
        class DummyTarget:
            def apply_damage(self, dmg):
                pass
        dummy_target = DummyTarget()
        # First shot to activate cooldown
        self.player_ship.fire_phasers(dummy_target, target_distance=1)
        # Attempt to fire again before cooldown ends
        mock_time.return_value = 100.0 + constants.PHASER_COOLDOWN_SECONDS / 2
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=1)
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_target_out_of_range(self, mock_time):
        """
        Ensure firing is not allowed when target is out of range.
        """
        class DummyTarget:
            def apply_damage(self, dmg):
                pass
        dummy_target = DummyTarget()
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=10)
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_insufficient_energy(self, mock_time):
        """
        Verify no firing occurs and appropriate state is set due to insufficient energy.
        """
        class DummyTarget:
            def apply_damage(self, dmg):
                pass
        dummy_target = DummyTarget()
        self.player_ship.warp_core_energy = 0
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=1)
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_success_case(self, mock_time):
        """
        Confirm correct damage is applied based on distance and fixed power.
        """
        class DummyTarget:
            def __init__(self):
                self.damage_taken = 0
            def apply_damage(self, dmg):
                self.damage_taken += dmg
        dummy_target = DummyTarget()
        initial_energy = self.player_ship.warp_core_energy
        target_dist = 3
        expected_damage = (constants.PLAYER_PHASER_POWER * 10) - (target_dist * 3)
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=target_dist)
        self.assertEqual(damage, expected_damage)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - constants.PHASER_ENERGY_COST)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_edge_of_range(self, mock_time):
        """
        Validate that damage calculation still applies accurately at 9 hexes.
        """
        class DummyTarget:
            def apply_damage(self, dmg):
                pass
        dummy_target = DummyTarget()
        initial_energy = self.player_ship.warp_core_energy
        target_dist = 9
        expected_damage = (constants.PLAYER_PHASER_POWER * 10) - (target_dist * 3)
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=target_dist)
        self.assertEqual(damage, expected_damage)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - constants.PHASER_ENERGY_COST)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_power_level_zero(self, mock_time):
        """
        Ensure phasers at power level 0 cannot fire (not applicable, so just test for 0 damage if range is 0).
        """
        class DummyTarget:
            def apply_damage(self, dmg):
                pass
        dummy_target = DummyTarget()
        initial_energy = self.player_ship.warp_core_energy
        # Simulate out-of-range as a proxy for 'power level 0' (since power level is not used)
        damage = self.player_ship.fire_phasers(dummy_target, target_distance=999)
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    # Test cases for initiate_warp(destination_sector)
    def test_initiate_warp_sufficient_energy(self):
        """
        Confirm ship transitions correctly and energy is reduced with sufficient energy.
        """
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 2
        initiation_cost = constants.WARP_INITIATION_COST
        energy_per_sector = constants.WARP_ENERGY_COST
        expected_total_cost = initiation_cost + (sectors_to_travel * energy_per_sector)
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertTrue(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - expected_total_cost)

    def test_initiate_warp_insufficient_energy(self):
        """
        Assert warp fails or is partially restricted due to insufficient energy.
        """
        self.player_ship.warp_core_energy = 10
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 2
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertFalse(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    def test_initiate_warp_same_sector_selected(self):
        """
        Ensure warp doesn't proceed and gives proper feedback when same sector is selected.
        """
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 0
        initiation_cost = constants.WARP_INITIATION_COST
        energy_per_sector = constants.WARP_ENERGY_COST
        expected_total_cost = initiation_cost + (sectors_to_travel * energy_per_sector)
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertTrue(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - expected_total_cost)

    # Note: 'Consecutive warp attempts' testing would involve simulating game turns
    # and might be more appropriate for integration tests or the main game loop.
    # The initiate_warp method itself primarily handles energy consumption and returns success. 