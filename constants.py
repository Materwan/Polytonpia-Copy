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

# ---------------------------------------------------------------------------
# Tribus (cosmetique pour l'instant : nom + petit bonus de depart)
# ---------------------------------------------------------------------------
TRIBES = {
    "Imperius": {"bonus_stars": 0},
    "Bardur": {"bonus_stars": 0},
    "Elyrion": {"bonus_stars": 0},
    "Zebasi": {"bonus_stars": 2},  # tribu commercante : un peu plus d'etoiles au depart
    "Ain-Ainu": {"bonus_stars": 0},
    "Quetzali": {"bonus_stars": 0},
    "Yaddak": {"bonus_stars": 0},
    "Aquarion": {"bonus_stars": 0},
}

# ---------------------------------------------------------------------------
# Villes / niveaux
# ---------------------------------------------------------------------------
# Population cumulee necessaire pour passer du niveau i au niveau i+1
# (index 0 = seuil pour passer du niveau 1 au niveau 2, etc.)
CITY_LEVEL_THRESHOLDS = [2, 3, 5, 8, 12, 18, 25, 35, 50, 70]

STARTING_STARS = 5
TECH_COST = 5  # cout fixe (simplifie) pour rechercher n'importe quelle technologie
