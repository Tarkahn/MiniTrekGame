import os
import glob
import random
import logging
import pygame


class BackgroundAndStarLoader:
    """Manages loading and scaling of background, star, and planet images."""
    
    def __init__(self):
        self.star_images = {}
        self.planet_images = {}
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
        
        # Load star images
        stars_dir = os.path.join(assets_dir, 'stars')
        if os.path.exists(stars_dir):
            star_files = glob.glob(os.path.join(stars_dir, '*.jpg'))
            for star_file in star_files:
                star_name = os.path.splitext(os.path.basename(star_file))[0]
                try:
                    image = pygame.image.load(star_file)
                    self.star_images[star_name] = image
                    logging.debug(f"[STARS] Loaded star image: {star_name}")
                except Exception as e:
                    logging.error(f"[STARS] Failed to load {star_file}: {e}")
        else:
            logging.warning(f"[STARS] Stars directory not found: {stars_dir}")
        
        # Load planet images
        planets_dir = os.path.join(assets_dir, 'planets')
        if os.path.exists(planets_dir):
            planet_files = glob.glob(os.path.join(planets_dir, '*.jpg'))
            for planet_file in planet_files:
                planet_name = os.path.splitext(os.path.basename(planet_file))[0]
                try:
                    image = pygame.image.load(planet_file)
                    self.planet_images[planet_name] = image
                    logging.debug(f"[PLANETS] Loaded planet image: {planet_name}")
                except Exception as e:
                    logging.error(f"[PLANETS] Failed to load {planet_file}: {e}")
            logging.info(f"[PLANETS] Loaded {len(self.planet_images)} planet images for maximum variety")
        else:
            logging.warning(f"[PLANETS] Planets directory not found: {planets_dir}")
    
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
        """Get a random star image."""
        if self.star_images:
            return random.choice(list(self.star_images.values()))
        return None
    
    def get_random_planet_image(self):
        """Get a random planet image."""
        if self.planet_images:
            return random.choice(list(self.planet_images.values()))
        return None
    
    def get_star_image_by_name(self, name):
        """Get a specific star image by name."""
        return self.star_images.get(name)
    
    def scale_star_image(self, image, radius):
        """Scale star image to appropriate size for given radius."""
        if image:
            # Scale image to be roughly 2x the hex radius for proper coverage
            target_size = int(radius * 4)
            return pygame.transform.scale(image, (target_size, target_size))
        return None
    
    def get_planet_image_by_name(self, name):
        """Get a specific planet image by name."""
        return self.planet_images.get(name)
    
    def scale_planet_image(self, image, base_radius, size_multiplier=1.0):
        """Scale planet image to variable size based on multiplier."""
        if image:
            # Base size is 60% of hex radius (minimum), up to 2 hex widths (maximum)
            # size_multiplier ranges from 1.0 (minimum) to ~3.3 (2 hex widths)
            base_size = base_radius * 0.6  # Current minimum size
            target_size = int(base_size * size_multiplier)
            return pygame.transform.scale(image, (target_size, target_size))
        return None