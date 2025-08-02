from data import constants
# Removed: from ship.ship_systems.shield import Shield # Circular import dependency


class BaseShip:
    """
    Base class for all ships in the Star Trek Tactical Game.
    Defines common attributes and basic functionalities for ship systems.
    """

    def __init__(self, name, shield_system, hull_strength, energy, max_energy, weapons, position):
        self.name = name
        self.shield_system = shield_system  # Accept pre-instantiated Shield object
        self.max_hull_strength = hull_strength  # Initialize max_hull_strength
        self.hull_strength = hull_strength
        self.warp_core_energy = energy
        self.max_warp_core_energy = max_energy
        self.weapons = weapons or []
        self.position = position
        
        # PRD: Power allocation system (0-9 scale for each system)
        self.power_allocation = {
            'phasers': constants.DEFAULT_PHASER_POWER,
            'shields': constants.DEFAULT_SHIELD_POWER,      
            'engines': constants.DEFAULT_ENGINE_POWER,  # Renamed from impulse for dual role
            'sensors': constants.DEFAULT_SENSOR_POWER
        }
        
        # Life support is always at maximum - no power allocation needed
        self.life_support_power = constants.DEFAULT_LIFE_SUPPORT_POWER
        
        # PRD: System integrity (0-100 scale)
        self.system_integrity = {
            'hull': hull_strength,
            'shields': 100,
            'phasers': 100,
            'engines': 100,  # Renamed from impulse for dual role
            'sensors': 100,
            'life_support': 100,
            'warp_core': 100
        }

    def apply_damage(self, raw_damage: int, attacker_ship=None):
        """
        PRD: Applies damage to the ship, prioritizing shields then hull.
        Implements critical hit system when shields are down.
        """
        import random
        
        # Check if shields are operational and powered
        shields_active = (hasattr(self.shield_system, 'current_power_level') and 
                         self.shield_system.current_power_level > 0 and
                         self.shield_system.is_operational())
        
        remaining_damage = self.shield_system.absorb_damage(raw_damage)
        
        # PRD: Critical hits when shields are down (10% chance)
        if remaining_damage > 0 and not shields_active:
            crit_chance = constants.CRITICAL_HIT_CHANCE_SHIELDS_DOWN
            if random.random() < crit_chance:
                # Critical hit damages random system
                self._apply_critical_damage()
                print("CRITICAL HIT! System damaged!")

        # Apply any remaining damage to hull
        self.hull_strength -= remaining_damage
        self.hull_strength = max(0, self.hull_strength)  # Ensure hull doesn't go below 0
        
    def _apply_critical_damage(self):
        """
        PRD: Critical hits disable random systems until repaired at starbase.
        """
        import random
        
        # Select a random system that isn't already disabled
        available_systems = [sys for sys, integrity in self.system_integrity.items() 
                           if integrity > 0 and sys not in ['hull', 'life_support']]
        
        if available_systems:
            damaged_system = random.choice(available_systems)
            self.system_integrity[damaged_system] = 0  # PRD: Disabled until repaired
            print(f"Critical hit damaged {damaged_system} system!")

    def reset_damage(self):
        """
        PRD: Resets hull and shield integrity to their maximum values.
        Repairs all disabled systems. Typically called when docking at a starbase.
        """
        self.hull_strength = self.max_hull_strength
        self.shield_system.current_integrity = 100  # Reset shield integrity to full
        self.shield_system.current_power_level = 0  # Shields start powered down
        
        # PRD: Repair all systems to full integrity
        for system in self.system_integrity:
            if system == 'hull':
                self.system_integrity[system] = self.max_hull_strength
            else:
                self.system_integrity[system] = 100
                
        print(f"{self.name} fully repaired at starbase.")

    def allocate_power(self, system: str, power_level: int) -> bool:
        """
        PRD: Allocates power to a specific ship system (0-9 scale).
        Returns True if successful, False if invalid.
        """
        if system not in self.power_allocation:
            print(f"Invalid system: {system}")
            return False
            
        if power_level < 0 or power_level > 9:
            print(f"Invalid power level: {power_level}. Must be 0-9.")
            return False
            
        # Check total power allocation doesn't exceed limits
        total_power = sum(self.power_allocation.values()) - self.power_allocation[system] + power_level
        max_total_power = constants.MAX_TOTAL_POWER  # Configurable limit for tactical choices
        
        if total_power > max_total_power:
            print(f"Total power allocation would exceed maximum ({max_total_power})")
            return False
            
        self.power_allocation[system] = power_level
        print(f"{system.capitalize()} power set to {power_level}")
        
        # Update shield power if shields were modified
        if system == 'shields' and hasattr(self, 'shield_system'):
            self.shield_system.set_power_level(power_level)
            
        return True

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