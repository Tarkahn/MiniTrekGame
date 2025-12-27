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
        
        # Torpedo system
        self.torpedo_count = constants.STARTING_TORPEDO_COUNT
        self.max_torpedo_capacity = constants.MAX_TORPEDO_CAPACITY
        
        # PRD: Power allocation system (0-9 scale for each system)
        self.power_allocation = {
            'phasers': constants.DEFAULT_PHASER_POWER,
            'shields': constants.DEFAULT_SHIELD_POWER,      
            'engines': constants.DEFAULT_ENGINE_POWER  # Renamed from impulse for dual role
        }
        
        # Life support is always at maximum - no power allocation needed
        self.life_support_power = constants.DEFAULT_LIFE_SUPPORT_POWER
        
        # PRD: System integrity (0-100 scale)
        self.system_integrity = {
            'hull': hull_strength,
            'shields': 100,
            'phasers': 100,
            'engines': 100,  # Renamed from impulse for dual role
            'warp_core': 100
        }
        
        # Ship state tracking
        self.ship_state = "operational"  # operational, hull_breach, warp_core_breach, destroyed
        self.hull_breach_start_time = None
        self.warp_core_breach_countdown = 0

    def apply_damage(self, raw_damage: int, attacker_ship=None):
        """
        PRD: Applies damage to the ship, prioritizing shields then hull.
        Implements critical hit system when shields are down.
        """
        import random
        
        # Debug output for testing
        print(f"[DAMAGE DEBUG] {self.name} taking {raw_damage} damage")
        print(f"[DAMAGE DEBUG] Hull before: {self.hull_strength}/{self.max_hull_strength}")
        shield_level = getattr(self.shield_system, 'current_power_level', 0)
        shield_integrity = getattr(self.shield_system, 'current_integrity', 0)
        print(f"[DAMAGE DEBUG] Shield level: {shield_level}, integrity: {shield_integrity}%")
        
        # Check if shields are operational and powered
        shields_active = (hasattr(self.shield_system, 'current_power_level') and 
                         self.shield_system.current_power_level > 0 and
                         self.shield_system.is_operational())
        
        remaining_damage = self.shield_system.absorb_damage(raw_damage)
        
        # Debug output after shield absorption
        shield_level_after = getattr(self.shield_system, 'current_power_level', 0)
        print(f"[DAMAGE DEBUG] Shield level after absorption: {shield_level_after}")
        print(f"[DAMAGE DEBUG] Remaining damage to hull: {remaining_damage}")
        
        # PRD: Critical hits when shields are down (10% chance)
        if remaining_damage > 0 and not shields_active:
            crit_chance = constants.CRITICAL_HIT_CHANCE_SHIELDS_DOWN
            if random.random() < crit_chance:
                # Critical hit damages random system
                self._apply_critical_damage()
                print("CRITICAL HIT! System damaged!")

        # Apply any remaining damage to hull
        if remaining_damage > 0:
            old_hull = self.hull_strength
            self.hull_strength -= remaining_damage
            self.hull_strength = max(0, self.hull_strength)  # Ensure hull doesn't go below 0

            # Sync system_integrity['hull'] with hull_strength for repair system
            self.system_integrity['hull'] = self.hull_strength
            
            # Check for hull breach (hull reaches zero)
            if old_hull > 0 and self.hull_strength <= 0:
                print(f"CRITICAL: {self.name} hull breach detected! All systems failing!")
                self._handle_hull_breach()
            elif self.hull_strength > 0:
                # Hull damage can now penetrate to systems based on hull integrity
                hull_penetration_damage = self._calculate_hull_penetration_damage(remaining_damage)
                if hull_penetration_damage > 0:
                    self._apply_hull_penetration_damage(hull_penetration_damage)
                
                # Normal hull damage causes cascading system damage
                self._apply_cascading_system_damage(remaining_damage)
        
    def _apply_critical_damage(self):
        """
        PRD: Critical hits disable random systems until repaired at starbase.
        """
        import random
        
        # Select a random system that isn't already disabled
        available_systems = [sys for sys, integrity in self.system_integrity.items() 
                           if integrity > 0 and sys not in ['hull']]
        
        if available_systems:
            damaged_system = random.choice(available_systems)
            self.system_integrity[damaged_system] = 0  # PRD: Disabled until repaired
            print(f"Critical hit damaged {damaged_system} system!")

    def _apply_cascading_system_damage(self, hull_damage: float):
        """
        Hull damage causes cascading damage to ship systems.
        Larger hull damage has higher chance of damaging multiple systems.
        """
        import random

        # Ensure hull_damage is an integer for range() calculations
        hull_damage = int(hull_damage)

        # Base chance of system damage per hull damage point
        base_damage_chance = 0.15  # 15% chance per damage point
        max_systems_damaged = min(3, hull_damage // 10)  # Up to 3 systems, more likely with heavy damage
        
        # Calculate how many systems get damaged
        systems_to_damage = 0
        for _ in range(max_systems_damaged):
            if random.random() < (hull_damage * base_damage_chance / 100):
                systems_to_damage += 1
        
        if systems_to_damage == 0:
            return  # No system damage this time
        
        # Select systems to damage (excluding hull itself)
        available_systems = [sys for sys in self.system_integrity.keys() if sys != 'hull']
        damaged_systems = random.sample(available_systems, min(systems_to_damage, len(available_systems)))
        
        for system in damaged_systems:
            # Damage amount: 5-20% of current integrity, scaled by hull damage
            damage_percent = random.uniform(0.05, 0.20) * (hull_damage / 50)  # Scale with hull damage
            damage_amount = damage_percent * self.system_integrity[system]
            
            old_integrity = self.system_integrity[system]
            self.system_integrity[system] = max(0, self.system_integrity[system] - damage_amount)
            
            print(f"Hull breach damaged {system}: {old_integrity:.0f} -> {self.system_integrity[system]:.0f}")

    def _calculate_hull_penetration_damage(self, incoming_damage: float) -> int:
        """
        Calculate damage that penetrates through weakened hull to damage systems directly.
        Similar to how damaged shields become less effective, damaged hull provides less protection.
        
        Args:
            incoming_damage: The damage amount hitting the hull
            
        Returns:
            Amount of damage that penetrates to systems
        """
        # Calculate hull integrity as percentage
        hull_integrity_percent = self.hull_strength / self.max_hull_strength
        
        # Hull protection effectiveness decreases as hull gets damaged
        # At 100% hull: 95% protection (5% penetration)
        # At 50% hull: 75% protection (25% penetration) 
        # At 25% hull: 50% protection (50% penetration)
        # At 10% hull: 25% protection (75% penetration)
        
        # Base protection when hull is at 100%
        base_protection = 0.95  # 95% protection at full hull
        
        # Protection factor decreases as hull integrity drops
        protection_factor = base_protection * hull_integrity_percent
        
        # Calculate penetration percentage (inverse of protection)
        penetration_percent = 1.0 - protection_factor
        
        # Calculate actual penetrating damage
        penetration_damage = int(incoming_damage * penetration_percent)
        
        if penetration_damage > 0:
            hull_percent = int(hull_integrity_percent * 100)
            print(f"Hull integrity at {hull_percent}% - {penetration_damage} damage penetrating to systems")
        
        return penetration_damage

    def _apply_hull_penetration_damage(self, penetration_damage: float):
        """
        Apply damage that has penetrated through weakened hull directly to ship systems.
        This represents how a damaged hull fails to protect internal systems.

        Args:
            penetration_damage: Amount of damage penetrating to systems
        """
        import random

        # Ensure penetration_damage is an integer for calculations
        penetration_damage = int(penetration_damage)

        # Determine how many systems get hit (1-3 systems based on damage amount)
        max_systems_hit = min(3, max(1, penetration_damage // 15))  # 1 system per 15 damage
        systems_hit = random.randint(1, max_systems_hit)
        
        # Select systems to damage (excluding hull, which already took damage)
        available_systems = [sys for sys in self.system_integrity.keys() 
                           if sys != 'hull' and self.system_integrity[sys] > 0]
        
        if not available_systems:
            return  # No systems to damage
        
        # Randomly select systems to hit
        systems_to_damage = random.sample(available_systems, min(systems_hit, len(available_systems)))
        
        # Distribute damage among selected systems
        damage_per_system = penetration_damage // len(systems_to_damage)
        
        for system in systems_to_damage:
            # Apply direct damage to system integrity
            old_integrity = self.system_integrity[system]
            direct_damage = random.randint(damage_per_system // 2, damage_per_system * 2)  # Add randomness
            
            self.system_integrity[system] = max(0, self.system_integrity[system] - direct_damage)
            
            if old_integrity > 0 and self.system_integrity[system] <= 0:
                print(f"SYSTEM FAILURE: {system} destroyed by hull penetration!")
            else:
                print(f"Hull penetration damaged {system}: {old_integrity:.0f} -> {self.system_integrity[system]:.0f}")

    def _handle_hull_breach(self):
        """
        Handle catastrophic hull breach - all systems take massive damage.
        Ship enters critical state where systems continue failing until warp core breach.
        """
        import time
        
        self.ship_state = "hull_breach"
        self.hull_breach_start_time = time.time()
        
        print(f"*** HULL BREACH CRITICAL ALERT on {self.name} ***")
        print("All systems taking massive damage! Warp core destabilizing!")
        
        # Massive damage to all systems (30-60% immediate damage)
        for system in self.system_integrity.keys():
            if system != 'hull':  # Hull is already at zero
                import random
                damage_percent = random.uniform(0.30, 0.60)  # 30-60% damage
                damage_amount = damage_percent * self.system_integrity[system]
                
                old_integrity = self.system_integrity[system]
                self.system_integrity[system] = max(0, self.system_integrity[system] - damage_amount)
                
                print(f"CRITICAL SYSTEM FAILURE: {system} {old_integrity:.0f} -> {self.system_integrity[system]:.0f}")
        
        # Set warp core breach countdown if warp core is still functional
        if self.system_integrity['warp_core'] > 0:
            self.warp_core_breach_countdown = 10.0  # 10 seconds until core breach
            print(f"WARP CORE BREACH IMMINENT: {self.warp_core_breach_countdown:.0f} seconds until explosion!")

    def update_critical_state(self, delta_time_seconds: float):
        """
        Update ship critical state - handle ongoing system failures and warp core breach countdown.
        Should be called every frame when ship is in critical state.
        """
        if self.ship_state == "hull_breach":
            # Continue damaging all systems every second
            import time
            import random
            
            current_time = time.time()
            time_since_breach = current_time - self.hull_breach_start_time
            
            # Damage systems over time (every 0.5 seconds)
            if hasattr(self, '_last_critical_damage_time'):
                if current_time - self._last_critical_damage_time >= 0.5:
                    self._apply_critical_system_damage()
                    self._last_critical_damage_time = current_time
            else:
                self._last_critical_damage_time = current_time
            
            # Countdown to warp core breach
            if self.warp_core_breach_countdown > 0:
                self.warp_core_breach_countdown -= delta_time_seconds
                
                # Warning messages at key intervals
                if self.warp_core_breach_countdown <= 5 and int(self.warp_core_breach_countdown) % 1 == 0:
                    print(f"WARP CORE BREACH IN {int(self.warp_core_breach_countdown)} SECONDS!")
                
                # Warp core breach occurs
                if self.warp_core_breach_countdown <= 0:
                    self._trigger_warp_core_breach()
        
        elif self.ship_state == "warp_core_breach":
            # Ship is exploding - handle explosion effects
            pass  # Will implement explosion effects later

    def _apply_critical_system_damage(self):
        """Apply ongoing damage to all systems during hull breach state."""
        import random
        
        for system in self.system_integrity.keys():
            if system != 'hull' and self.system_integrity[system] > 0:
                # 5-15% damage per interval
                damage_percent = random.uniform(0.05, 0.15)
                damage_amount = damage_percent * self.system_integrity[system]
                
                old_integrity = self.system_integrity[system]
                self.system_integrity[system] = max(0, self.system_integrity[system] - damage_amount)
                
                if old_integrity > 0 and self.system_integrity[system] <= 0:
                    print(f"SYSTEM OFFLINE: {system} has failed completely!")

    def _trigger_warp_core_breach(self):
        """Trigger warp core breach and ship explosion."""
        self.ship_state = "warp_core_breach"
        self.system_integrity['warp_core'] = 0
        self.warp_core_energy = 0
        
        print(f"*** WARP CORE BREACH! {self.name} IS EXPLODING! ***")
        
        # Set all systems to zero
        for system in self.system_integrity.keys():
            self.system_integrity[system] = 0
        
        # Mark ship as destroyed
        self.ship_state = "destroyed"
        
        # TODO: Trigger explosion visual/audio effects
        return True  # Signal that explosion occurred

    def reset_damage(self):
        """
        PRD: Resets hull and shield integrity to their maximum values.
        Repairs all disabled systems. Typically called when docking at a starbase.
        """
        self.hull_strength = self.max_hull_strength
        self.shield_system.current_integrity = 100  # Reset shield integrity to full
        self.power_allocation['shields'] = 0  # Shields start powered down
        
        # PRD: Repair all systems to full integrity
        for system in self.system_integrity:
            if system == 'hull':
                self.system_integrity[system] = self.max_hull_strength
            else:
                self.system_integrity[system] = 100
        
        # Replenish torpedoes during starbase repairs
        self.replenish_torpedoes()
        
        # Reset ship critical state
        self.ship_state = "operational"
        self.hull_breach_start_time = None
        self.warp_core_breach_countdown = 0
        
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
        return self.ship_state not in ["warp_core_breach", "destroyed"] and self.hull_strength > 0 
    
    def consume_torpedo(self) -> bool:
        """
        Consumes one torpedo if available.
        Returns True if torpedo was consumed, False if no torpedoes available.
        """
        if self.torpedo_count > 0:
            self.torpedo_count -= 1
            return True
        return False
    
    def replenish_torpedoes(self):
        """
        Restores torpedo count to maximum capacity.
        Typically called when docking at a starbase.
        """
        self.torpedo_count = self.max_torpedo_capacity
        print(f"{self.name} torpedoes replenished to {self.torpedo_count}")
    
    def has_torpedoes(self) -> bool:
        """
        Returns True if ship has torpedoes available.
        """
        return self.torpedo_count > 0
    
    def get_movement_duration(self, base_duration_ms: int) -> int:
        """
        Calculate movement duration based on engine power and system integrity.
        
        Args:
            base_duration_ms: Base movement duration in milliseconds
            
        Returns:
            Actual movement duration in milliseconds based on engine power
        """
        engine_power = self.power_allocation.get('engines', 5)
        engine_integrity = self.system_integrity.get('engines', 100) / 100.0
        
        # Speed multipliers based on engine power (0-9 scale)
        speed_multipliers = {
            0: 0.25,  # Emergency: 4x slower (8 seconds from 2 second base)
            1: 0.4,   # Very slow: 2.5x slower (5 seconds)
            2: 0.5,   # Slow: 2x slower (4 seconds)  
            3: 0.7,   # Below normal: 1.4x slower (2.8 seconds)
            4: 0.85,  # Slightly slow: 1.2x slower (2.4 seconds)
            5: 1.0,   # Normal: Standard speed (2 seconds)
            6: 1.2,   # Fast: 1.2x faster (1.7 seconds)
            7: 1.4,   # Very fast: 1.4x faster (1.4 seconds)
            8: 1.7,   # Maximum: 1.7x faster (1.2 seconds)
            9: 2.0    # Overdrive: 2x faster (1 second)
        }
        
        speed_multiplier = speed_multipliers.get(engine_power, 1.0)
        # Apply engine damage to reduce effective speed
        effective_multiplier = speed_multiplier * engine_integrity
        
        # Ensure minimum speed (never completely immobilized)
        effective_multiplier = max(effective_multiplier, 0.1)
        
        duration = int(base_duration_ms / effective_multiplier)
        print(f"[MOVEMENT] Engine power: {engine_power}, integrity: {engine_integrity:.1f}, duration: {duration}ms")
        return duration
    
    def get_engine_efficiency(self) -> float:
        """
        Get current engine efficiency as a percentage.
        
        Returns:
            Engine efficiency from 0.0 to 1.0+
        """
        engine_power = self.power_allocation.get('engines', 5)
        engine_integrity = self.system_integrity.get('engines', 100) / 100.0
        
        # Base efficiency from power level (0-9 scale maps to 0.25-2.0 multiplier)
        if engine_power == 0:
            base_efficiency = 0.25
        else:
            # Linear scaling from 0.4 to 2.0 for power levels 1-9
            base_efficiency = 0.4 + (engine_power - 1) * (2.0 - 0.4) / 8
        
        return base_efficiency * engine_integrity
    
    def get_movement_energy_cost(self, base_cost: int) -> int:
        """
        Calculate energy cost for movement based on engine power usage.
        
        Args:
            base_cost: Base energy cost for movement
            
        Returns:
            Actual energy cost based on engine power
        """
        engine_power = self.power_allocation.get('engines', 5)
        
        # Higher engine power = more energy consumption
        # Power 0-3: Reduced energy usage (efficient low power)
        # Power 4-6: Standard energy usage
        # Power 7-9: Increased energy usage (high performance cost)
        
        if engine_power <= 3:
            energy_multiplier = 0.7 + (engine_power * 0.1)  # 0.7x to 1.0x
        elif engine_power <= 6:
            energy_multiplier = 1.0 + ((engine_power - 4) * 0.1)  # 1.0x to 1.2x
        else:
            energy_multiplier = 1.2 + ((engine_power - 6) * 0.2)  # 1.2x to 1.8x
        
        cost = int(base_cost * energy_multiplier)
        print(f"[ENERGY] Engine power: {engine_power}, cost multiplier: {energy_multiplier:.1f}, total cost: {cost}")
        return cost
    
    def get_effective_max_energy(self) -> int:
        """
        Get effective maximum warp core energy based on warp core integrity.
        Damaged warp core reduces maximum energy capacity.
        """
        warp_core_integrity = self.system_integrity.get('warp_core', 100) / 100.0
        effective_max = int(self.max_warp_core_energy * warp_core_integrity)
        
        # Ensure current energy doesn't exceed new maximum
        if self.warp_core_energy > effective_max:
            self.warp_core_energy = effective_max
            
        return effective_max
    
    def get_phaser_damage_multiplier(self) -> float:
        """
        Get phaser damage multiplier based on phaser system integrity.
        Damaged phasers reduce weapon effectiveness.
        """
        phaser_integrity = self.system_integrity.get('phasers', 100) / 100.0
        return phaser_integrity
    
    def get_engine_damage_modifier(self) -> float:
        """
        Get engine damage modifier for movement calculations.
        Already implemented in existing engine efficiency methods, but kept for consistency.
        """
        return self.system_integrity.get('engines', 100) / 100.0