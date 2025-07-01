# Game Configuration Constants

MAX_TURNS = 1000  # Maximum turns allowed.
STARTING_ENERGY = 1000  # Initial ship energy capacity.
SHIELD_REGEN_RATE = 10  # Shield regeneration rate (per minute).
WARP_ENERGY_COST = 10  # Energy per sector hex during warp.
SHIELD_ABSORPTION_PER_LEVEL = 10  # Damage absorbed by shields per level.
PHASER_COOLDOWN_SECONDS = 5  # Phaser cooldown duration.
KLINGON_DISRUPTOR_DAMAGE_MIN = 30  # Minimum Klingon disruptor damage.
KLINGON_DISRUPTOR_DAMAGE_MAX = 50  # Maximum Klingon disruptor damage.

# Ship Systems and Movement
PHASER_ENERGY_COST = 50
LOCAL_MOVEMENT_ENERGY_COST_PER_HEX = 5  # New constant for local movement energy cost
WARP_INITIATION_COST = 20  # from PRD

# Energy Regeneration
ENERGY_REGEN_RATE_PER_TURN = 10  # Energy regenerated per turn

# Game State
INITIAL_GAME_STATE = {
}