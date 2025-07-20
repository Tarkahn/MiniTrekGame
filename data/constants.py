# Game Configuration Constants

MAX_TURNS = 1000  # Maximum turns allowed in a game.
STARTING_ENERGY = 1000  # Initial ship energy capacity.
# SHIELD_REGEN_RATE = 10  # Shield regeneration rate (per minute).
# Removed in favor of SHIELD_REGEN_RATE_PER_SECOND
WARP_ENERGY_COST = 10  # Energy per sector hex during warp.
SHIELD_ABSORPTION_PER_LEVEL = 10  # Damage absorbed by shields per level.
PHASER_COOLDOWN_SECONDS = 5  # Phaser cooldown duration.
KLINGON_DISRUPTOR_DAMAGE_MIN = 30  # Minimum Klingon disruptor damage.
KLINGON_DISRUPTOR_DAMAGE_MAX = 50  # Maximum Klingon disruptor damage.

# Ship Systems and Movement
PHASER_ENERGY_COST = 50
LOCAL_MOVEMENT_ENERGY_COST_PER_HEX = 5  # New constant for local movement
WARP_INITIATION_COST = 20  # from PRD

# Player Ship Systems
PLAYER_PHASER_POWER = 50
PLAYER_PHASER_RANGE = 9

# Energy Regeneration
ENERGY_REGEN_RATE_PER_TURN = 10  # Energy regenerated per turn

# Shield Systems
SHIELD_ENERGY_COST_PER_LEVEL = 5  # Energy consumed to activate shield

# Torpedo Systems
TORPEDO_ENERGY_COST = 100  # Energy consumed per torpedo fired
TORPEDO_MAX_POWER = 100  # Maximum damage a torpedo can deal

# Sensor Systems
SENSOR_ENERGY_COST_PER_SCAN = 10  # Energy consumed per scan operation

# Enemy Ship Weaponry
ENEMY_PHASER_POWER = 40
ENEMY_PHASER_RANGE = 7
ENEMY_TORPEDO_POWER = 80
ENEMY_TORPEDO_SPEED = 10
ENEMY_TORPEDO_ACCURACY = 0.7

# Critical Hit System
CRITICAL_HIT_CHANCE = 0.15  # 15% chance for a critical hit
CRITICAL_HIT_MULTIPLIER = 1.5  # 1.5x damage on critical hit

# Game State
INITIAL_GAME_STATE = {
}

# New constant for shield regeneration rate per second
SHIELD_REGEN_RATE_PER_SECOND = 5  # Example: 5 points per second

# Map grid size
GRID_ROWS = 20
GRID_COLS = 20

# Object counts
NUM_STARS = 30  # Reduced from 100 to allow more room for planets
NUM_PLANETS = 35  # Increased to ensure at least 1 planet per star (30) plus extras
NUM_STARBases = 1
NUM_ENEMY_SHIPS = 30
NUM_ANOMALIES = 1

# Placement rules
MIN_STAR_PLANET_DISTANCE = 6  # Minimum hexes between any star and planet

# --- System object limits ---
MAX_STARS_PER_SYSTEM = 2  # No more than 2 stars per system
MAX_PLANETS_PER_SYSTEM = 4  # No more than 4 planets per system
MAX_STARBases_PER_SYSTEM = 1  # Only 1 starbase per system

# UI and rendering constants
SCREEN_WIDTH = 1075
SCREEN_HEIGHT = 1408
HEX_RADIUS = 20
HEX_HEIGHT = 34  # Approximately 2 * radius * sin(60 degrees)
HEX_WIDTH = 40   # 2 * radius
MAP_WIDTH = 800
MAP_HEIGHT = 800
STAR_COLORS = (255, 255, 0)  # Yellow for stars
PLANET_COLORS = (0, 255, 0)  # Green for planets
STARBASE_COLOR = (0, 0, 255)  # Blue for starbases
ENEMY_COLOR = (255, 0, 0)     # Red for enemies
ANOMALY_COLOR = (255, 0, 255)  # Magenta for anomalies
PLAYER_COLOR = (0, 255, 255)  # Cyan for player
UI_HEIGHT = 200
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
