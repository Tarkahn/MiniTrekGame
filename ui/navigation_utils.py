"""
Navigation utilities for the Star Trek Tactical Game.

This module re-exports hex utilities from hex_utils for backwards compatibility.
"""
from ui.hex_utils import get_hex_neighbors, get_star_hexes, get_planet_hexes, is_hex_blocked

__all__ = ['get_hex_neighbors', 'get_star_hexes', 'get_planet_hexes', 'is_hex_blocked']
