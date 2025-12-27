"""
Geometry and distance utilities for hex grid calculations.

This module contains pure functions for geometric calculations that are
used across multiple modules (galaxy generation, combat, navigation).
"""


def hex_distance(a, b):
    """Calculate hex grid distance between two positions.

    Uses the cube coordinate system for accurate hex distance calculation.
    Works with offset coordinate tuples (q, r).

    Args:
        a: First position as (q, r) tuple
        b: Second position as (q, r) tuple

    Returns:
        int: The hex distance (number of hexes between positions)
    """
    dq = abs(a[0] - b[0])
    dr = abs(a[1] - b[1])
    ds = abs((-a[0] - a[1]) - (-b[0] - b[1]))
    return max(dq, dr, ds)


def hex_neighbors(q, r):
    """Get all 6 neighboring hexes for a given hex coordinate.

    Works with flat-topped hexes using offset coordinates.

    Args:
        q: Column coordinate
        r: Row coordinate

    Returns:
        list: List of 6 (q, r) tuples representing neighbor positions
    """
    if q % 2 == 0:  # Even column
        neighbors = [
            (q-1, r-1), (q-1, r),    # Left neighbors
            (q, r-1), (q, r+1),      # Top and bottom
            (q+1, r-1), (q+1, r)     # Right neighbors
        ]
    else:  # Odd column
        neighbors = [
            (q-1, r), (q-1, r+1),    # Left neighbors
            (q, r-1), (q, r+1),      # Top and bottom
            (q+1, r), (q+1, r+1)     # Right neighbors
        ]
    return neighbors


def point_distance(p1, p2):
    """Calculate Euclidean distance between two points.

    Args:
        p1: First point as (x, y) tuple
        p2: Second point as (x, y) tuple

    Returns:
        float: The Euclidean distance between the points
    """
    import math
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
