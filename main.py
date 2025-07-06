import sys
from ship.player_ship import PlayerShip
from data import constants

def print_menu():
    print("\n--- Star Trek Tactical Game (User Test Mode) ---")
    print("1. Move Ship")
    print("2. Fire Phasers (dummy target)")
    print("3. Show Status")
    print("4. Exit")

def show_status(player):
    print(f"\nShip: {player.name}")
    print(f"Hull: {player.hull_strength}/{player.max_hull_strength}")
    print(f"Shields: {player.shield_system.current_strength}/{player.shield_system.max_strength}")
    print(f"Energy: {player.warp_core_energy}/{player.max_warp_core_energy}")
    print(f"Position: {player.position}")

def main():
    player = PlayerShip(
        name="USS Test",
        max_shield_strength=100,
        hull_strength=1000,
        energy=1000,
        max_energy=1000,
        weapons=[],
        position=(0, 0)
    )

    while True:
        print_menu()
        choice = input("Choose an action: ").strip()
        if choice == "1":
            try:
                hexes = int(input("How many hexes to move? "))
                if hexes < 1:
                    print("Must move at least 1 hex.")
                    continue
                success = player.move_ship(hexes)
                if not success:
                    print("Move failed: Not enough energy.")
            except ValueError:
                print("Invalid input. Enter a number.")
        elif choice == "2":
            # Dummy target for now
            class DummyTarget:
                def apply_damage(self, dmg):
                    print(f"Dummy target took {dmg} damage.")
            dummy = DummyTarget()
            try:
                dist = int(input("Enter target distance (hexes): "))
                dmg = player.fire_phasers(dummy, target_distance=dist)
                if dmg == 0:
                    print("Phasers failed to fire (cooldown, out of range, or not enough energy).")
            except ValueError:
                print("Invalid input. Enter a number.")
        elif choice == "3":
            show_status(player)
        elif choice == "4":
            print("Exiting game. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main() 