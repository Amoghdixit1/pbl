"""Configuration constants for the parking management system."""

# Configuration
DATA_DIR = "parking_data"
SLOTS_FILE = DATA_DIR + "/slots.txt"
ACTIVE_FILE = DATA_DIR + "/active_sessions.txt"
TRANS_FILE = DATA_DIR + "/transactions.txt"
REVENUE_FILE = DATA_DIR + "/revenue.txt"

TIME_FMT = "%Y-%m-%d %H:%M:%S"
FLOORS = 3

# number of slots of each type on every floor
COMPACT_PER_FLOOR = 6
LARGE_PER_FLOOR = 3
EV_PER_FLOOR = 2

# which slot types each vehicle category can use
ALLOWED_SLOTS = {
    "compact": ["Compact", "Large"],
    "large": ["Large"],
    "ev": ["EV"],
}
