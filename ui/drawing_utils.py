"""
Drawing and rendering utilities for the Star Trek Tactical Game
"""
import random


def get_star_color():
    """Generate realistic star colors based on stellar classification."""
    star_colors = [
        (255, 255, 255),  # White (white dwarf, hot stars)
        (255, 254, 250),  # Blue-white
        (255, 244, 234),  # Yellow-white
        (255, 229, 206),  # Yellow (G-type like our Sun)
        (255, 204, 111),  # Orange
        (255, 178, 102),  # Orange-red
        (255, 154, 86),   # Red-orange
        (255, 128, 74),   # Red (M-type red dwarf)
    ]
    return random.choice(star_colors)


def get_planet_color():
    """Generate varied planet colors."""
    planet_colors = [
        (100, 149, 237),  # Cornflower blue (Earth-like)
        (255, 228, 181),  # Moccasin (desert world)
        (189, 183, 107),  # Dark khaki (rocky)
        (70, 130, 180),   # Steel blue (ice world)
        (244, 164, 96),   # Sandy brown (Mars-like)
        (176, 196, 222),  # Light steel blue (gas giant)
        (147, 112, 219),  # Medium purple (exotic)
        (188, 143, 143),  # Rosy brown
    ]
    return random.choice(planet_colors)
