"""
Event handling for the Star Trek Tactical Game.

This module handles all user input events including button clicks,
mouse clicks for navigation and targeting, and keyboard input.
"""
import pygame
import math
import time
import random
import logging

from debug_logger import log_debug
from data import constants
from galaxy_generation.map_object import MapObject
from galaxy_generation.object_placement import generate_system_objects
from ui.hex_utils import get_star_hexes, get_planet_hexes
from ui.dialogs import show_orbit_dialog


class EventContext:
    """
    Context object containing all state needed for event handling.
    This allows the event handler to access and modify game state
    without relying on module-level globals.
    """
    def __init__(self):
        # Core game state
        self.game_state = None
        self.player_ship = None
        self.systems = None
        self.current_system = None
        self.hex_grid = None
        self.screen = None
        self.font = None

        # UI elements
        self.button_rects = None
        self.toggle_btn_rect = None
        self.button_labels = None
        self.map_rect = None
        self.ship_status_display = None
        self.enemy_scan_panel = None

        # Sound
        self.sound_manager = None

        # Galaxy data
        self.star_coords = None
        self.lazy_object_coords = None
        self.planet_orbits = None
        self.planet_anim_state = None

        # Animation state (sector)
        self.ship_q = 0
        self.ship_r = 0
        self.trajectory_start_x = None
        self.trajectory_start_y = None

        # Animation state (system)
        self.system_ship_anim_x = None
        self.system_ship_anim_y = None
        self.system_dest_q = None
        self.system_dest_r = None
        self.system_ship_moving = False
        self.system_move_start_time = None
        self.system_move_duration_ms = 1000
        self.system_trajectory_start_x = None
        self.system_trajectory_start_y = None

        # Pending orbital state
        self.pending_orbit_center = None
        self.pending_orbit_key = None
        self.player_orbit_key = None

        # Phaser range
        self.phaser_range = 10

        # Callbacks
        self.add_event_log = None
        self.create_enemy_popup = None
        self.perform_enemy_scan = None
        self.perform_planet_scan = None
        self.perform_star_scan = None
        self.get_enemy_id = None
        self.get_enemy_current_position = None
        self.is_hex_blocked = None


class EventResult:
    """Result object returned from event handling."""
    def __init__(self):
        self.running = True
        self.ship_q = None
        self.ship_r = None
        self.current_system = None

        # Updated animation state
        self.trajectory_start_x = None
        self.trajectory_start_y = None
        self.system_ship_anim_x = None
        self.system_ship_anim_y = None
        self.system_dest_q = None
        self.system_dest_r = None
        self.system_ship_moving = None
        self.system_move_start_time = None
        self.system_move_duration_ms = None
        self.system_trajectory_start_x = None
        self.system_trajectory_start_y = None

        # Orbit state
        self.pending_orbit_center = None
        self.pending_orbit_key = None
        self.player_orbit_key = None


def handle_button_click(label: str, ctx: EventContext) -> bool:
    """
    Handle a button click based on the button label.
    Returns True if the event was handled and should not propagate.
    """
    if label == "Move":
        ctx.add_event_log("Move mode: Click on a hex to navigate")
        return True

    elif label == "Torpedo":
        return _handle_torpedo_button(ctx)

    elif label == "Fire":
        return _handle_fire_button(ctx)

    elif label == "Scan":
        return _handle_scan_button(ctx)

    elif label == "Repairs":
        return _handle_repairs_button(ctx)

    return False


def _handle_torpedo_button(ctx: EventContext) -> bool:
    """Handle torpedo button click - fires at torpedo target hex if set."""
    player_ship = ctx.player_ship
    game_state = ctx.game_state
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log

    # Check if ship is capable of firing weapons
    if not player_ship.is_alive():
        add_event_log("Ship is destroyed - weapons offline!")
        sound_manager.play_sound('error')
        return True

    if hasattr(player_ship, 'ship_state') and player_ship.ship_state != "operational":
        add_event_log("Ship systems critical - weapons disabled!")
        sound_manager.play_sound('error')
        return True

    # Check if weapon systems are functional
    phaser_integrity = player_ship.system_integrity.get('phasers', 100)
    if phaser_integrity <= 0:
        add_event_log("Weapon systems offline - cannot fire!")
        sound_manager.play_sound('error')
        return True

    # Check torpedo availability first
    if not player_ship.has_torpedoes():
        add_event_log("*** NO TORPEDOES REMAINING ***")
        add_event_log("Dock at a starbase to replenish torpedo supplies!")
        sound_manager.play_sound('error')
        return True

    # Check if torpedoes are on cooldown
    if player_ship.torpedo_system.is_on_cooldown():
        cooldown_time = (player_ship.torpedo_system._last_fired_time +
                        player_ship.torpedo_system.cooldown_seconds) - time.time()
        add_event_log(f"Torpedoes reloading - {cooldown_time:.1f}s remaining")
        sound_manager.play_sound('error')
        return True

    # Only works in system mode
    if game_state.map_mode != 'system':
        add_event_log("Torpedoes can only be fired in system view")
        return True

    # Fire at torpedo target hex if set
    torpedo_target = game_state.get_torpedo_target_hex()
    if torpedo_target is not None:
        return _fire_torpedo_at_hex(ctx, torpedo_target[0], torpedo_target[1])

    # No target set - inform player
    add_event_log("No torpedo target! Right-click any hex to set target.")
    sound_manager.play_sound('error')
    return True


def _fire_torpedo_at_hex(ctx: EventContext, target_q: int, target_r: int) -> bool:
    """Fire a torpedo at a specific hex location."""
    player_ship = ctx.player_ship
    game_state = ctx.game_state
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log

    player_obj = next((obj for obj in ctx.systems.get(ctx.current_system, [])
                      if obj.type == 'player'), None)

    if player_obj is None:
        add_event_log("Cannot determine player position")
        return True

    # Calculate distance to target hex
    dx = target_q - player_obj.system_q
    dy = target_r - player_obj.system_r
    distance = math.hypot(dx, dy)

    # Check range
    from data import constants
    if distance > constants.TORPEDO_RANGE:
        add_event_log(f"Target out of torpedo range ({distance:.1f} > {constants.TORPEDO_RANGE})")
        sound_manager.play_sound('error')
        return True

    # Get start position for animation
    if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
        start_pos = (ctx.system_ship_anim_x, ctx.system_ship_anim_y)
    else:
        start_pos = ctx.hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)

    # Get target position (center of target hex)
    target_pos = ctx.hex_grid.get_hex_center(target_q, target_r)

    # Check if there's an enemy at the target hex for direct hit tracking
    target_enemy = None
    for obj in ctx.systems.get(ctx.current_system, []):
        if obj.type == 'enemy' and obj.system_q == target_q and obj.system_r == target_r:
            target_enemy = obj
            break

    # Fire torpedo using weapon animation manager
    # Note: target_enemy can be None - torpedo will still explode at target location
    result = game_state.weapon_animation_manager.fire_torpedo(
        target_enemy, distance, start_pos, target_pos, (target_q, target_r)
    )

    if result['success']:
        if target_enemy:
            add_event_log(f"Torpedo launched at enemy position ({target_q}, {target_r})!")
        else:
            add_event_log(f"Torpedo launched at hex ({target_q}, {target_r})!")

        if player_ship.torpedo_count <= 3 and player_ship.torpedo_count > 0:
            add_event_log(f"*** LOW TORPEDO SUPPLY: {player_ship.torpedo_count} remaining ***")
        elif player_ship.torpedo_count == 0:
            add_event_log("*** LAST TORPEDO EXPENDED ***")

        # Clear the torpedo target after firing
        game_state.clear_torpedo_target()
    else:
        add_event_log(f"Torpedo launch failed: {result.get('reason', 'Unknown error')}")

    return True


def _handle_fire_button(ctx: EventContext) -> bool:
    """Handle fire (phaser) button click."""
    player_ship = ctx.player_ship
    game_state = ctx.game_state
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log

    # Check if ship is capable of firing weapons
    if not player_ship.is_alive():
        add_event_log("Ship is destroyed - weapons offline!")
        sound_manager.play_sound('error')
        return True

    if hasattr(player_ship, 'ship_state') and player_ship.ship_state != "operational":
        add_event_log("Ship systems critical - weapons disabled!")
        sound_manager.play_sound('error')
        return True

    # Check if weapon systems are functional
    phaser_integrity = player_ship.system_integrity.get('phasers', 100)
    if phaser_integrity <= 0:
        add_event_log("Weapon systems offline - cannot fire!")
        sound_manager.play_sound('error')
        return True

    # Check if phasers are on cooldown
    if player_ship.phaser_system.is_on_cooldown():
        cooldown_time = (player_ship.phaser_system._last_fired_time +
                        player_ship.phaser_system.cooldown_seconds) - time.time()
        add_event_log(f"Phasers recharging - {cooldown_time:.1f}s remaining")
        sound_manager.play_sound('error')
        return True

    # Fire phasers at selected enemy (only works in system mode)
    if game_state.map_mode == 'system':
        if game_state.combat.selected_enemy is not None:
            player_obj = next((obj for obj in ctx.systems.get(ctx.current_system, [])
                              if obj.type == 'player'), None)

            if player_obj is None:
                # Create player object if missing
                player_obj = _ensure_player_object(ctx)

            if (player_obj is not None and
                hasattr(player_obj, 'system_q') and
                hasattr(game_state.combat.selected_enemy, 'system_q')):

                dx = game_state.combat.selected_enemy.system_q - player_obj.system_q
                dy = game_state.combat.selected_enemy.system_r - player_obj.system_r
                distance = math.hypot(dx, dy)

                if distance <= ctx.phaser_range:
                    result = game_state.weapon_animation_manager.fire_phaser(
                        game_state.combat.selected_enemy, distance
                    )

                    if result['success']:
                        sound_manager.play_phaser_sequence()
                        add_event_log("Phaser fired!")
                    else:
                        add_event_log(f"Phaser fire failed: {result.get('reason', 'Unknown error')}")
                else:
                    add_event_log(f"Target out of range! Max range: {ctx.phaser_range} hexes")
            else:
                add_event_log("No target selected! Right-click an enemy ship.")
        else:
            add_event_log("No target selected! Right-click an enemy ship.")
    else:
        add_event_log("Weapons offline in sector view. Enter a system first.")

    return True


def _ensure_player_object(ctx: EventContext):
    """Ensure player object exists in current system, creating one if needed."""
    current_system = ctx.current_system
    systems = ctx.systems
    hex_grid = ctx.hex_grid

    occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                   for obj in systems[current_system]
                   if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))

    max_attempts = 100
    for _ in range(max_attempts):
        rand_q = random.randint(0, hex_grid.cols - 1)
        rand_r = random.randint(0, hex_grid.rows - 1)
        if (rand_q, rand_r) not in occupied:
            player_obj = MapObject('player', current_system[0], current_system[1])
            player_obj.system_q = rand_q
            player_obj.system_r = rand_r
            systems[current_system].append(player_obj)
            return player_obj

    # Fallback: place at (0, 0)
    player_obj = MapObject('player', current_system[0], current_system[1])
    player_obj.system_q = 0
    player_obj.system_r = 0
    systems[current_system].append(player_obj)
    return player_obj


def _handle_scan_button(ctx: EventContext) -> bool:
    """Handle scan button click."""
    game_state = ctx.game_state
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log
    current_system = ctx.current_system

    sound_manager.play_sound('scanner')

    if game_state.map_mode == 'sector':
        game_state.scan.sector_scan_active = True
        add_event_log("Long-range sensors activated. All systems revealed.")
        return True

    elif game_state.map_mode == 'system':
        # Check if we have targeted enemies to scan
        if game_state.combat.targeted_enemies:
            new_popups = 0
            for enemy_id, enemy_obj in game_state.combat.targeted_enemies.items():
                if enemy_id not in game_state.scan.enemy_popups:
                    popup_info = ctx.create_enemy_popup(enemy_id, enemy_obj)
                    game_state.scan.enemy_popups[enemy_id] = popup_info
                    new_popups += 1
                game_state.scan.enemy_popups[enemy_id]['visible'] = True

            if new_popups > 0:
                add_event_log(f"Scanning {new_popups} targeted enemies - detailed sensor data displayed")
            else:
                add_event_log(f"Updating sensor data for {len(game_state.combat.targeted_enemies)} targeted enemies")
        else:
            # No targeted enemies, perform system scan
            if current_system not in game_state.scan.scanned_systems:
                _perform_system_scan(ctx)
            else:
                add_event_log("System already scanned. Right-click enemies to target them for detailed scans.")

    return True


def _handle_repairs_button(ctx: EventContext) -> bool:
    """Handle repairs button click - toggle ship repairs on/off."""
    player_ship = ctx.player_ship
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log

    # Check if ship is alive
    if not player_ship.is_alive():
        add_event_log("Ship is destroyed - cannot initiate repairs!")
        sound_manager.play_sound('error')
        return True

    # Check for critical ship state
    if hasattr(player_ship, 'ship_state') and player_ship.ship_state == "hull_breach":
        add_event_log("CRITICAL: Hull breach in progress! Repairs impossible!")
        add_event_log("Evacuate or seal breaches before repairs can begin.")
        sound_manager.play_sound('error')
        return True

    # Toggle repairs
    was_repairing = player_ship.is_repairing()
    repairs_active = player_ship.toggle_repairs()

    if repairs_active:
        # Repairs started
        repair_status = player_ship.get_repair_status()
        systems = repair_status.get('systems_needing_repair', [])
        time_estimate = player_ship.repair_system.get_repair_time_estimate()

        add_event_log("*** REPAIR CREWS ACTIVATED ***")
        add_event_log(f"Repairing: {', '.join(s.upper() for s in systems)}")
        if time_estimate > 0:
            minutes = int(time_estimate // 60)
            seconds = int(time_estimate % 60)
            if minutes > 0:
                add_event_log(f"Estimated repair time: {minutes}m {seconds}s")
            else:
                add_event_log(f"Estimated repair time: {seconds}s")
        sound_manager.play_sound('scanner')  # Use scanner sound for now
    else:
        if was_repairing:
            # Repairs stopped
            add_event_log("Repair operations halted.")
            sound_manager.play_sound('scanner')
        else:
            # No repairs needed or couldn't start
            repair_status = player_ship.get_repair_status()
            if not repair_status.get('needs_repair', False):
                add_event_log("All systems operational - no repairs needed.")
            sound_manager.play_sound('error')

    return True


def _perform_system_scan(ctx: EventContext):
    """Perform a full system scan, generating system objects."""
    game_state = ctx.game_state
    current_system = ctx.current_system
    add_event_log = ctx.add_event_log
    hex_grid = ctx.hex_grid
    systems = ctx.systems
    planet_orbits = ctx.planet_orbits
    planet_anim_state = ctx.planet_anim_state

    game_state.scan.scanned_systems.add(current_system)
    add_event_log("System scan complete. No enemies targeted - right-click enemies to target them for detailed scans.")

    # Generate system objects
    system_objs = generate_system_objects(
        current_system[0],
        current_system[1],
        ctx.lazy_object_coords,
        star_coords=ctx.star_coords,
        planet_orbits=planet_orbits,
        grid_size=hex_grid.cols
    )

    # Preserve existing player ship position if it exists
    existing_player = None
    if current_system in systems:
        existing_player = next((obj for obj in systems[current_system] if obj.type == 'player'), None)

    # Assign random system positions to non-player objects
    for obj in system_objs:
        if obj.type == 'player' and existing_player:
            obj.system_q = existing_player.system_q
            obj.system_r = existing_player.system_r
        else:
            obj.system_q = random.randint(0, hex_grid.cols - 1)
            obj.system_r = random.randint(0, hex_grid.rows - 1)

    # Handle planet visibility
    planets_in_hex = [orbit['planet'] for orbit in planet_orbits if orbit['star'] == current_system]
    for planet_coord in planets_in_hex:
        existing_orbit = next((orbit for orbit in planet_orbits if orbit['planet'] == planet_coord), None)
        if not existing_orbit:
            new_orbit = {
                'star': current_system,
                'planet': planet_coord,
                'hex_radius': random.randint(8, 15),
                'angle': random.uniform(0, 2 * math.pi),
                'speed': random.uniform(0.02, 0.1)
            }
            planet_orbits.append(new_orbit)
            planet_anim_state[(current_system, planet_coord)] = new_orbit['angle']

    # Update systems
    systems[current_system] = system_objs
    game_state.system_object_states[current_system] = [
        {
            'type': obj.type,
            'q': obj.q,
            'r': obj.r,
            'system_q': obj.system_q,
            'system_r': obj.system_r,
            'props': obj.props
        } for obj in system_objs
    ]

    # Ensure player object exists
    player_obj = next((obj for obj in systems[current_system] if obj.type == 'player'), None)
    if player_obj is None:
        _place_player_in_system(ctx)


def _place_player_in_system(ctx: EventContext):
    """Place player in current system at an unoccupied hex."""
    current_system = ctx.current_system
    systems = ctx.systems
    hex_grid = ctx.hex_grid

    occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                   for obj in systems[current_system]
                   if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))

    max_attempts = 100
    for _ in range(max_attempts):
        rand_q = random.randint(0, hex_grid.cols - 1)
        rand_r = random.randint(0, hex_grid.rows - 1)
        blocked, _ = ctx.is_hex_blocked(rand_q, rand_r, current_system, systems,
                                        ctx.planet_orbits, hex_grid)
        if (rand_q, rand_r) not in occupied and not blocked:
            player_obj = MapObject('player', current_system[0], current_system[1])
            player_obj.system_q = rand_q
            player_obj.system_r = rand_r
            systems[current_system].append(player_obj)
            return

    # Fallback: find any unblocked hex
    for attempt_q in range(hex_grid.cols):
        for attempt_r in range(hex_grid.rows):
            blocked, _ = ctx.is_hex_blocked(attempt_q, attempt_r, current_system,
                                           systems, ctx.planet_orbits, hex_grid)
            if not blocked:
                player_obj = MapObject('player', current_system[0], current_system[1])
                player_obj.system_q = attempt_q
                player_obj.system_r = attempt_r
                systems[current_system].append(player_obj)
                return


def handle_toggle_click(ctx: EventContext) -> bool:
    """Handle toggle button click to switch between sector and system view."""
    game_state = ctx.game_state
    sound_manager = ctx.sound_manager
    add_event_log = ctx.add_event_log

    sound_manager.play_sound('keypress')
    new_mode = 'system' if game_state.map_mode == 'sector' else 'sector'
    add_event_log(f"Switched to {new_mode} view")
    game_state.map_mode = new_mode
    return True


def handle_sector_map_click(mx: int, my: int, ctx: EventContext, result: EventResult) -> bool:
    """
    Handle left-click on sector map for navigation.
    Returns True if the click was handled.
    """
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    player_ship = ctx.player_ship
    add_event_log = ctx.add_event_log
    sound_manager = ctx.sound_manager

    q, r = hex_grid.pixel_to_hex(mx, my)
    if q is None or r is None:
        return False

    # Determine starting position for trajectory calculation
    if game_state.animation.ship_moving:
        start_hex_q, start_hex_r = hex_grid.pixel_to_hex(
            game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)
        if start_hex_q is None or start_hex_r is None:
            start_hex_q, start_hex_r = ctx.ship_q, ctx.ship_r
        log_debug(f"[REDIRECT] Ship redirecting mid-flight from ({start_hex_q}, {start_hex_r}) to ({q}, {r})")
        action_msg = "Changing course"
    else:
        start_hex_q, start_hex_r = ctx.ship_q, ctx.ship_r
        action_msg = "Setting course"

    # Calculate distance and energy cost
    dx = abs(q - start_hex_q)
    dy = abs(r - start_hex_r)
    distance = max(dx, dy)

    if game_state.animation.ship_moving:
        energy_cost = distance * constants.WARP_ENERGY_COST
    else:
        energy_cost = constants.WARP_INITIATION_COST + (distance * constants.WARP_ENERGY_COST)

    # Check if ship is capable of movement
    if not player_ship.is_alive():
        add_event_log("Ship is destroyed - movement impossible!")
        return True

    if hasattr(player_ship, 'ship_state') and player_ship.ship_state != "operational":
        add_event_log("Ship systems critical - movement disabled!")
        return True

    engine_integrity = player_ship.system_integrity.get('engines', 100)
    if engine_integrity <= 0:
        add_event_log("Engine systems offline - movement impossible!")
        return True

    engine_power = player_ship.power_allocation.get('engines', 5)
    if engine_power <= 0:
        add_event_log("Engine power offline - allocate power to engines for movement!")
        return True

    # Calculate dynamic energy cost
    dynamic_energy_cost = player_ship.get_movement_energy_cost(energy_cost)

    if player_ship.warp_core_energy >= dynamic_energy_cost:
        base_duration = 2000
        movement_duration = player_ship.get_movement_duration(base_duration)

        game_state.animation.dest_q, game_state.animation.dest_r = q, r
        game_state.animation.ship_moving = True
        game_state.animation.move_start_time = pygame.time.get_ticks()
        game_state.animation.move_duration_ms = movement_duration

        result.trajectory_start_x = game_state.animation.ship_anim_x
        result.trajectory_start_y = game_state.animation.ship_anim_y

        sound_manager.play_movement_sound('warp', movement_duration)

        efficiency = player_ship.get_engine_efficiency()
        add_event_log(f"{action_msg} for sector ({q}, {r}) - Engine Power: {engine_power} - Duration: {movement_duration/1000:.1f}s")
        add_event_log(f"Energy cost: {dynamic_energy_cost} - Engine efficiency: {efficiency:.1f}x")
    else:
        add_event_log(f"Insufficient energy! Need {energy_cost}, have {player_ship.warp_core_energy}")
        sound_manager.play_sound('error')

    return True


def handle_system_map_click(mx: int, my: int, ctx: EventContext, result: EventResult) -> bool:
    """
    Handle left-click on system map for navigation.
    Returns True if the click was handled.
    """
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    player_ship = ctx.player_ship
    add_event_log = ctx.add_event_log
    sound_manager = ctx.sound_manager
    current_system = ctx.current_system
    systems = ctx.systems
    planet_orbits = ctx.planet_orbits

    player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
    if player_obj is None:
        return False

    q, r = hex_grid.pixel_to_hex(mx, my)
    if q is None or r is None:
        return False

    # Check if destination is blocked
    blocked, block_type = ctx.is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)

    if blocked:
        if block_type == 'planet':
            return _handle_planet_click(q, r, ctx, result)
        else:
            add_event_log(f"Cannot move to ({q}, {r}) - blocked by {block_type}!")
            return True

    # Exit orbit mode if player was orbiting
    if game_state.orbital.player_orbiting_planet:
        game_state.orbital.player_orbiting_planet = False
        game_state.orbital.player_orbit_center = None
        result.player_orbit_key = None
        add_event_log("Breaking orbit")

    # Handle movement
    return _handle_system_movement(q, r, player_obj, ctx, result)


def _handle_planet_click(q: int, r: int, ctx: EventContext, result: EventResult) -> bool:
    """Handle clicking on a planet hex."""
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    add_event_log = ctx.add_event_log
    current_system = ctx.current_system
    systems = ctx.systems
    planet_orbits = ctx.planet_orbits
    planet_anim_state = ctx.planet_anim_state
    player_ship = ctx.player_ship

    wants_orbit = show_orbit_dialog(ctx.screen, ctx.font)
    if not wants_orbit:
        add_event_log(f"Cannot move to ({q}, {r}) - blocked by planet!")
        return True

    # Find the planet at this location
    planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
    for orbit in planets_in_system:
        star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
        if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
            star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
            hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
            orbit_radius_px = orbit['hex_radius'] * hex_size
            key = (orbit['star'], orbit['planet'])
            angle = planet_anim_state.get(key, orbit['angle'])
            planet_px = star_px + orbit_radius_px * math.cos(angle)
            planet_py = star_py + orbit_radius_px * math.sin(angle)

            planet_q, planet_r = hex_grid.pixel_to_hex(planet_px, planet_py)
            if planet_q is not None and planet_r is not None:
                planet_hexes = get_planet_hexes(planet_q, planet_r)
                if (q, r) in planet_hexes:
                    current_player_obj = next((obj for obj in systems.get(current_system, [])
                                              if obj.type == 'player'), None)

                    if (current_player_obj and
                        current_player_obj.system_q == q and
                        current_player_obj.system_r == r):
                        # Already at planet - start orbiting immediately
                        _start_orbit(planet_px, planet_py, key, ctx, result)
                    else:
                        # Need to move to planet first
                        _move_to_planet(q, r, planet_px, planet_py, key, current_player_obj, ctx, result)
                    return True

    add_event_log(f"Cannot find planet at ({q}, {r})")
    return True


def _start_orbit(planet_px: float, planet_py: float, key: tuple, ctx: EventContext, result: EventResult):
    """Start orbiting a planet."""
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    add_event_log = ctx.add_event_log
    current_system = ctx.current_system
    systems = ctx.systems

    current_player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)

    # Calculate initial orbital angle
    if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
        dx = ctx.system_ship_anim_x - planet_px
        dy = ctx.system_ship_anim_y - planet_py
        initial_angle = math.atan2(dy, dx)
    else:
        ship_px, ship_py = hex_grid.get_hex_center(current_player_obj.system_q, current_player_obj.system_r)
        dx = ship_px - planet_px
        dy = ship_py - planet_py
        initial_angle = math.atan2(dy, dx)

    game_state.orbital.player_orbiting_planet = True
    game_state.orbital.player_orbit_center = (planet_px, planet_py)
    result.player_orbit_key = key
    game_state.orbital.orbital_angle = initial_angle
    add_event_log(f"Entering orbit around planet")


def _move_to_planet(q: int, r: int, planet_px: float, planet_py: float, key: tuple,
                    current_player_obj, ctx: EventContext, result: EventResult):
    """Move to a planet and set up pending orbit."""
    player_ship = ctx.player_ship
    add_event_log = ctx.add_event_log
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state

    if current_player_obj is None:
        add_event_log("Cannot find player position for orbital movement")
        return

    dx = abs(q - current_player_obj.system_q)
    dy = abs(r - current_player_obj.system_r)
    distance = max(dx, dy)
    energy_cost = distance * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX

    if player_ship.warp_core_energy >= energy_cost:
        result.pending_orbit_center = (planet_px, planet_py)
        result.pending_orbit_key = key

        result.system_dest_q = q
        result.system_dest_r = r
        result.system_ship_moving = True
        result.system_move_start_time = pygame.time.get_ticks()

        if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
            result.system_trajectory_start_x = ctx.system_ship_anim_x
            result.system_trajectory_start_y = ctx.system_ship_anim_y
        else:
            start_pos_x, start_pos_y = hex_grid.get_hex_center(
                current_player_obj.system_q, current_player_obj.system_r)
            result.system_ship_anim_x = start_pos_x
            result.system_ship_anim_y = start_pos_y
            result.system_trajectory_start_x = start_pos_x
            result.system_trajectory_start_y = start_pos_y

        game_state.orbital.player_orbiting_planet = False
        game_state.orbital.player_orbit_center = None

        add_event_log(f"Moving to planet at ({q}, {r}) to enter orbit")
    else:
        add_event_log(f"Insufficient energy to reach planet. Need {energy_cost}, have {player_ship.warp_core_energy}")


def _handle_system_movement(q: int, r: int, player_obj, ctx: EventContext, result: EventResult) -> bool:
    """Handle movement within a system."""
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    player_ship = ctx.player_ship
    add_event_log = ctx.add_event_log
    sound_manager = ctx.sound_manager

    # Determine starting position
    if ctx.system_ship_moving:
        start_hex_q, start_hex_r = hex_grid.pixel_to_hex(ctx.system_ship_anim_x, ctx.system_ship_anim_y)
        if start_hex_q is None or start_hex_r is None:
            start_hex_q, start_hex_r = player_obj.system_q, player_obj.system_r
        action_msg = "Changing course"
    else:
        start_hex_q, start_hex_r = player_obj.system_q, player_obj.system_r
        action_msg = "Setting course"

    # Calculate distance and energy cost
    dx = abs(q - start_hex_q)
    dy = abs(r - start_hex_r)
    distance = max(dx, dy)
    base_energy_cost = distance * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX

    # Check movement capability
    if not player_ship.is_alive():
        add_event_log("Ship is destroyed - movement impossible!")
        return True

    if hasattr(player_ship, 'ship_state') and player_ship.ship_state != "operational":
        add_event_log("Ship systems critical - movement disabled!")
        return True

    engine_integrity = player_ship.system_integrity.get('engines', 100)
    if engine_integrity <= 0:
        add_event_log("Engine systems offline - movement impossible!")
        return True

    engine_power = player_ship.power_allocation.get('engines', 5)
    if engine_power <= 0:
        add_event_log("Engine power offline - allocate power to engines for movement!")
        return True

    energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)

    if player_ship.warp_core_energy >= energy_cost:
        base_duration = 1000
        movement_duration = player_ship.get_movement_duration(base_duration)

        result.system_dest_q = q
        result.system_dest_r = r
        result.system_ship_moving = True
        result.system_move_start_time = pygame.time.get_ticks()
        result.system_move_duration_ms = movement_duration

        if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
            result.system_trajectory_start_x = ctx.system_ship_anim_x
            result.system_trajectory_start_y = ctx.system_ship_anim_y
        else:
            start_pos_x, start_pos_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
            result.system_ship_anim_x = start_pos_x
            result.system_ship_anim_y = start_pos_y
            result.system_trajectory_start_x = start_pos_x
            result.system_trajectory_start_y = start_pos_y

        sound_manager.play_movement_sound('impulse', movement_duration)

        efficiency = player_ship.get_engine_efficiency()
        add_event_log(f"{action_msg} for system hex ({q}, {r}) - Engine Power: {engine_power} - Duration: {movement_duration/1000:.1f}s")
        add_event_log(f"Energy cost: {energy_cost} - Engine efficiency: {efficiency:.1f}x")
    else:
        add_event_log(f"Insufficient energy! Need {energy_cost}, have {player_ship.warp_core_energy}")
        sound_manager.play_sound('error')

    return True


def handle_right_click(mx: int, my: int, ctx: EventContext) -> bool:
    """
    Handle right-click for targeting enemies or scanning celestial objects.
    Returns True if the click was handled.
    """
    game_state = ctx.game_state
    hex_grid = ctx.hex_grid
    add_event_log = ctx.add_event_log
    current_system = ctx.current_system
    systems = ctx.systems
    planet_orbits = ctx.planet_orbits
    planet_anim_state = ctx.planet_anim_state
    sound_manager = ctx.sound_manager

    if game_state.map_mode != 'system':
        return False

    q, r = hex_grid.pixel_to_hex(mx, my)
    if q is None or r is None:
        return False

    # Check for planets at clicked location
    scanned_celestial = False
    planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
    for orbit in planets_in_system:
        star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
        if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
            star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
            hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
            orbit_radius_px = orbit['hex_radius'] * hex_size
            key = (orbit['star'], orbit['planet'])
            angle = planet_anim_state.get(key, orbit['angle'])
            planet_px = star_px + orbit_radius_px * math.cos(angle)
            planet_py = star_py + orbit_radius_px * math.sin(angle)

            planet_q, planet_r = hex_grid.pixel_to_hex(planet_px, planet_py)
            if planet_q is not None and planet_r is not None:
                planet_hexes = get_planet_hexes(planet_q, planet_r)
                if (q, r) in planet_hexes:
                    ctx.perform_planet_scan(q, r)
                    scanned_celestial = True
                    break

    # Check for stars at clicked location
    if not scanned_celestial:
        for obj in systems.get(current_system, []):
            if obj.type == 'star' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                star_hexes = get_star_hexes(obj.system_q, obj.system_r)
                if (q, r) in star_hexes:
                    ctx.perform_star_scan(obj.system_q, obj.system_r)
                    scanned_celestial = True
                    break

    if scanned_celestial:
        return True

    # Always set torpedo target hex for any right-clicked location
    # Torpedoes can be fired at any hex, even empty space
    game_state.set_torpedo_target_hex(q, r)

    # Find enemy at this hex
    found_enemy = None
    for obj in systems.get(current_system, []):
        if obj.type == 'enemy' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
            if obj.system_q == q and obj.system_r == r:
                found_enemy = obj
                break

    if found_enemy is not None:
        # Enemy found - set phaser target (tracks enemy) AND torpedo target (fixed hex)
        enemy_id = ctx.get_enemy_id(found_enemy)
        game_state.combat.selected_enemy = found_enemy

        if enemy_id in game_state.combat.targeted_enemies:
            add_event_log(f"Switching target to {enemy_id}")
        else:
            game_state.combat.targeted_enemies[enemy_id] = found_enemy
            add_event_log(f"Target {enemy_id} acquired at ({q}, {r})")

        add_event_log(f"Torpedo target locked at ({q}, {r})")
        ctx.perform_enemy_scan(found_enemy, enemy_id)
        sound_manager.play_sound('scanner')
    else:
        # No enemy - set torpedo target only (phasers need an enemy)
        add_event_log(f"Torpedo target set at ({q}, {r}) - no enemy for phasers")
        sound_manager.play_sound('scanner')

    return True
