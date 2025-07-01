import unittest
from unittest.mock import patch
import time

from ship.player_ship import PlayerShip
from data import constants


class TestPlayerShip(unittest.TestCase):

    def setUp(self):
        """
        Set up a fresh PlayerShip instance before each test.
        """
        self.player_ship = PlayerShip()

    # Test cases for move_ship(destination)
    def test_move_ship_sufficient_energy(self):
        """
        Verify movement works and energy is deducted correctly with sufficient energy.
        """
        initial_energy = self.player_ship.warp_core_energy
        hex_count = 5
        expected_energy_deduction = hex_count * constants.WARP_ENERGY_COST
        
        success = self.player_ship.move_ship(hex_count)
        self.assertTrue(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - expected_energy_deduction)

    def test_move_ship_insufficient_energy(self):
        """
        Assert movement fails gracefully with no state change due to insufficient energy.
        """
        self.player_ship.warp_core_energy = 0  # Drain energy
        initial_energy = self.player_ship.warp_core_energy
        hex_count = 5

        success = self.player_ship.move_ship(hex_count)
        self.assertFalse(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)  # Energy should not change

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
        # First shot to activate cooldown
        self.player_ship.fire_phasers(target_distance=1, phaser_power_level=5)
        
        # Attempt to fire again before cooldown ends
        mock_time.return_value = 100.0 + constants.PHASER_COOLDOWN_SECONDS / 2  # Halfway through cooldown
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(target_distance=1, phaser_power_level=5)
        
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)  # Energy should not change

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_target_out_of_range(self, mock_time):
        """
        Ensure firing is not allowed when target is out of range.
        """
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(target_distance=10, phaser_power_level=5)
        
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)  # Energy should not change

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_insufficient_energy(self, mock_time):
        """
        Verify no firing occurs and appropriate state is set due to insufficient energy.
        """
        self.player_ship.warp_core_energy = 0  # Drain energy
        initial_energy = self.player_ship.warp_core_energy
        
        damage = self.player_ship.fire_phasers(target_distance=1, phaser_power_level=5)
        
        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)  # Energy should not change

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_success_case(self, mock_time):
        """
        Confirm correct damage is applied based on distance and power level.
        """
        initial_energy = self.player_ship.warp_core_energy
        phaser_power = 5
        target_dist = 3
        expected_damage = (phaser_power * 10) - (target_dist * 3)  # (5 * 10) - (3 * 3) = 50 - 9 = 41
        
        damage = self.player_ship.fire_phasers(target_distance=target_dist, phaser_power_level=phaser_power)
        
        self.assertEqual(damage, expected_damage)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - constants.PHASER_ENERGY_COST)
        self.assertAlmostEqual(self.player_ship.phaser_cooldown_end_time, time.time() + constants.PHASER_COOLDOWN_SECONDS, delta=0.1)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_edge_of_range(self, mock_time):
        """
        Validate that damage calculation still applies accurately at 9 hexes.
        """
        initial_energy = self.player_ship.warp_core_energy
        phaser_power = 5
        target_dist = 9
        expected_damage = (phaser_power * 10) - (target_dist * 3)  # (5 * 10) - (9 * 3) = 50 - 27 = 23
        
        damage = self.player_ship.fire_phasers(target_distance=target_dist, phaser_power_level=phaser_power)
        
        self.assertEqual(damage, expected_damage)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - constants.PHASER_ENERGY_COST)

    @patch('time.time', return_value=100.0)
    def test_fire_phasers_power_level_zero(self, mock_time):
        """
        Ensure phasers at power level 0 cannot fire.
        """
        initial_energy = self.player_ship.warp_core_energy
        damage = self.player_ship.fire_phasers(target_distance=1, phaser_power_level=0)

        self.assertEqual(damage, 0)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)


    # Test cases for initiate_warp(destination_sector)
    def test_initiate_warp_sufficient_energy(self):
        """
        Confirm ship transitions correctly and energy is reduced with sufficient energy.
        """
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 2
        initiation_cost = 20
        energy_per_sector = constants.WARP_ENERGY_COST  # 10
        expected_total_cost = initiation_cost + (sectors_to_travel * energy_per_sector)  # 20 + (2 * 10) = 40
        
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertTrue(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy - expected_total_cost)

    def test_initiate_warp_insufficient_energy(self):
        """
        Assert warp fails or is partially restricted due to insufficient energy.
        """
        self.player_ship.warp_core_energy = 10  # Set energy to be too low
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 2
        
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertFalse(success)
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)  # Energy should not change

    def test_initiate_warp_same_sector_selected(self):
        """
        Ensure warp doesn't proceed and gives proper feedback when same sector is selected.
        (This check would typically be in UI/game logic, but we can simulate a zero-cost warp here)
        """
        initial_energy = self.player_ship.warp_core_energy
        sectors_to_travel = 0  # Simulating selecting the current sector
        
        success = self.player_ship.initiate_warp(sectors_to_travel)
        self.assertTrue(success)  # Should succeed if cost is 0, no energy consumed
        self.assertEqual(self.player_ship.warp_core_energy, initial_energy)

    # Note: 'Consecutive warp attempts' testing would involve simulating game turns
    # and might be more appropriate for integration tests or the main game loop.
    # The initiate_warp method itself primarily handles energy consumption and returns success. 