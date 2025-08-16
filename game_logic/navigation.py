from ship.base_ship import BaseShip
from data.constants import LOCAL_MOVEMENT_ENERGY_COST_PER_HEX, WARP_INITIATION_COST, WARP_ENERGY_COST

def move_ship_local(ship: BaseShip, target_position: tuple) -> bool:
    """
    Calculates and applies local movement for a ship towards a target position.
    Consumes energy based on distance.
    Returns True if movement is possible and energy is sufficient, False otherwise.
    """
    current_x, current_y = ship.position
    target_x, target_y = target_position

    # Calculate raw distance (Manhattan distance for hex grid approximation for now)
    # Actual hex distance might be more complex, but this serves as a placeholder for energy cost.
    dx = abs(target_x - current_x)
    dy = abs(target_y - current_y)
    distance = max(dx, dy) # Simple approximation for hex grid distance

    if distance == 0:
        return True

    energy_cost = distance * LOCAL_MOVEMENT_ENERGY_COST_PER_HEX # Assuming LOCAL_MOVEMENT_ENERGY_COST_PER_HEX is a constant

    if not ship.consume_energy(energy_cost):
        print(f"Insufficient energy for {ship.name} to move {distance} hexes.")
        return False

    # For now, simply update the ship's position to the target.
    # Later: more granular movement, pathfinding, obstacle avoidance.
    ship.position = target_position
    return True

def warp_to_sector(ship: BaseShip, sectors_to_travel: int) -> bool:
    """
    Handles warp travel for a ship to a new sector.
    Consumes a flat initiation cost plus energy per sector traveled.
    Returns True if warp is successful and energy is sufficient, False otherwise.
    """
    initiation_cost = WARP_INITIATION_COST
    energy_per_sector = WARP_ENERGY_COST
    total_energy_cost = initiation_cost + (sectors_to_travel * energy_per_sector)

    if not ship.consume_energy(total_energy_cost):
        print(f"Insufficient energy for {ship.name} to warp {sectors_to_travel} sectors.")
        return False

    # In a full game, this would involve updating the galaxy map position
    # and potentially loading a new sector map.
    print(f"{ship.name} initiated warp travel for {sectors_to_travel} sectors. Energy remaining: {ship.warp_core_energy}")
    return True 