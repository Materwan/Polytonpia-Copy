"""
Represente une ville (capitale ou ville conquise/fondee) : population,
niveau, territoire exploitable et batiments construits.

La montee de niveau suit `constants.CITY_LEVEL_THRESHOLDS` : la population
cumulee necessaire pour passer du niveau i au niveau i+1. A chaque niveau
gagne, une recompense est retournee (a appliquer par l'appelant, cf.
`player.Player.add_population_to_city`) :

    - "population"     : +1 population immediate (equivalent a un Parc)
    - "workshop"        : une unite de base gratuite dans la ville
    - "border_growth"   : +1 rayon de territoire exploitable
    - "explorer"        : revele une zone de la carte autour de la ville
    - "resources"       : revele les ressources autour de la ville

Le niveau 1 est le niveau de depart (ville fraichement fondee / capitale).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import constants as C
from utils import round_

LEVEL_REWARD_CYCLE = [
    "workshop",
    "border_growth",
    "population",
    "explorer",
    "resources",
]


@dataclass
class City:
    id: int
    owner: int
    position: int
    name: str = "City"
    level: int = 1
    population: float = 0.0
    border_radius: int = 1
    buildings: Dict[int, int] = field(default_factory=dict)  # tile_idx -> building_id
    is_capital: bool = False

    # ------------------------------------------------------------------
    # Population / niveaux
    # ------------------------------------------------------------------
    def population_needed(self) -> Optional[int]:
        """Population cumulee necessaire pour passer au niveau suivant.
        Retourne None si la ville a atteint le niveau maximum defini."""
        idx = self.level - 1
        if idx >= len(C.CITY_LEVEL_THRESHOLDS):
            return None
        return C.CITY_LEVEL_THRESHOLDS[idx]

    def add_population(self, amount: float) -> List[str]:
        """Ajoute de la population a la ville et la fait monter de niveau
        autant de fois que necessaire. Retourne la liste (dans l'ordre) des
        recompenses de niveau obtenues, a appliquer par l'appelant (le
        Player a besoin d'acceder aux unites / a la carte pour certaines
        d'entre elles)."""
        if amount <= 0:
            return []
        self.population += amount
        rewards = []
        needed = self.population_needed()
        while needed is not None and self.population >= needed:
            self.population -= needed
            self.level += 1
            rewards.append(self._level_up_reward())
            needed = self.population_needed()
        return rewards

    def _level_up_reward(self) -> str:
        # cycle simple et previsible plutot qu'un choix interactif ;
        # le tout premier niveau 2 donne toujours un atelier (unite gratuite)
        cycle_index = (self.level - 2) % len(LEVEL_REWARD_CYCLE)
        return LEVEL_REWARD_CYCLE[cycle_index]

    # ------------------------------------------------------------------
    # Batiments
    # ------------------------------------------------------------------
    def has_building(self, building_id: int) -> bool:
        return building_id in self.buildings.values()

    def temple_count(self) -> int:
        from buildings import TEMPLE, FOREST_TEMPLE, MOUNTAIN_TEMPLE

        return sum(
            1
            for b in self.buildings.values()
            if b in (TEMPLE, FOREST_TEMPLE, MOUNTAIN_TEMPLE)
        )

    def add_building(self, tile_idx: int, building_id: int) -> None:
        self.buildings[tile_idx] = building_id

    # ------------------------------------------------------------------
    # Territoire
    # ------------------------------------------------------------------
    def workable_tiles(self, map_size: int) -> List[int]:
        """Cases sur lesquelles la ville peut construire, en fonction de son
        rayon de territoire actuel (agrandi par la recompense de niveau
        'border_growth')."""
        return round_(self.position, self.border_radius, map_size)

    # ------------------------------------------------------------------
    # Economie
    # ------------------------------------------------------------------
    def stars_income(self) -> int:
        """Etoiles produites par cette ville a chaque tour : une etoile de
        base par niveau, plus le bonus des batiments economiques (marche)."""
        from buildings import BUILDING_SPECS

        income = self.level
        for building_id in self.buildings.values():
            income += BUILDING_SPECS[building_id].stars_bonus
        return income

    def defense_multiplier(self) -> float:
        from buildings import BUILDING_SPECS, CITY_WALL

        if self.has_building(CITY_WALL):
            return BUILDING_SPECS[CITY_WALL].defense_bonus
        return 1.0

    def __str__(self):
        needed = self.population_needed()
        progress = (
            f"{self.population:.1f}/{needed}"
            if needed is not None
            else f"{self.population:.1f} (max)"
        )
        return (
            f"{self.name} (niv {self.level}, pop {progress}, "
            f"rayon {self.border_radius}, {len(self.buildings)} batiment(s))"
        )
