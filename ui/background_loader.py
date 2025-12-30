import os
import glob
import random
import logging
import pygame
import time
import math


class AnimatedImage:
    """Handles animated GIF files by extracting frames and cycling through them."""
    
    def __init__(self, gif_path, speed_multiplier=1.0):
        self.frames = []
        self.frame_durations = []
        self.current_frame = 0
        self.last_frame_time = time.time()
        self.is_animated = False
        self.speed_multiplier = speed_multiplier  # 1.0 = normal, 0.5 = half speed, 2.0 = double speed
        
        try:
            # Try to use PIL/Pillow for GIF frame extraction
            from PIL import Image
            
            with Image.open(gif_path) as img:
                # Check if it's actually animated
                if hasattr(img, 'is_animated') and img.is_animated:
                    self.is_animated = True
                    frame_count = img.n_frames
                    
                    for frame_num in range(frame_count):
                        img.seek(frame_num)
                        
                        # Get frame duration (in milliseconds)
                        duration = img.info.get('duration', 100)  # Default 100ms if not specified
                        # Apply speed multiplier (higher multiplier = slower animation)
                        adjusted_duration = (duration / 1000.0) * self.speed_multiplier
                        self.frame_durations.append(adjusted_duration)
                        
                        # Convert PIL image to pygame surface
                        frame_rgba = img.convert('RGBA')
                        frame_data = frame_rgba.tobytes()
                        frame_surface = pygame.image.fromstring(frame_data, frame_rgba.size, 'RGBA')
                        self.frames.append(frame_surface)
                        
                else:
                    # Single frame image, treat as static
                    static_frame = img.convert('RGBA')
                    frame_data = static_frame.tobytes()
                    frame_surface = pygame.image.fromstring(frame_data, static_frame.size, 'RGBA')
                    self.frames.append(frame_surface)
                    self.frame_durations.append(1.0)  # Arbitrary duration for static image
                    
        except (ImportError, Exception) as e:
            # Fallback: PIL not available or error occurred, load as static image
            logging.warning(f"Could not load animated GIF {gif_path}: {e}. Loading as static image.")
            try:
                static_surface = pygame.image.load(gif_path)
                self.frames.append(static_surface)
                self.frame_durations.append(1.0)
            except Exception as e2:
                logging.error(f"Failed to load image {gif_path}: {e2}")
    
    def get_current_frame(self):
        """Get the current frame, updating animation if needed."""
        if not self.frames:
            return None
            
        if not self.is_animated or len(self.frames) == 1:
            return self.frames[0]
        
        # Check if it's time to advance to the next frame
        current_time = time.time()
        if current_time - self.last_frame_time >= self.frame_durations[self.current_frame]:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = current_time
        
        return self.frames[self.current_frame]


class BackgroundAndStarLoader:
    """Manages loading and scaling of background, star, planet, and anomaly images."""

    def __init__(self):
        self.star_images = {}
        self.planet_images = {}
        self.anomaly_images = {}
        self.starbase_image = None
        self.player_ship_image = None
        self.enemy_ship_image = None
        self.background_image = None
        self.scaled_background = None
        self.load_images()
    
    def load_images(self):
        """Load background image, all star images, and all planet images."""
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        
        # Load background image
        bg_path = os.path.join(assets_dir, 'MapBackground.jpg')
        if os.path.exists(bg_path):
            try:
                self.background_image = pygame.image.load(bg_path)
                logging.debug(f"[BACKGROUND] Loaded background image: MapBackground.jpg")
            except Exception as e:
                logging.error(f"[BACKGROUND] Failed to load background: {e}")
        else:
            logging.warning(f"[BACKGROUND] Background image not found: {bg_path}")
        
        # Load starbase image
        starbase_path = os.path.join(assets_dir, 'starbase2.png')
        if os.path.exists(starbase_path):
            try:
                self.starbase_image = pygame.image.load(starbase_path)
                logging.debug(f"[STARBASE] Loaded starbase image: starbase2.png")
            except Exception as e:
                logging.error(f"[STARBASE] Failed to load starbase image: {e}")
        else:
            logging.warning(f"[STARBASE] Starbase image not found: {starbase_path}")
        
        # Load player ship image
        player_ship_path = os.path.join(assets_dir, 'playerShip.png')
        if os.path.exists(player_ship_path):
            try:
                self.player_ship_image = pygame.image.load(player_ship_path)
                logging.debug(f"[SHIP] Loaded player ship image: playerShip.png")
            except Exception as e:
                logging.error(f"[SHIP] Failed to load player ship image: {e}")
        else:
            logging.warning(f"[SHIP] Player ship image not found: {player_ship_path}")
        
        # Load enemy ship image
        enemy_ship_path = os.path.join(assets_dir, 'enemyShip.png')
        if os.path.exists(enemy_ship_path):
            try:
                self.enemy_ship_image = pygame.image.load(enemy_ship_path)
                logging.debug(f"[SHIP] Loaded enemy ship image: enemyShip.png")
            except Exception as e:
                logging.error(f"[SHIP] Failed to load enemy ship image: {e}")
        else:
            logging.warning(f"[SHIP] Enemy ship image not found: {enemy_ship_path}")
        
        # Load star images (supports .jpg, .jpeg, .png, .bmp, .gif)
        stars_dir = os.path.join(assets_dir, 'stars')
        if os.path.exists(stars_dir):
            # Support multiple image formats
            star_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
                star_files.extend(glob.glob(os.path.join(stars_dir, ext)))
            
            for star_file in star_files:
                star_name = os.path.splitext(os.path.basename(star_file))[0]
                file_ext = os.path.splitext(star_file)[1].lower()
                try:
                    if file_ext == '.gif':
                        # Load as animated image with slow rotation for stars
                        star_speed = 3.0  # Make stars rotate 3x slower than original GIF
                        animated_image = AnimatedImage(star_file, speed_multiplier=star_speed)
                        if animated_image.frames:
                            self.star_images[star_name] = animated_image
                            logging.debug(f"[STARS] Loaded animated star: {star_name} ({len(animated_image.frames)} frames, {star_speed}x slower)")
                        else:
                            logging.error(f"[STARS] Failed to load animated star: {star_file}")
                    else:
                        # Load as static image
                        image = pygame.image.load(star_file)
                        self.star_images[star_name] = image
                        logging.debug(f"[STARS] Loaded star image: {star_name} ({file_ext})")
                except Exception as e:
                    logging.error(f"[STARS] Failed to load {star_file}: {e}")
        else:
            logging.warning(f"[STARS] Stars directory not found: {stars_dir}")
        
        # Load planet images (supports .jpg, .jpeg, .png, .bmp, .gif)
        planets_dir = os.path.join(assets_dir, 'planets')
        if os.path.exists(planets_dir):
            # Support multiple image formats
            planet_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
                planet_files.extend(glob.glob(os.path.join(planets_dir, ext)))
            
            for planet_file in planet_files:
                planet_name = os.path.splitext(os.path.basename(planet_file))[0]
                file_ext = os.path.splitext(planet_file)[1].lower()
                try:
                    if file_ext == '.gif':
                        # Load as animated image with slow rotation for planets
                        planet_speed = 2.0  # Make planets rotate 2x slower than original GIF
                        animated_image = AnimatedImage(planet_file, speed_multiplier=planet_speed)
                        if animated_image.frames:
                            self.planet_images[planet_name] = animated_image
                            logging.debug(f"[PLANETS] Loaded animated planet: {planet_name} ({len(animated_image.frames)} frames, {planet_speed}x slower)")
                        else:
                            logging.error(f"[PLANETS] Failed to load animated planet: {planet_file}")
                    else:
                        # Load as static image
                        image = pygame.image.load(planet_file)
                        self.planet_images[planet_name] = image
                        logging.debug(f"[PLANETS] Loaded planet image: {planet_name} ({file_ext})")
                except Exception as e:
                    logging.error(f"[PLANETS] Failed to load {planet_file}: {e}")
            logging.info(f"[PLANETS] Loaded {len(self.planet_images)} planet images for maximum variety")
        else:
            logging.warning(f"[PLANETS] Planets directory not found: {planets_dir}")

        # Load anomaly images (supports .jpg, .jpeg, .png, .bmp, .gif, .webp)
        anomalies_dir = os.path.join(assets_dir, 'anomalies')
        if os.path.exists(anomalies_dir):
            # Support multiple image formats
            anomaly_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.webp']:
                anomaly_files.extend(glob.glob(os.path.join(anomalies_dir, ext)))

            for anomaly_file in anomaly_files:
                anomaly_name = os.path.splitext(os.path.basename(anomaly_file))[0]
                file_ext = os.path.splitext(anomaly_file)[1].lower()
                # Skip if we already have this anomaly (prefer .webp over .jpg)
                if anomaly_name in self.anomaly_images:
                    continue
                try:
                    if file_ext == '.gif':
                        # Load as animated image
                        anomaly_speed = 1.5  # Slightly slower than original
                        animated_image = AnimatedImage(anomaly_file, speed_multiplier=anomaly_speed)
                        if animated_image.frames:
                            self.anomaly_images[anomaly_name] = animated_image
                            logging.debug(f"[ANOMALIES] Loaded animated anomaly: {anomaly_name}")
                        else:
                            logging.error(f"[ANOMALIES] Failed to load animated anomaly: {anomaly_file}")
                    else:
                        # Load as static image
                        image = pygame.image.load(anomaly_file)
                        self.anomaly_images[anomaly_name] = image
                        logging.debug(f"[ANOMALIES] Loaded anomaly image: {anomaly_name} ({file_ext})")
                except Exception as e:
                    logging.error(f"[ANOMALIES] Failed to load {anomaly_file}: {e}")
            logging.info(f"[ANOMALIES] Loaded {len(self.anomaly_images)} anomaly images")
        else:
            logging.warning(f"[ANOMALIES] Anomalies directory not found: {anomalies_dir}")

    def get_scaled_background(self, width, height):
        """Get background image scaled to fit the map area."""
        if self.background_image and (self.scaled_background is None or 
                                     self.scaled_background.get_size() != (width, height)):
            try:
                self.scaled_background = pygame.transform.scale(self.background_image, (width, height))
                logging.debug(f"[BACKGROUND] Scaled background to {width}x{height}")
            except Exception as e:
                logging.error(f"[BACKGROUND] Failed to scale background: {e}")
                return None
        return self.scaled_background
    
    def get_random_star_image(self):
        """Get a random star image (handles both static and animated)."""
        if self.star_images:
            star_obj = random.choice(list(self.star_images.values()))
            if isinstance(star_obj, AnimatedImage):
                return star_obj.get_current_frame()
            return star_obj
        return None
    
    def get_random_planet_image(self):
        """Get a random planet image (handles both static and animated)."""
        if self.planet_images:
            planet_obj = random.choice(list(self.planet_images.values()))
            if isinstance(planet_obj, AnimatedImage):
                return planet_obj.get_current_frame()
            return planet_obj
        return None
    
    def get_star_image_by_name(self, name):
        """Get a specific star image by name (handles both static and animated)."""
        star_obj = self.star_images.get(name)
        if isinstance(star_obj, AnimatedImage):
            return star_obj.get_current_frame()
        return star_obj
    
    def scale_star_image(self, image, radius):
        """Scale star image to appropriate size for given radius."""
        if image:
            # Scale image to be roughly 2x the hex radius for proper coverage
            target_size = int(radius * 4)
            return pygame.transform.scale(image, (target_size, target_size))
        return None
    
    def get_planet_image_by_name(self, name):
        """Get a specific planet image by name (handles both static and animated)."""
        planet_obj = self.planet_images.get(name)
        if isinstance(planet_obj, AnimatedImage):
            return planet_obj.get_current_frame()
        return planet_obj
    
    def scale_planet_image(self, image, base_radius, size_multiplier=1.0):
        """Scale planet image to variable size based on multiplier."""
        if image:
            # Base size is 60% of hex radius (minimum), up to 2 hex widths (maximum)
            # size_multiplier ranges from 1.0 (minimum) to ~3.3 (2 hex widths)
            base_size = base_radius * 0.6  # Current minimum size
            target_size = int(base_size * size_multiplier)
            return pygame.transform.scale(image, (target_size, target_size))
        return None

    def get_random_anomaly_image(self):
        """Get a random anomaly image (handles both static and animated)."""
        if self.anomaly_images:
            anomaly_obj = random.choice(list(self.anomaly_images.values()))
            if isinstance(anomaly_obj, AnimatedImage):
                return anomaly_obj.get_current_frame()
            return anomaly_obj
        return None

    def get_anomaly_image_by_name(self, name):
        """Get a specific anomaly image by name (handles both static and animated)."""
        anomaly_obj = self.anomaly_images.get(name)
        if isinstance(anomaly_obj, AnimatedImage):
            return anomaly_obj.get_current_frame()
        return anomaly_obj

    def get_anomaly_names(self):
        """Get list of all available anomaly image names."""
        return list(self.anomaly_images.keys())

    def scale_anomaly_image(self, image, base_radius, size_multiplier=1.5):
        """Scale anomaly image to appropriate size.

        Args:
            image: The anomaly image to scale
            base_radius: The hex grid radius
            size_multiplier: Size multiplier (default 1.5 for medium visibility)

        Returns:
            Scaled pygame surface
        """
        if image:
            # Anomalies are slightly larger than planets for visual impact
            base_size = base_radius * 1.2
            target_size = int(base_size * size_multiplier)
            return pygame.transform.scale(image, (target_size, target_size))
        return None

    def get_starbase_image(self):
        """Get the starbase image."""
        return self.starbase_image
    
    def scale_starbase_image(self, image, radius):
        """Scale starbase image so docking pads align with adjacent hex centers.
        
        The starbase2.png has 6 docking pads arranged in a hexagonal pattern around
        a central hub. This scaling ensures each pad aligns with an adjacent hex center.
        
        For flat-topped hexes:
        - Adjacent hex centers are 1.5 * radius apart horizontally
        - Adjacent hex centers are sqrt(3) * radius apart vertically
        - The 6 pads form a perfect hexagon around the center
        
        Args:
            image: The starbase image to scale
            radius: The hex grid radius
            
        Returns:
            Scaled pygame surface with pads aligned to hex centers
        """
        if image:
            import math
            
            # Distance from center to adjacent hex center (hex spacing)
            # For a hex grid, the distance to each of the 6 surrounding hexes is:
            # - Horizontal neighbors: 1.5 * radius
            # - Diagonal neighbors: sqrt(3) * radius  
            # We want the starbase pads to align with the 6 surrounding hexes
            
            # The starbase image shows pads at roughly the same distance from center
            # We need to scale so that the pad-to-center distance in the image
            # matches the hex spacing in the game
            
            # For flat-topped hexes, the distance to the 6 surrounding hexes varies:
            # - East/West neighbors: 1.5 * radius  
            # - NE/NW/SE/SW neighbors: sqrt(3) * radius ≈ 1.732 * radius
            # We'll use the average for balanced pad positioning
            avg_hex_spacing = radius * 1.6  # Compromise between 1.5 and 1.732
            
            # The starbase2.png shows pads positioned at approximately 45% of the image radius
            # from the center, so we scale to make 45% of the scaled image = hex spacing
            pad_ratio_in_image = 0.45  # Measured ratio from starbase2.png
            required_radius = avg_hex_spacing / pad_ratio_in_image
            target_size = int(required_radius * 2)  # Full diameter
            
            # Ensure the starbase covers exactly the right area for docking
            # Make it large enough to be impressive but not overwhelming
            target_size = max(target_size, int(radius * 7))  # Minimum impressive size
            
            return pygame.transform.scale(image, (target_size, target_size))
        return None
    
    def get_player_ship_image(self):
        """Get the player ship image."""
        return self.player_ship_image
    
    def get_enemy_ship_image(self):
        """Get the enemy ship image."""
        return self.enemy_ship_image
    
    def scale_ship_image(self, image, radius):
        """Scale ship image to appropriate size for game display."""
        if image:
            # Scale ship images to be about 1.5x the hex radius for good visibility
            target_size = int(radius * 1.5)
            return pygame.transform.scale(image, (target_size, target_size))
        return None
    
    def rotate_ship_image(self, image, angle_degrees):
        """Rotate ship image by the given angle in degrees."""
        if image:
            # Rotate the image - pygame rotates counter-clockwise
            return pygame.transform.rotate(image, angle_degrees)
        return None
    
    def calculate_movement_angle(self, start_pos, end_pos):
        """Calculate the angle of movement from start to end position in degrees.
        Returns angle where 0° = North (up), 90° = East (right), etc."""
        if start_pos == end_pos:
            return 0  # No movement, default to North
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        # Calculate angle in radians from positive X axis
        angle_rad = math.atan2(dy, dx)
        # Convert to degrees
        angle_deg = math.degrees(angle_rad)
        
        # In pygame/screen coordinates:
        # - Positive X = Right (East)
        # - Positive Y = Down (South) 
        # - atan2(dy, dx) gives: East = 0°, South = 90°, West = 180°/-180°, North = -90°
        
        # We need to convert to rotation where:
        # - 0° = North (ship pointing up)
        # - 90° = East (ship pointing right)  
        # - 180° = South (ship pointing down)
        # - 270° = West (ship pointing left)
        
        # Convert from atan2 angles to our ship rotation angles
        # atan2 gives: East=0°, Northeast=-45°, North=-90°, Northwest=-135°, West=180°, Southwest=135°, South=90°, Southeast=45°
        # We want: North=0°, Northeast=45°, East=90°, Southeast=135°, South=180°, Southwest=225°, West=270°, Northwest=315°
        
        # The conversion is: rotation = -angle_deg + 90
        # Northeast: atan2=-45° → rotation = -(-45°) + 90° = 45° ✓
        # East: atan2=0° → rotation = -0° + 90° = 90° ✓  
        # Southeast: atan2=45° → rotation = -45° + 90° = 45° ✗ should be 135°
        
        # Since screen Y is inverted, we need to flip dy sign in the atan2 call
        corrected_angle = math.degrees(math.atan2(-dy, dx))  # Flip Y to match normal coordinate system
        rotation_angle = corrected_angle + 90
        
        # Add 180° to flip ship orientation (ship image has nose pointing down, we want nose pointing in direction of movement)
        rotation_angle += 180
        
        # Normalize to 0-360 range
        while rotation_angle < 0:
            rotation_angle += 360
        while rotation_angle >= 360:
            rotation_angle -= 360
            
        return rotation_angle
    
    def interpolate_rotation(self, current_angle, target_angle, rotation_speed, delta_time):
        """Smoothly interpolate between current and target rotation angles.
        
        Args:
            current_angle: Current rotation angle in degrees (0-360)
            target_angle: Target rotation angle in degrees (0-360)
            rotation_speed: Rotation speed in degrees per second
            delta_time: Time elapsed since last frame in seconds
            
        Returns:
            New current angle after interpolation
        """
        if current_angle == target_angle:
            return current_angle
        
        # Calculate the shortest rotation direction
        diff = target_angle - current_angle
        
        # Wrap around 360 degrees to find shortest path
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        # Calculate rotation step for this frame
        max_rotation = rotation_speed * delta_time
        
        # Apply rotation step
        if abs(diff) <= max_rotation:
            # Close enough - snap to target
            return target_angle
        else:
            # Rotate toward target
            rotation_step = max_rotation if diff > 0 else -max_rotation
            new_angle = current_angle + rotation_step
            
            # Normalize to 0-360 range
            while new_angle < 0:
                new_angle += 360
            while new_angle >= 360:
                new_angle -= 360
                
            return new_angle
    
    def is_rotation_complete(self, current_angle, target_angle, tolerance=5.0):
        """Check if current rotation is close enough to target rotation.
        
        Args:
            current_angle: Current rotation angle in degrees (0-360)
            target_angle: Target rotation angle in degrees (0-360)
            tolerance: Acceptable difference in degrees
            
        Returns:
            True if rotation is within tolerance of target
        """
        # Calculate the shortest rotation difference
        diff = target_angle - current_angle
        
        # Wrap around 360 degrees to find shortest path
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        return abs(diff) <= tolerance