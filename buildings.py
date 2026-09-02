"""
Batiments constructibles dans le territoire d'une ville.

Chaque batiment coute des etoiles (la monnaie du jeu, produite par les
villes chaque tour) et apporte de la population a la ville, ce qui la fait
monter de niveau une fois un certain seuil cumule atteint (voir
`constants.CITY_LEVEL_THRESHOLDS` et `city.City.add_population`).

Certains batiments ont des contraintes :
    - `terrain`      : terrains sur lesquels la case elle-meme doit se trouver
    - `resource_required` : ressource devant etre presente sur la case
    - `extra_check`  : fonction de validation additionnelle (adjacence...)
    - `requires_tech`: technologie necessaire (cf. `player.Player.techs`)

Le batiment n'est jamais applique directement sur la carte (`Map`) : il est
enregistre dans `City.buildings` (tile_idx -> building_id). Pour l'affichage
ou les regles de mouvement, la case garde son terrain d'origine.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Optional

import constants as C
from utils import plus_sign
from map import FRUIT, CROP, GAME, ORE, FISH, WHALE

# ---------------------------------------------------------------------------
# Identifiants des batiments
# ---------------------------------------------------------------------------
(
    FARM,
    WINDMILL,
    SAWMILL,
    MINE,
    PORT,
    MARKET,
    TEMPLE,
    FOREST_TEMPLE,
    MOUNTAIN_TEMPLE,
    CITY_WALL,
    PARK,
) = range(11)

BUILDING_NAMES = {
    FARM: "farm",
    WINDMILL: "windmill",
    SAWMILL: "sawmill",
    MINE: "mine",
    PORT: "port",
    MARKET: "market",
    TEMPLE: "temple",
    FOREST_TEMPLE: "forest_temple",
    MOUNTAIN_TEMPLE: "mountain_temple",
    CITY_WALL: "city_wall",
    PARK: "park",
}
NAME_TO_BUILDING = {v: k for k, v in BUILDING_NAMES.items()}


@dataclass(frozen=True)
class BuildingSpec:
    id: int
    name: str
    cost: int
    population: int
    terrain: Optional[FrozenSet[int]] = None  # None = n'importe quelle case terrestre
    resource_required: Optional[int] = None  # ressource devant etre sur la case
    requires_tech: Optional[str] = None
    is_level_reward: bool = False  # non achetable, obtenu en montant de niveau
    one_per_city: bool = True
    stars_bonus: int = 0  # etoiles supplementaires produites par tour
    defense_bonus: float = 1.0  # multiplicateur de defense (murs)
    enables_naval: bool = False  # autorise la production d'unites navales
    extra_check: Optional[Callable] = None  # (tile_idx, game_map, resource_map) -> bool
    description: str = ""


# ---------------------------------------------------------------------------
# Verifications d'adjacence specifiques
# ---------------------------------------------------------------------------
def _count_adjacent(tile_idx, game_map, predicate) -> int:
    n = game_map.size
    count = 0
    for nb in plus_sign(tile_idx, n):
        row, col = nb // n, nb % n
        if predicate(nb, row, col):
            count += 1
    return count


def _windmill_check(tile_idx, game_map, resource_map) -> bool:
    # necessite au moins une case de blé (CROP) adjacente pour etre rentable
    return (
        _count_adjacent(
            tile_idx, game_map, lambda nb, r, c: resource_map.get(nb) == CROP
        )
        >= 1
    )


def _sawmill_check(tile_idx, game_map, resource_map) -> bool:
    # necessite au moins deux forets adjacentes
    return (
        _count_adjacent(tile_idx, game_map, lambda nb, r, c: game_map[r, c] == C.FOREST)
        >= 2
    )


def _port_check(tile_idx, game_map, resource_map) -> bool:
    # doit toucher l'eau pour donner acces a la mer
    return (
        _count_adjacent(tile_idx, game_map, lambda nb, r, c: game_map[r, c] == C.WATER)
        >= 1
    )


def _market_check(tile_idx, game_map, resource_map) -> bool:
    # doit etre adjacent a un batiment de ressource (le controle se fait
    # cote City car il faut connaitre les batiments deja construits ;
    # ici on se contente de valider que la case est bien en plaine.
    return True


# ---------------------------------------------------------------------------
# Catalogue des batiments
# ---------------------------------------------------------------------------
BUILDING_SPECS: Dict[int, BuildingSpec] = {
    FARM: BuildingSpec(
        FARM,
        "farm",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        resource_required=CROP,
        description="Cultive le ble d'une case. +1 population.",
    ),
    WINDMILL: BuildingSpec(
        WINDMILL,
        "windmill",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        requires_tech="farming",
        extra_check=_windmill_check,
        description="Doit toucher un champ de ble. +1 population.",
    ),
    SAWMILL: BuildingSpec(
        SAWMILL,
        "sawmill",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        requires_tech="forestry",
        extra_check=_sawmill_check,
        description="Doit toucher au moins 2 forets. +1 population.",
    ),
    MINE: BuildingSpec(
        MINE,
        "mine",
        cost=5,
        population=1,
        terrain=frozenset({C.MOUNTAIN}),
        resource_required=ORE,
        requires_tech="mining",
        description="Exploite un gisement de minerai. +1 population.",
    ),
    PORT: BuildingSpec(
        PORT,
        "port",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        requires_tech="navigation",
        extra_check=_port_check,
        enables_naval=True,
        description="Cote maritime, permet de construire des unites navales.",
    ),
    MARKET: BuildingSpec(
        MARKET,
        "market",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        requires_tech="trade",
        extra_check=_market_check,
        stars_bonus=1,
        description="+1 population et +1 etoile par tour.",
    ),
    TEMPLE: BuildingSpec(
        TEMPLE,
        "temple",
        cost=5,
        population=1,
        terrain=frozenset({C.PLAIN}),
        requires_tech="meditation",
        description="+1 population immediatement, contribue au score au fil des niveaux.",
    ),
    FOREST_TEMPLE: BuildingSpec(
        FOREST_TEMPLE,
        "forest_temple",
        cost=5,
        population=1,
        terrain=frozenset({C.FOREST}),
        requires_tech="meditation",
        description="Variante foret du temple.",
    ),
    MOUNTAIN_TEMPLE: BuildingSpec(
        MOUNTAIN_TEMPLE,
        "mountain_temple",
        cost=5,
        population=1,
        terrain=frozenset({C.MOUNTAIN}),
        requires_tech="meditation",
        description="Variante montagne du temple.",
    ),
    CITY_WALL: BuildingSpec(
        CITY_WALL,
        "city_wall",
        cost=5,
        population=0,
        requires_tech="strategy",
        defense_bonus=1.5,
        description="Construit sur la capitale : +50% defense pour la ville.",
    ),
    PARK: BuildingSpec(
        PARK,
        "park",
        cost=0,
        population=1,
        is_level_reward=True,
        one_per_city=False,
        description="Recompense de niveau : +1 population immediate.",
    ),
}


# ---------------------------------------------------------------------------
# Validation d'une construction
# ---------------------------------------------------------------------------
def can_build(
    building_id: int, city, tile_idx: int, game_map, resource_map, player_techs: set
) -> "tuple[bool, str]":
    """Verifie si `building_id` peut etre construit sur `tile_idx` par la
    ville `city`. `resource_map` est le dict index -> ressource (ex:
    `Map.objects`). Retourne (ok, message_erreur_si_echec)."""
    if building_id not in BUILDING_SPECS:
        return False, "Batiment inconnu."
    spec = BUILDING_SPECS[building_id]

    if spec.is_level_reward:
        return False, f"{spec.name} n'est pas achetable, obtenu en montant de niveau."

    if spec.requires_tech and spec.requires_tech not in player_techs:
        return False, f"Technologie requise non recherchee : {spec.requires_tech}."

    if spec.one_per_city and city.has_building(building_id):
        return False, f"{spec.name} deja construit dans cette ville."

    if tile_idx in city.buildings:
        return False, "Une case ne peut accueillir qu'un seul batiment."

    if tile_idx not in city.workable_tiles(game_map.size) and tile_idx != city.position:
        return False, "Cette case est hors du territoire de la ville."

    if building_id == CITY_WALL and tile_idx != city.position:
        return False, "Les murs ne se construisent que sur la case de la ville."

    row, col = tile_idx // game_map.size, tile_idx % game_map.size
    terrain = game_map[row, col]

    if spec.terrain is not None and terrain not in spec.terrain:
        return False, "Terrain incompatible avec ce batiment."

    if (
        spec.resource_required is not None
        and resource_map.get(tile_idx) != spec.resource_required
    ):
        return False, "La ressource requise n'est pas presente sur cette case."

    if spec.extra_check is not None and not spec.extra_check(
        tile_idx, game_map, resource_map
    ):
        return False, "Conditions d'adjacence non remplies pour ce batiment."

    if building_id == MARKET:
        # doit toucher un batiment "producteur" (farm/mine/sawmill/port)
        producer_ids = {FARM, MINE, SAWMILL, PORT}
        touches_producer = any(
            nb in city.buildings and city.buildings[nb] in producer_ids
            for nb in plus_sign(tile_idx, game_map.size)
        )
        if not touches_producer:
            return (
                False,
                "Le marche doit toucher une ferme, une mine, une scierie ou un port.",
            )

    return True, ""
