# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------
WATER = 0
PLAIN = 1
FOREST = 2
MOUNTAIN = 3

TERRAIN_NAMES = {WATER: "water", PLAIN: "plain", FOREST: "forest", MOUNTAIN: "mountain"}
IMPASSABLE_TERRAIN = {WATER}  # land units cannot enter water in this simplified env

MAP_SIZES = {
    "Tiny": 121,
    "Small": 196,
    "Normal": 256,
    "Large": 324,
    "Huge": 400,
    "Massive": 900,
}
