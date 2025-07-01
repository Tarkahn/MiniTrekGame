from data import constants
from ship.player_ship import PlayerShip


def check_victory_condition(enemy_ships: list) -> bool:
    """
    Checks if the victory condition has been met.
    Victory condition: All Klingon (enemy) ships are destroyed.
    """
    return all(not ship.is_alive() for ship in enemy_ships) if enemy_ships else False


def check_defeat_condition(player_ship: PlayerShip, current_turn: int, surrendered: bool) -> bool:
    """
    Checks if any defeat condition has been met.
    Defeat conditions:
    1. Player ship hull strength is 0 or less.
    2. Turn limit exceeded.
    3. Life support failure (placeholder).
    4. Player surrenders.
    """
    if not player_ship.is_alive():
        print("Defeat: Your ship has been destroyed!")
        return True
    
    if current_turn >= constants.MAX_TURNS:
        print("Defeat: Turn limit exceeded!")
        return True
    
    # Placeholder for actual life support system check
    # if player_ship.life_support_failed(): 
    #     print("Defeat: Life support has failed!")
    #     return True

    if surrendered:
        print("Defeat: You have surrendered!")
        return True

    return False 


def display_notification(message: str, type: str = "info"):  # type can be "info", "victory", "defeat"
    """
    Displays a game notification to the player.
    """
    if type == "victory":
        print(f"\n--- VICTORY! ---\n{message}\n------------------\n")
    elif type == "defeat":
        print(f"\n--- DEFEAT! ---\n{message}\n------------------\n")
    else:
        print(f"\n--- NOTIFICATION ---\n{message}\n--------------------\n") 