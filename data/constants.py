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
PHASER_DAMAGE_PER_POWER_LEVEL = 3  # Damage multiplier per power allocation level
PLAYER_PHASER_RANGE = 18  # Extended range for tactical positioning
PHASER_RANGE = 18  # General phaser range (same as player)
PHASER_RANGE_PENALTY = 3  # Damage reduction per hex distance

# Torpedo System
STARTING_TORPEDO_COUNT = 10    # Number of torpedoes ship starts with
MAX_TORPEDO_CAPACITY = 10      # Maximum torpedoes ship can carry

# Ship Defense Systems
PLAYER_SHIELD_CAPACITY = 75   # Player ship shield strength
ENEMY_SHIELD_CAPACITY = 75    # Enemy ship shield strength  
PLAYER_HULL_STRENGTH = 100    # Player ship hull integrity
ENEMY_HULL_STRENGTH = 100     # Enemy ship hull integrity

# Power Allocation System Defaults (0-9 scale)
DEFAULT_PHASER_POWER = 5      # Default phaser power allocation
DEFAULT_SHIELD_POWER = 5      # Default shield power allocation
DEFAULT_ENGINE_POWER = 5      # Default engine power (warp/impulse)
DEFAULT_LIFE_SUPPORT_POWER = 9  # Default life support (critical system)
MAX_TOTAL_POWER = 27          # Maximum total power across tactical systems (3 systems × 9 max)

# Phaser Distance-Based Damage System
PHASER_CLOSE_RANGE = 3      # Close range threshold (0-3 hexes)
PHASER_MEDIUM_RANGE = 9     # Medium range threshold (4-9 hexes)
PHASER_CLOSE_MULTIPLIER = 1.5   # 150% damage at close range (high risk/reward)
PHASER_MEDIUM_MULTIPLIER = 1.0  # 100% damage at medium range (standard)
PHASER_LONG_MULTIPLIER = 0.6    # 60% damage at long range (10-18 hexes)

# Energy Regeneration
ENERGY_REGEN_RATE_PER_TURN = 15  # Energy regenerated per turn (increased for gameplay balance)

# Shield Systems (PRD Compliant)
SHIELD_ENERGY_COST_PER_LEVEL = 3  # Reduced for better gameplay balance - each level costs 3 energy/sec to maintain
SHIELD_REGEN_RATE_PER_MINUTE = 30  # PRD: 30 units per minute real-time (faster for gameplay)

# Torpedo Systems (PRD Compliant)
TORPEDO_ENERGY_COST = 1  # PRD: 1 torpedo per shot (uses ammo, not energy)
TORPEDO_MAX_POWER = 100  # Maximum damage a torpedo can deal
TORPEDO_DAMAGE = 80  # Standard torpedo damage
TORPEDO_RANGE = 30  # Torpedo range in hexes (longer than phasers)
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

# Enemy Ship Weaponry (Balanced for fair gameplay)
ENEMY_PHASER_POWER = 4  # Reduced from 40 to 4 for balanced combat (same as player base)
ENEMY_PHASER_RANGE = 7
ENEMY_TORPEDO_POWER = 60  # Reduced from 80 to 60 for balance
ENEMY_TORPEDO_SPEED = 10
ENEMY_TORPEDO_ACCURACY = 0.7
ENEMY_WEAPON_COOLDOWN_SECONDS = 3.0  # Minimum seconds between enemy weapon shots

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
NUM_STARBases = 3
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

# ====================================================================
# KLINGON AI BEHAVIOR PARAMETERS - Randomizable for Dynamic Enemies
# ====================================================================

# Movement Behavior Parameters
# ----------------------------
KLINGON_MOVEMENT_SPEED_MIN = 0.8    # Minimum movement speed multiplier (80% of base speed)
KLINGON_MOVEMENT_SPEED_MAX = 1.5    # Maximum movement speed multiplier (150% of base speed)

KLINGON_MOVE_DISTANCE_MIN = 1       # Minimum hexes per move
KLINGON_MOVE_DISTANCE_MAX = 4       # Maximum hexes per move

KLINGON_MOVE_VARIABILITY_MIN = 0.2  # Low variability = consistent movement distances
KLINGON_MOVE_VARIABILITY_MAX = 0.9  # High variability = very random movement distances

# Combat Aggression Parameters
# ----------------------------
KLINGON_AGGRESSION_MIN = 0.8        # Highly aggressive baseline (80% aggression)
KLINGON_AGGRESSION_MAX = 0.99       # Extremely aggressive, always attacks (99% aggression)

KLINGON_ATTACK_RANGE_MIN = 2        # Prefers close combat (minimum preferred attack range)
KLINGON_ATTACK_RANGE_MAX = 10       # Reduced max range to encourage closer combat

KLINGON_CLOSING_TENDENCY_MIN = 0.6  # Strong tendency to close in on player (60% tendency)
KLINGON_CLOSING_TENDENCY_MAX = 0.95 # Extremely aggressive closing behavior (95% tendency)

# Weapon System Parameters
# ------------------------
KLINGON_WEAPON_POWER_MIN = 5        # Higher minimum weapon power allocation
KLINGON_WEAPON_POWER_MAX = 9        # Maximum weapon power allocation

KLINGON_FIRING_FREQUENCY_MIN = 0.6   # Very aggressive firing (60% chance per turn)
KLINGON_FIRING_FREQUENCY_MAX = 0.9   # Extremely high firing rate (90% chance per turn)

KLINGON_WEAPON_ACCURACY_MIN = 0.5   # Poor marksmanship (50% accuracy)
KLINGON_WEAPON_ACCURACY_MAX = 0.9   # Expert marksmanship (90% accuracy)

# Tactical Intelligence Parameters
# ---------------------------------
KLINGON_FLANKING_TENDENCY_MIN = 0.0 # Never attempts flanking maneuvers
KLINGON_FLANKING_TENDENCY_MAX = 0.8 # Frequently attempts flanking maneuvers

KLINGON_EVASION_SKILL_MIN = 0.2     # Poor evasion patterns (20% effectiveness)
KLINGON_EVASION_SKILL_MAX = 0.8     # Excellent evasion patterns (80% effectiveness)

KLINGON_TACTICAL_PATIENCE_MIN = 0   # Attacks immediately, no waiting
KLINGON_TACTICAL_PATIENCE_MAX = 0   # No patience - immediate engagement

# Defensive Behavior Parameters  
# -----------------------------
KLINGON_RETREAT_THRESHOLD_MIN = 0.1 # Fights to the death (retreats at 10% health)
KLINGON_RETREAT_THRESHOLD_MAX = 0.7 # Cowardly, retreats early (retreats at 70% health)

KLINGON_SHIELD_PRIORITY_MIN = 0.2   # Low shield management priority
KLINGON_SHIELD_PRIORITY_MAX = 0.9   # High shield management priority

KLINGON_DAMAGE_AVOIDANCE_MIN = 0.1  # Reckless, ignores incoming damage
KLINGON_DAMAGE_AVOIDANCE_MAX = 0.9  # Cautious, actively avoids damage

# Personality Trait Parameters
# ----------------------------
KLINGON_COURAGE_MIN = 0.2           # Cowardly disposition
KLINGON_COURAGE_MAX = 0.95          # Fearless warrior disposition

KLINGON_UNPREDICTABILITY_MIN = 0.1  # Highly predictable behavior patterns
KLINGON_UNPREDICTABILITY_MAX = 0.8  # Chaotic, unpredictable behavior patterns

KLINGON_HONOR_CODE_MIN = 0.0        # Dishonorable, uses any tactics
KLINGON_HONOR_CODE_MAX = 0.9        # Honorable warrior, follows combat ethics

KLINGON_VENGEANCE_FACTOR_MIN = 0.1  # Quickly forgets damage taken
KLINGON_VENGEANCE_FACTOR_MAX = 0.9  # Remembers and prioritizes revenge

# Advanced Combat Parameters
# --------------------------
KLINGON_POWER_MANAGEMENT_MIN = 0.3  # Poor power allocation skills
KLINGON_POWER_MANAGEMENT_MAX = 0.9  # Expert power allocation skills

KLINGON_MULTI_TARGET_MIN = 0.0      # Focuses on single target only
KLINGON_MULTI_TARGET_MAX = 0.6      # May engage multiple targets

KLINGON_AMBUSH_PREFERENCE_MIN = 0.0 # Never uses ambush tactics
KLINGON_AMBUSH_PREFERENCE_MAX = 0.7 # Frequently uses ambush tactics

# Temporal Behavior Parameters
# ----------------------------
KLINGON_REACTION_TIME_MIN = 0.5     # Lightning fast reactions (shorter decision intervals)
KLINGON_REACTION_TIME_MAX = 1.0     # Very quick reactions - immediate response

KLINGON_PURSUIT_PERSISTENCE_MIN = 0.2 # Gives up pursuit easily
KLINGON_PURSUIT_PERSISTENCE_MAX = 0.9 # Relentlessly pursues player

KLINGON_LEARNING_RATE_MIN = 0.0     # Never adapts to player tactics
KLINGON_LEARNING_RATE_MAX = 0.5     # Adapts quickly to player tactics

# ====================================================================
# PLANET AND STAR CLASSIFICATION DATA
# ====================================================================

# Planet Class Definitions (Star Trek Standard)
PLANET_CLASSES = {
    'D': {
        'name': 'Class D Planet',
        'description': 'Rocky, barren world with thin atmosphere. Surface is inhospitable to most life forms.',
        'images': ['classDplanet.png', 'classDplanet1.png']
    },
    'H': {
        'name': 'Class H Planet',
        'description': 'Desert planet with arid climate. Capable of supporting hardy life forms.',
        'images': ['classHplanet.png', 'classHplanet2.png', 'classHplanet3.png']
    },
    'J': {
        'name': 'Class J Planet',
        'description': 'Gas giant with turbulent atmospheric conditions. Rich in hydrogen and helium.',
        'images': ['classJplanet.png', 'classJplanet2.png']
    },
    'K': {
        'name': 'Class K Planet',
        'description': 'Rocky planet with thin atmosphere. Borderline habitable with proper terraforming.',
        'images': ['classKplanet.png', 'classKplanet1.png', 'classKplanet2.png']
    },
    'L': {
        'name': 'Class L Planet',
        'description': 'Rocky world with minimal atmosphere. Requires environmental suits for surface activity.',
        'images': ['classLplanet.png', 'classLplanet2.png']
    },
    'M': {
        'name': 'Class M Planet',
        'description': 'Earth-like world with oxygen-nitrogen atmosphere. Ideal for humanoid life.',
        'images': ['classMplanet.png']
    },
    'N': {
        'name': 'Class N Planet',
        'description': 'Sulfuric world with high surface temperatures and toxic atmosphere.',
        'images': ['classNplanet.png']
    },
    'R': {
        'name': 'Class R Planet',
        'description': 'Rogue planet with volcanic activity. Extremely dangerous surface conditions.',
        'images': ['classRplanet.jpg', 'classRplanet.webp']
    },
    'T': {
        'name': 'Class T Planet',
        'description': 'Ultra-giant gas world with extreme gravitational fields and radiation.',
        'images': ['classTplanet.jpg', 'classTplanet.webp', 'classTplanet1.jpg', 'classTplanet1.webp']
    },
    'Y': {
        'name': 'Class Y Planet',
        'description': 'Demon-class planet with corrosive atmosphere and extreme temperatures.',
        'images': ['classYplanet.jpg', 'classYplanet.webp', 'classYplanet1.jpg', 'classYplanet1.webp']
    }
}

# Star Classification (Main Sequence and Stellar Remnants)
STAR_CLASSES = {
    'YELLOW_DWARF': {
        'name': 'Yellow Dwarf Star',
        'description': 'Main sequence star similar to Earth\'s sun. Stable hydrogen fusion, ideal for planetary systems.',
        'images': ['yellowDwarf.png']
    },
    'RED_DWARF': {
        'name': 'Red Dwarf Star',
        'description': 'Small, cool star with extended lifespan. Most common type in the galaxy.',
        'images': ['redDwarf.png']
    },
    'RED_GIANT': {
        'name': 'Red Giant Star',
        'description': 'Evolved star in late stages of life. Massive size with cooler surface temperature.',
        'images': ['redGiant.png']
    },
    'WHITE_DWARF': {
        'name': 'White Dwarf Star',
        'description': 'Dense stellar remnant. Extremely hot but small, gradually cooling over billions of years.',
        'images': ['whiteDwarf.png']
    },
    'BLUE_GIANT': {
        'name': 'Blue Giant Star',
        'description': 'Massive, extremely hot star burning through fuel rapidly. Short but spectacular lifespan.',
        'images': ['blueGiant.png']
    },
    'ORANGE_GIANT': {
        'name': 'Orange Giant Star',
        'description': 'Evolved star larger than main sequence. Cooler than sun-type stars but more luminous.',
        'images': ['orangeGiant.png']
    },
    'BROWN_DWARF': {
        'name': 'Brown Dwarf Star',
        'description': 'Failed star lacking sufficient mass for hydrogen fusion. Dim and cool.',
        'images': ['brownDwarf.png']
    },
    'NEUTRON_STAR': {
        'name': 'Neutron Star',
        'description': 'Ultra-dense stellar remnant composed entirely of neutrons. Intense gravitational field.',
        'images': ['neutronStar.png']
    },
    'PULSAR': {
        'name': 'Pulsar',
        'description': 'Rapidly rotating neutron star emitting beams of radiation. Precise timing beacon.',
        'images': ['pulsar.png']
    },
    'HYPERGIANT': {
        'name': 'Hypergiant Star',
        'description': 'Extremely massive and luminous star. Among the most powerful objects in the galaxy.',
        'images': ['hyperGiant.png']
    }
}
