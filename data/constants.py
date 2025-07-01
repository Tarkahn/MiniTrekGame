# Game Configuration Constants

MAX_TURNS = 1000  # Maximum turns allowed in a game. This is a defeat condition.
STARTING_ENERGY = 1000  # Initial ship energy capacity.
# SHIELD_REGEN_RATE = 10  # Shield regeneration rate (per minute). -- Removed in favor of SHIELD_REGEN_RATE_PER_SECOND
WARP_ENERGY_COST = 10  # Energy per sector hex during warp.
SHIELD_ABSORPTION_PER_LEVEL = 10  # Damage absorbed by shields per level.
PHASER_COOLDOWN_SECONDS = 5  # Phaser cooldown duration.
KLINGON_DISRUPTOR_DAMAGE_MIN = 30  # Minimum Klingon disruptor damage.
KLINGON_DISRUPTOR_DAMAGE_MAX = 50  # Maximum Klingon disruptor damage.

# Ship Systems and Movement
PHASER_ENERGY_COST = 50
LOCAL_MOVEMENT_ENERGY_COST_PER_HEX = 5  # New constant for local movement energy cost
WARP_INITIATION_COST = 20  # from PRD

# Player Ship Systems
PLAYER_PHASER_POWER = 50
PLAYER_PHASER_RANGE = 9

# Energy Regeneration
ENERGY_REGEN_RATE_PER_TURN = 10  # Energy regenerated per turn

# Shield Systems
SHIELD_ENERGY_COST_PER_LEVEL = 5  # Energy consumed to activate/maintain one level of shield

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
