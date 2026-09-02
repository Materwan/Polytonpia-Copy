"""
Represente un joueur : sa tribu, son tresor d'etoiles, ses villes, ses
unites et les technologies qu'il a recherchees.

C'est ici que se trouve la logique d'achat (batiments, unites,
technologies) : le `Player` est responsable de verifier qu'il peut payer,
de deduire les etoiles, et d'appliquer les consequences (population,
nouvelle unite, nouvelle technologie...).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import constants as C
from city import City
from buildings import BUILDING_SPECS, can_build
from units import UNIT_SPECS, Unit, WARRIOR


@dataclass
class Player:
    id: int
    name: str
    tribe: str
    stars: int = C.STARTING_STARS
    cities: List[City] = field(default_factory=list)
    units: List[Unit] = field(default_factory=list)
    techs: Set[str] = field(default_factory=set)
    _next_city_id: int = 0

    def __post_init__(self):
        bonus = C.TRIBES.get(self.tribe, {}).get("bonus_stars", 0)
        self.stars += bonus

    # ------------------------------------------------------------------
    # Villes
    # ------------------------------------------------------------------
    @property
    def capital(self) -> Optional[City]:
        for c in self.cities:
            if c.is_capital:
                return c
        return self.cities[0] if self.cities else None

    def found_capital(self, position: int) -> City:
        city = City(
            id=self._next_city_id,
            owner=self.id,
            position=position,
            name=f"{self.tribe} Capital",
            is_capital=True,
        )
        self._next_city_id += 1
        self.cities.append(city)
        return city

    def get_city(self, city_id: int) -> Optional[City]:
        for c in self.cities:
            if c.id == city_id:
                return c
        return None

    # ------------------------------------------------------------------
    # Economie
    # ------------------------------------------------------------------
    def collect_income(self) -> int:
        """A appeler en debut de tour : ajoute les etoiles produites par
        toutes les villes du joueur, retourne le montant collecte."""
        income = sum(city.stars_income() for city in self.cities)
        self.stars += income
        return income

    def research_tech(self, tech_name: str) -> "tuple[bool, str]":
        if tech_name in self.techs:
            return False, "Technologie deja recherchee."
        if self.stars < C.TECH_COST:
            return False, f"Pas assez d'etoiles (cout {C.TECH_COST})."
        self.stars -= C.TECH_COST
        self.techs.add(tech_name)
        return True, f"Technologie '{tech_name}' recherchee."

    # ------------------------------------------------------------------
    # Batiments
    # ------------------------------------------------------------------
    def buy_building(
        self, city: City, tile_idx: int, building_id: int, game_map, resource_map
    ) -> "tuple[bool, str]":
        ok, err = can_build(
            building_id, city, tile_idx, game_map, resource_map, self.techs
        )
        if not ok:
            return False, err

        spec = BUILDING_SPECS[building_id]
        if self.stars < spec.cost:
            return (
                False,
                f"Pas assez d'etoiles (cout {spec.cost}, disponible {self.stars}).",
            )

        self.stars -= spec.cost
        city.add_building(tile_idx, building_id)
        rewards = city.add_population(spec.population)
        for reward in rewards:
            self._apply_level_reward(city, reward)

        return True, f"{spec.name} construit en {tile_idx} ({city.name})."

    def _apply_level_reward(self, city: City, reward: str) -> None:
        """Applique la recompense de montee de niveau d'une ville."""
        if reward == "population":
            city.add_population(1)  # equivalent a un Parc, sans reboucler a l'infini
        elif reward == "border_growth":
            city.border_radius += 1
        elif reward == "workshop":
            self.units.append(
                Unit(unit_type=WARRIOR, owner=self.id, position=city.position)
            )
        elif reward in ("explorer", "resources"):
            # pas de brouillard de guerre / carte cachee dans cet environnement
            # simplifie : ces recompenses n'ont pour l'instant pas d'effet
            pass

    # ------------------------------------------------------------------
    # Unites
    # ------------------------------------------------------------------
    def can_train(self, unit_type: int, city: City) -> "tuple[bool, str]":
        if unit_type not in UNIT_SPECS:
            return False, "Unite inconnue."
        spec = UNIT_SPECS[unit_type]
        if spec.requires_tech and spec.requires_tech not in self.techs:
            return False, f"Technologie requise non recherchee : {spec.requires_tech}."
        from units import Domain

        if spec.domain == Domain.NAVAL:
            from buildings import PORT

            if not city.has_building(PORT):
                return False, "Un port est necessaire pour entrainer une unite navale."
        if self.stars < spec.cost:
            return (
                False,
                f"Pas assez d'etoiles (cout {spec.cost}, disponible {self.stars}).",
            )
        return True, ""

    def train_unit(self, unit_type: int, city: City) -> "tuple[bool, str]":
        ok, err = self.can_train(unit_type, city)
        if not ok:
            return False, err
        spec = UNIT_SPECS[unit_type]
        self.stars -= spec.cost
        unit = Unit(unit_type=unit_type, owner=self.id, position=city.position)
        self.units.append(unit)
        return True, f"{spec.name} entraine dans {city.name}."

    # ------------------------------------------------------------------
    # Tour de jeu
    # ------------------------------------------------------------------
    def reset_units_for_new_turn(self) -> None:
        for unit in self.units:
            unit.reset_turn()

    def remove_dead_units(self) -> None:
        self.units = [u for u in self.units if u.is_alive]

    def is_eliminated(self) -> bool:
        return len(self.cities) == 0

    def __str__(self):
        return (
            f"{self.name} [{self.tribe}] - {self.stars} etoiles, "
            f"{len(self.cities)} ville(s), {len(self.units)} unite(s), "
            f"techs: {', '.join(sorted(self.techs)) or 'aucune'}"
        )
