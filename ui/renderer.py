"""
Rendering module for the Star Trek Tactical Game.

This module contains all rendering functions extracted from wireframe.py to improve
code organization and maintainability.
"""
import pygame
import math
import random
import time

from ui.hex_utils import get_star_hexes
from ui.drawing_utils import get_star_color, get_planet_color
from ui.text_utils import wrap_text


class RenderContext:
    """Context object containing all state needed for rendering."""

    def __init__(self):
        # Screen and fonts
        self.screen = None
        self.font = None
        self.label_font = None
        self.title_font = None
        self.small_font = None

        # Layout dimensions
        self.width = 0
        self.height = 0
        self.map_x = 0
        self.map_y = 0
        self.map_size = 0
        self.status_height = 0
        self.event_log_x = 0
        self.event_log_y = 0
        self.event_log_width = 0
        self.event_log_height = 0
        self.bottom_pane_y = 0
        self.bottom_pane_height = 0
        self.image_display_width = 0
        self.control_panel_width = 0
        self.popup_dock_x = 0
        self.enemy_scan_width = 0

        # Colors
        self.color_status = (60, 60, 100)
        self.color_map = (40, 40, 60)
        self.color_event_log = (30, 30, 50)
        self.color_event_log_border = (80, 80, 120)
        self.color_image_display = (30, 50, 30)
        self.color_control_panel = (50, 30, 30)
        self.color_button_area_border = (80, 50, 50)
        self.color_text = (220, 220, 220)
        self.hex_outline = (180, 180, 220)

        # Game state
        self.game_state = None
        self.player_ship = None
        self.hex_grid = None
        self.background_loader = None
        self.stardate_system = None

        # System data
        self.systems = None
        self.star_coords = None
        self.planet_orbits = None
        self.lazy_object_coords = None
        self.current_system = None

        # Animation state
        self.planet_anim_state = None
        self.planet_images_assigned = None
        self.planet_colors = None
        self.delta_time = 0

        # Ship position state (system map)
        self.system_ship_anim_x = None
        self.system_ship_anim_y = None
        self.system_ship_moving = False
        self.system_dest_q = None
        self.system_dest_r = None

        # Scan/display state
        self.current_scanned_object = None
        self.current_scanned_image = None

        # Event log max lines
        self.event_log_max_lines = 20

        # Button panel settings
        self.control_panel_label_spacer = 50
        self.button_w = 100
        self.button_h = 40
        self.button_gap = 10
        self.button_color = (80, 80, 120)
        self.toggle_btn_w = 150
        self.toggle_btn_h = 40
        self.toggle_btn_y = 50


def draw_status_bar(ctx):
    """Draw the status/tooltip panel at the top of the screen.

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    player_ship = ctx.player_ship
    stardate_system = ctx.stardate_system
    font = ctx.font
    label_font = ctx.label_font
    width = ctx.width

    # Status/Tooltip Panel (top)
    status_rect = pygame.Rect(0, 0, width, ctx.status_height)
    pygame.draw.rect(screen, ctx.color_status, status_rect)
    status_label = label_font.render('Status/Tooltip Panel', True, ctx.color_text)
    screen.blit(status_label, (10, 8))

    # Weapon Cooldown Display (just left of stardate)
    cooldown_y = 8
    cooldown_x = width - 320

    # Phaser Cooldown
    if hasattr(player_ship, 'phaser_system') and player_ship.phaser_system.is_on_cooldown():
        cooldown_time = (player_ship.phaser_system._last_fired_time +
                         player_ship.phaser_system.cooldown_seconds) - time.time()
        if cooldown_time > 0:
            cooldown_label = font.render(f"Phasers: {cooldown_time:.1f}s", True, (255, 255, 0))
            screen.blit(cooldown_label, (cooldown_x, cooldown_y))
            cooldown_y += 20

    # Torpedo Cooldown
    if hasattr(player_ship, 'torpedo_system') and player_ship.torpedo_system.is_on_cooldown():
        cooldown_time = (player_ship.torpedo_system._last_fired_time +
                         player_ship.torpedo_system.cooldown_seconds) - time.time()
        if cooldown_time > 0:
            cooldown_label = font.render(f"Torpedoes: {cooldown_time:.1f}s", True, (255, 100, 100))
            screen.blit(cooldown_label, (cooldown_x, cooldown_y))

    # Stardate Display
    stardate_label = font.render(stardate_system.format_stardate(), True, ctx.color_text)
    screen.blit(stardate_label, (width - 180, 8))


def draw_map_background(ctx):
    """Draw the main map area background and grid.

    Args:
        ctx: RenderContext with all necessary state

    Returns:
        pygame.Rect: The map rectangle
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state
    background_loader = ctx.background_loader

    # Main Map Area (perfect square, flush left)
    map_rect = pygame.Rect(ctx.map_x, ctx.map_y, ctx.map_size, ctx.map_size)
    pygame.draw.rect(screen, ctx.color_map, map_rect)

    # Draw background image (lowest layer)
    background_img = background_loader.get_scaled_background(ctx.map_size, ctx.map_size)
    if background_img:
        screen.blit(background_img, (ctx.map_x, ctx.map_y))

    # Draw stars in background (before hex grid) for system view
    if game_state.map_mode == 'system':
        _draw_system_stars_background(ctx)

    # Draw the hex grid with conditional transparency based on map mode
    grid_alpha = 64 if game_state.map_mode == 'sector' else 20
    hex_grid.draw_grid(screen, ctx.hex_outline, alpha=grid_alpha)

    return map_rect


def _draw_system_stars_background(ctx):
    """Draw stars that span multiple hexes in system view (background layer).

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    systems = ctx.systems
    current_system = ctx.current_system
    background_loader = ctx.background_loader

    for obj in systems.get(current_system, []):
        if obj.type == 'star':
            if not hasattr(obj, 'system_q') or not hasattr(obj, 'system_r'):
                obj.system_q = random.randint(1, hex_grid.cols - 2)
                obj.system_r = random.randint(1, hex_grid.rows - 2)

            # Draw star across multiple hexes
            star_hexes = get_star_hexes(obj.system_q, obj.system_r)
            sum_x, sum_y = 0, 0
            valid_hexes = []
            for hq, hr in star_hexes:
                if 0 <= hq < hex_grid.cols and 0 <= hr < hex_grid.rows:
                    hx, hy = hex_grid.get_hex_center(hq, hr)
                    sum_x += hx
                    sum_y += hy
                    valid_hexes.append((hx, hy))

            if valid_hexes:
                center_x = sum_x / len(valid_hexes)
                center_y = sum_y / len(valid_hexes)

                # Get or assign star image
                if not hasattr(obj, 'star_image'):
                    obj.star_image = background_loader.get_random_star_image()
                    obj.scaled_star_image = None

                # Draw star image if available, otherwise fallback to circle
                if obj.star_image:
                    if obj.scaled_star_image is None:
                        obj.scaled_star_image = background_loader.scale_star_image(
                            obj.star_image, hex_grid.radius * 3.6
                        )

                    if obj.scaled_star_image:
                        image_rect = obj.scaled_star_image.get_rect()
                        image_rect.center = (int(center_x), int(center_y))
                        screen.blit(obj.scaled_star_image, image_rect)
                    else:
                        if not hasattr(obj, 'color'):
                            obj.color = get_star_color()
                        pygame.draw.circle(screen, obj.color,
                                          (int(center_x), int(center_y)),
                                          int(hex_grid.radius * 3.6))
                else:
                    if not hasattr(obj, 'color'):
                        obj.color = get_star_color()
                    pygame.draw.circle(screen, obj.color,
                                      (int(center_x), int(center_y)),
                                      int(hex_grid.radius * 3.6))


def draw_fog_of_war(ctx):
    """Draw fog of war overlay on unscanned hexes.

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state

    # Only apply fog of war to sector map, not system maps
    if game_state.map_mode == 'sector':
        for row in range(hex_grid.rows):
            for col in range(hex_grid.cols):
                if (col, row) not in game_state.scan.scanned_systems:
                    cx, cy = hex_grid.get_hex_center(col, row)
                    hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)


def draw_sector_objects(ctx, add_event_log_func=None):
    """Draw objects on the sector map (system indicators).

    Args:
        ctx: RenderContext with all necessary state
        add_event_log_func: Optional function to add log messages
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state
    systems = ctx.systems
    star_coords = ctx.star_coords
    lazy_object_coords = ctx.lazy_object_coords
    planet_orbits = ctx.planet_orbits

    if not game_state.scan.sector_scan_active:
        return

    # Show indicator for any hex that has actual systems
    occupied_hexes = set(star_coords)
    for coords_set in lazy_object_coords.values():
        occupied_hexes.update(coords_set)

    # Ensure starbase systems are generated for sector map display
    if 'starbase' in lazy_object_coords:
        for starbase_coord in lazy_object_coords['starbase']:
            if starbase_coord not in systems:
                from galaxy_generation.object_placement import generate_system_objects
                starbase_objects = generate_system_objects(
                    starbase_coord[0], starbase_coord[1],
                    lazy_object_coords,
                    star_coords=star_coords,
                    planet_orbits=planet_orbits,
                    grid_size=hex_grid.cols
                )
                systems[starbase_coord] = starbase_objects

    # Draw indicators
    for q, r in occupied_hexes:
        px, py = hex_grid.get_hex_center(q, r)

        # Check if this system contains a starbase
        system_has_starbase = False
        system_objects = systems.get((q, r), [])
        for obj in system_objects:
            if obj.type == 'starbase':
                system_has_starbase = True
                break

        # Draw dot with appropriate color
        dot_color = (144, 238, 144) if system_has_starbase else (100, 100, 130)
        pygame.draw.circle(screen, dot_color, (int(px), int(py)), 6)


def draw_sector_player_ship(ctx):
    """Draw the player ship on the sector map.

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state
    background_loader = ctx.background_loader
    delta_time = ctx.delta_time

    player_img = background_loader.get_player_ship_image()
    if player_img:
        scaled_player = background_loader.scale_ship_image(player_img, hex_grid.radius)
        if scaled_player:
            # Initialize rotation tracking if not exists
            if not hasattr(game_state.animation, 'player_current_rotation'):
                game_state.animation.player_current_rotation = 0.0

            if not hasattr(game_state.animation, 'player_target_rotation'):
                game_state.animation.player_target_rotation = game_state.animation.player_current_rotation

            # Update target rotation only when destination changes
            if (game_state.animation.ship_moving and
                game_state.animation.dest_q is not None and
                game_state.animation.dest_r is not None):
                current_pos = (game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)
                dest_pos = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
                new_target_rotation = background_loader.calculate_movement_angle(current_pos, dest_pos)

                if (not hasattr(game_state.animation, 'last_dest_q') or
                    game_state.animation.last_dest_q != game_state.animation.dest_q or
                    game_state.animation.last_dest_r != game_state.animation.dest_r):
                    game_state.animation.player_target_rotation = new_target_rotation
                    game_state.animation.last_dest_q = game_state.animation.dest_q
                    game_state.animation.last_dest_r = game_state.animation.dest_r

            target_rotation = game_state.animation.player_target_rotation

            # Smoothly interpolate to target rotation
            rotation_speed = 720.0  # degrees per second
            game_state.animation.player_current_rotation = background_loader.interpolate_rotation(
                game_state.animation.player_current_rotation,
                target_rotation,
                rotation_speed,
                delta_time
            )

            # Apply rotation and draw
            rotated_player = background_loader.rotate_ship_image(
                scaled_player, game_state.animation.player_current_rotation
            )
            img_rect = rotated_player.get_rect(
                center=(int(game_state.animation.ship_anim_x),
                       int(game_state.animation.ship_anim_y))
            )
            screen.blit(rotated_player, img_rect)
        else:
            # Fallback to circle
            pygame.draw.circle(
                screen, (0, 255, 255),
                (int(game_state.animation.ship_anim_x),
                 int(game_state.animation.ship_anim_y)), 8
            )
    else:
        # Fallback to circle
        pygame.draw.circle(
            screen, (0, 255, 255),
            (int(game_state.animation.ship_anim_x),
             int(game_state.animation.ship_anim_y)), 8
        )


def draw_event_log_panel(ctx):
    """Draw the right-side event log panel.

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    game_state = ctx.game_state
    label_font = ctx.label_font
    small_font = ctx.small_font

    # Right-side Event Log Panel
    right_event_rect = pygame.Rect(ctx.event_log_x, ctx.event_log_y,
                                   ctx.event_log_width, ctx.event_log_height)
    pygame.draw.rect(screen, ctx.color_event_log, right_event_rect)
    pygame.draw.rect(screen, ctx.color_event_log_border, right_event_rect, 2)
    event_label = label_font.render('Event Log', True, ctx.color_text)
    screen.blit(event_label, (ctx.event_log_x + 20, ctx.event_log_y + 20))

    # Draw event log lines with text wrapping
    log_font = small_font
    log_area_width = ctx.event_log_width - 40
    y_offset = ctx.event_log_y + 50
    line_height = 20

    rendered_lines = 0
    for line in game_state.ui.event_log[-ctx.event_log_max_lines:]:
        if rendered_lines >= ctx.event_log_max_lines:
            break

        wrapped_lines = wrap_text(line, log_area_width, log_font)
        for wrapped_line in wrapped_lines:
            if rendered_lines >= ctx.event_log_max_lines:
                break
            text_surface = log_font.render(wrapped_line, True, ctx.color_text)
            screen.blit(text_surface, (ctx.event_log_x + 20, y_offset + rendered_lines * line_height))
            rendered_lines += 1


def draw_popup_dock(ctx):
    """Draw the popup dock area (right of event log).

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    label_font = ctx.label_font

    popup_dock_rect = pygame.Rect(ctx.popup_dock_x, ctx.status_height,
                                  ctx.enemy_scan_width, ctx.height - ctx.status_height)
    pygame.draw.rect(screen, (25, 25, 40), popup_dock_rect)
    pygame.draw.rect(screen, ctx.color_event_log_border, popup_dock_rect, 2)
    dock_label = label_font.render('Scan Results', True, ctx.color_text)
    screen.blit(dock_label, (ctx.popup_dock_x + 20, ctx.status_height + 20))


def draw_image_display_panel(ctx):
    """Draw the image display panel (bottom left).

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    font = ctx.font
    label_font = ctx.label_font

    image_rect = pygame.Rect(0, ctx.bottom_pane_y,
                             ctx.image_display_width, ctx.bottom_pane_height)
    pygame.draw.rect(screen, ctx.color_image_display, image_rect)
    image_label = label_font.render('Target Image Display', True, ctx.color_text)
    screen.blit(image_label, (20, ctx.bottom_pane_y + 20))

    # Display scanned object image and info
    if ctx.current_scanned_object and ctx.current_scanned_image:
        image_display_y = ctx.bottom_pane_y + 50
        image_display_height = ctx.bottom_pane_height - 80

        scaled_image = pygame.transform.scale(
            ctx.current_scanned_image,
            (min(ctx.image_display_width - 40, 150), min(image_display_height - 60, 150))
        )
        image_x = 20 + (ctx.image_display_width - 40 - scaled_image.get_width()) // 2
        image_y = image_display_y + 10
        screen.blit(scaled_image, (image_x, image_y))

        # Display object information
        info_y = image_y + scaled_image.get_height() + 15
        name_text = font.render(ctx.current_scanned_object['name'], True, ctx.color_text)
        screen.blit(name_text, (20, info_y))
        info_y += 20

        if ctx.current_scanned_object['type'] == 'planet':
            class_text = font.render(f"Class {ctx.current_scanned_object['class']}", True, ctx.color_text)
        else:
            class_text = font.render(
                ctx.current_scanned_object['class'].replace('_', ' ').title(), True, ctx.color_text
            )
        screen.blit(class_text, (20, info_y))
    else:
        # Show instructions when no object is scanned
        instruction_text = font.render('Right-click on a planet or star to scan', True, ctx.color_text)
        screen.blit(instruction_text, (20, ctx.bottom_pane_y + 60))


def draw_control_panel(ctx):
    """Draw the control panel (bottom right).

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    label_font = ctx.label_font

    control_rect = pygame.Rect(ctx.image_display_width, ctx.bottom_pane_y,
                               ctx.control_panel_width, ctx.bottom_pane_height)
    pygame.draw.rect(screen, ctx.color_control_panel, control_rect)
    control_label = label_font.render('Control Panel', True, ctx.color_text)
    screen.blit(control_label, (ctx.image_display_width + 20, ctx.bottom_pane_y + 20))

    # Draw border around button area
    button_area_x = ctx.image_display_width + 30
    button_area_y = ctx.bottom_pane_y + ctx.control_panel_label_spacer - 10
    button_area_width = ctx.control_panel_width - 40
    button_area_height = ctx.bottom_pane_height - ctx.control_panel_label_spacer
    button_area_rect = pygame.Rect(button_area_x, button_area_y, button_area_width, button_area_height)
    pygame.draw.rect(screen, ctx.color_button_area_border, button_area_rect, 2)


def draw_destination_indicator(ctx):
    """Draw the destination indicator (red circle) when ship is moving.

    Args:
        ctx: RenderContext with all necessary state
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state

    # Sector map destination
    if (game_state.animation.ship_moving and
        game_state.animation.dest_q is not None and
        game_state.animation.dest_r is not None and
        game_state.map_mode == 'sector'):
        dest_x, dest_y = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
        pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)

    # System map destination
    if (ctx.system_ship_moving and
        ctx.system_dest_q is not None and
        ctx.system_dest_r is not None and
        game_state.map_mode == 'system'):
        dest_x, dest_y = hex_grid.get_hex_center(ctx.system_dest_q, ctx.system_dest_r)
        pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)


def draw_phaser_animation(ctx, current_time, get_enemy_position_func):
    """Draw the phaser beam animation.

    Args:
        ctx: RenderContext with all necessary state
        current_time: Current game time in milliseconds
        get_enemy_position_func: Function to get enemy position
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state
    systems = ctx.systems
    current_system = ctx.current_system

    phaser_anim_data = game_state.weapon_animation_manager.get_phaser_animation_data(current_time)
    if phaser_anim_data and phaser_anim_data['active']:
        player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
        if player_obj is not None:
            # Use animated position if available
            if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
                px1, py1 = ctx.system_ship_anim_x, ctx.system_ship_anim_y
            else:
                px1, py1 = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
            px2, py2 = get_enemy_position_func(phaser_anim_data['target_enemy'], hex_grid)

            # Draw laser line (yellow/red alternating)
            color = (255, 255, 0) if (current_time // 100) % 2 == 0 else (255, 0, 0)
            pygame.draw.line(screen, color, (int(px1), int(py1)), (int(px2), int(py2)), 4)


def draw_torpedo_animation(ctx, current_time):
    """Draw the torpedo projectile and explosion animation.

    Args:
        ctx: RenderContext with all necessary state
        current_time: Current game time in milliseconds
    """
    screen = ctx.screen
    game_state = ctx.game_state

    torpedo_anim_data = game_state.weapon_animation_manager.get_torpedo_animation_data(current_time)
    if torpedo_anim_data:
        if torpedo_anim_data['state'] == 'traveling':
            # Draw torpedo as a bright white circle
            torpedo_x, torpedo_y = torpedo_anim_data['position']
            pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 6)
            pygame.draw.circle(screen, (255, 255, 0), (int(torpedo_x), int(torpedo_y)), 8, 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 3)
        elif torpedo_anim_data['state'] == 'exploding':
            # Draw proximity explosion animation
            target_x, target_y = torpedo_anim_data['position']
            waves = torpedo_anim_data.get('waves', [])

            for wave in waves:
                radius = wave['radius']
                opacity = wave['opacity']
                wave_index = wave['wave_index']

                # Color variation based on wave index
                if wave_index == 0:
                    color = (255, 255, 255, min(opacity, 255))
                elif wave_index == 1:
                    color = (255, 255, 0, min(opacity, 255))
                elif wave_index == 2:
                    color = (255, 150, 0, min(opacity, 255))
                else:
                    color = (255, 50, 0, min(opacity, 255))

                if radius > 0:
                    wave_surface = pygame.Surface(
                        (int(radius * 2 + 10), int(radius * 2 + 10)), pygame.SRCALPHA
                    )
                    wave_center = (int(radius + 5), int(radius + 5))
                    pygame.draw.circle(wave_surface, color[:3], wave_center, int(radius))
                    wave_surface.set_alpha(opacity)
                    screen.blit(
                        wave_surface,
                        (int(target_x - radius - 5), int(target_y - radius - 5))
                    )


def draw_enemy_weapon_animations(ctx, current_time, get_enemy_position_func):
    """Draw enemy weapon animations (phasers/torpedoes directed at player).

    Args:
        ctx: RenderContext with all necessary state
        current_time: Current game time in milliseconds
        get_enemy_position_func: Function to get enemy position
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    game_state = ctx.game_state
    systems = ctx.systems
    current_system = ctx.current_system

    # Determine actual player render position for accurate targeting
    player_render_pos = None
    if game_state.map_mode == 'system':
        if ctx.system_ship_anim_x is not None and ctx.system_ship_anim_y is not None:
            player_render_pos = (ctx.system_ship_anim_x, ctx.system_ship_anim_y)
        else:
            player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
            if player_obj:
                player_render_pos = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
    elif game_state.map_mode == 'sector':
        if (hasattr(game_state.animation, 'ship_anim_x') and
            game_state.animation.ship_anim_x is not None and
            game_state.animation.ship_anim_y is not None):
            player_render_pos = (game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)

    game_state.weapon_animation_manager.draw_enemy_weapon_animations(
        screen, current_time, hex_grid, player_render_pos
    )


def draw_system_planets(ctx, clock):
    """Draw planets orbiting stars in system view.

    Args:
        ctx: RenderContext with all necessary state
        clock: pygame.Clock for delta time calculation

    Returns:
        None (modifies planet_anim_state in place)
    """
    screen = ctx.screen
    hex_grid = ctx.hex_grid
    systems = ctx.systems
    current_system = ctx.current_system
    planet_orbits = ctx.planet_orbits
    planet_anim_state = ctx.planet_anim_state
    planet_images_assigned = ctx.planet_images_assigned
    planet_colors = ctx.planet_colors
    background_loader = ctx.background_loader

    # Animate and draw all planets associated with stars in this system
    planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]

    for orbit in planets_in_system:
        # Get star position in system coordinates
        star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
        if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
            star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
        else:
            star_px, star_py = hex_grid.get_hex_center(current_system[0], current_system[1])

        hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
        orbit_radius_px = orbit['hex_radius'] * hex_size
        key = (orbit['star'], orbit['planet'])

        # Update angle
        dt = clock.get_time() / 1000.0
        planet_anim_state[key] += orbit['speed'] * dt
        angle = planet_anim_state[key]

        planet_px = star_px + orbit_radius_px * math.cos(angle)
        planet_py = star_py + orbit_radius_px * math.sin(angle)

        planet_key = (orbit['star'], orbit['planet'])

        # Get or assign planet image
        if planet_key not in planet_images_assigned:
            planet_image = background_loader.get_random_planet_image()
            size_multiplier = random.uniform(1.0, 3.3)
            scaled_planet_image = None
            if planet_image:
                scaled_planet_image = background_loader.scale_planet_image(
                    planet_image, hex_grid.radius * 1.8, size_multiplier
                )
            planet_images_assigned[planet_key] = (planet_image, scaled_planet_image, size_multiplier)
        else:
            planet_image, scaled_planet_image, size_multiplier = planet_images_assigned[planet_key]

        # Draw planet
        if scaled_planet_image:
            image_rect = scaled_planet_image.get_rect()
            image_rect.center = (int(planet_px), int(planet_py))
            screen.blit(scaled_planet_image, image_rect)
        else:
            if planet_key not in planet_colors:
                planet_colors[planet_key] = get_planet_color()
            planet_color = planet_colors[planet_key]
            base_radius = hex_grid.radius * 1.8 * 0.6
            variable_radius = int(base_radius * size_multiplier)
            pygame.draw.circle(screen, planet_color, (int(planet_px), int(planet_py)), variable_radius)
