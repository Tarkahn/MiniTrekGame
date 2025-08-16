# Game Configuration Constants

MAX_TURNS = 1000  # Maximum turns allowed in a game.
STARTING_ENERGY = 1000  # Initial ship energy capacity.
# SHIELD_REGEN_RATE = 10  # Shield regeneration rate (per minute).
# Removed in favor of SHIELD_REGEN_RATE_PER_SECOND
WARP_ENERGY_COST = 3  # Energy per sector hex during warp (reduced for gameplay balance)
SHIELD_ABSORPTION_PER_LEVEL = 10  # Damage absorbed by shields per level.
PHASER_COOLDOWN_SECONDS = 4  # PRD: 4s real-time cooldown (reduced for better gameplay)
KLINGON_DISRUPTOR_DAMAGE_MIN = 30  # Minimum Klingon disruptor damage.
KLINGON_DISRUPTOR_DAMAGE_MAX = 50  # Maximum Klingon disruptor damage.

# Ship Systems and Movement (Balanced for Gameplay)
PHASER_ENERGY_COST = 5  # PRD: 5 units per shot
LOCAL_MOVEMENT_ENERGY_COST_PER_HEX = 5  # Energy cost for impulse movement within systems
WARP_INITIATION_COST = 5  # Warp initiation cost (reduced for gameplay balance)

# Player Ship Systems (PRD Compliant)
PLAYER_PHASER_POWER = 5   # Base damage before distance modifiers (balanced for shield combat)
PLAYER_PHASER_RANGE = 18  # Extended range for tactical positioning

# Ship Defense Systems
PLAYER_SHIELD_CAPACITY = 75   # Player ship shield strength
ENEMY_SHIELD_CAPACITY = 75    # Enemy ship shield strength  
PLAYER_HULL_STRENGTH = 100    # Player ship hull integrity
ENEMY_HULL_STRENGTH = 100     # Enemy ship hull integrity

# Power Allocation System Defaults (0-9 scale)
DEFAULT_PHASER_POWER = 5      # Default phaser power allocation
DEFAULT_SHIELD_POWER = 5      # Default shield power allocation
DEFAULT_ENGINE_POWER = 5      # Default engine power (warp/impulse)
DEFAULT_SENSOR_POWER = 5      # Default sensor power allocation
DEFAULT_LIFE_SUPPORT_POWER = 9  # Default life support (critical system)
MAX_TOTAL_POWER = 36          # Maximum total power across tactical systems (4 systems × 9 max)

# Phaser Distance-Based Damage System
PHASER_CLOSE_RANGE = 3      # Close range threshold (0-3 hexes)
PHASER_MEDIUM_RANGE = 9     # Medium range threshold (4-9 hexes)
PHASER_CLOSE_MULTIPLIER = 1.5   # 150% damage at close range (high risk/reward)
PHASER_MEDIUM_MULTIPLIER = 1.0  # 100% damage at medium range (standard)
PHASER_LONG_MULTIPLIER = 0.6    # 60% damage at long range (10-18 hexes)

# Energy Regeneration
ENERGY_REGEN_RATE_PER_TURN = 15  # Energy regenerated per turn (increased for gameplay balance)

# Shield Systems (PRD Compliant)
SHIELD_ENERGY_COST_PER_LEVEL = 10  # PRD: Each level costs energy to maintain
SHIELD_REGEN_RATE_PER_MINUTE = 10  # PRD: 10 units per minute real-time

# Torpedo Systems (PRD Compliant)
TORPEDO_ENERGY_COST = 1  # PRD: 1 torpedo per shot (uses ammo, not energy)
TORPEDO_MAX_POWER = 100  # Maximum damage a torpedo can deal
PLAYER_TORPEDO_POWER = 80  # Player torpedo damage
PLAYER_TORPEDO_SPEED = 12  # Player torpedo speed
PLAYER_TORPEDO_ACCURACY = 0.85  # Player torpedo accuracy (85%)

# Torpedo Proximity Explosion System
TORPEDO_EXPLOSION_RADIUS = 3  # Maximum hex distance for explosion damage
TORPEDO_DIRECT_HIT_MULTIPLIER = 2.0  # Full damage multiplier for direct hit (hex 0)
TORPEDO_PROXIMITY_DAMAGE_FALLOFF = 0.6  # Damage falloff per hex distance
TORPEDO_EXPLOSION_ANIMATION_WAVES = 6  # Number of expanding visual waves
TORPEDO_EXPLOSION_WAVE_DELAY = 80  # Milliseconds between wave expansions

# Sensor Systems (PRD Compliant)
SHORT_RANGE_SCAN_COST = 5   # PRD: 5 energy units
LONG_RANGE_SCAN_COST = 20   # PRD: 20 energy units
SENSOR_ENERGY_COST_PER_SCAN = 5  # Backward compatibility

# Enemy Ship Weaponry
ENEMY_PHASER_POWER = 40
ENEMY_PHASER_RANGE = 7
ENEMY_TORPEDO_POWER = 80
ENEMY_TORPEDO_SPEED = 10
ENEMY_TORPEDO_ACCURACY = 0.7

# Critical Hit System (PRD Compliant)
CRITICAL_HIT_CHANCE = 0.15  # 15% base chance for a critical hit
CRITICAL_HIT_CHANCE_SHIELDS_DOWN = 0.10  # PRD: 10% chance when shields are down
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
MAX_ENEMIES_PER_SYSTEM = 2  # Maximum enemy ships per system for better distribution

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
