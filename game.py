"""
Boucle de jeu principale.

`Game` s'occupe de :
    - creer la carte et les joueurs (`setup`)
    - gerer l'ordre des tours (`start_turn` / `end_turn`)
    - exposer les actions possibles pour le joueur courant (construire,
      entrainer une unite, rechercher une technologie, se deplacer,
      attaquer...)

Le combat et le deplacement s'appuient sur les fonctions deja definies
dans `units.py` (reachable_tiles, apply_combat...). Ce module se contente
de les brancher a l'etat de la partie (qui possede quoi, qui joue).
"""

from typing import Dict, List, Optional, Tuple

import constants as C
from map import Map, MapType
from player import Player
from units import (
    Unit,
    UNIT_SPECS,
    UNIT_NAMES,
    reachable_tiles,
    can_enter_tile,
    apply_combat,
    in_attack_range,
    board_ship,
    disembark,
)
from buildings import BUILDING_NAMES, NAME_TO_BUILDING


class Game:
    def __init__(self):
        self.map: Optional[Map] = None
        self.players: List[Player] = []
        self.turn_number: int = 1
        self.current_player_index: int = 0
        self.finished: bool = False

    # ------------------------------------------------------------------
    # Mise en place
    # ------------------------------------------------------------------
    def setup(
        self,
        player_names: List[str],
        tribes: List[str],
        map_size_name: str,
        seed: Optional[int] = None,
    ) -> None:
        if len(player_names) != len(tribes):
            raise ValueError("Il faut une tribu par joueur.")
        n_players = len(player_names)
        if n_players < 2:
            raise ValueError("Il faut au moins 2 joueurs.")

        size = C.MAP_SIZES[map_size_name]
        map_type = MapType(size=(size, size), n_players=n_players, seed=seed)
        self.map = Map(map_type)

        self.players = []
        for i, (name, tribe) in enumerate(zip(player_names, tribes)):
            player = Player(id=i, name=name, tribe=tribe)
            capital_position = self.map.capitals[i]
            player.found_capital(capital_position)
            self.players.append(player)

        self.turn_number = 1
        self.current_player_index = 0
        self.finished = False

    # ------------------------------------------------------------------
    # Acces
    # ------------------------------------------------------------------
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def occupied_tiles(self) -> Dict[int, Unit]:
        occupied = {}
        for player in self.players:
            for unit in player.units:
                occupied[unit.position] = unit
        return occupied

    def owner_of_city(self, city_id: int, player_id: int) -> bool:
        player = self.players[player_id]
        return player.get_city(city_id) is not None

    # ------------------------------------------------------------------
    # Tours
    # ------------------------------------------------------------------
    def start_turn(self) -> int:
        """A appeler en debut de tour du joueur courant. Retourne le
        montant d'etoiles collecte."""
        player = self.current_player
        player.reset_units_for_new_turn()
        return player.collect_income()

    def end_turn(self) -> None:
        self.current_player_index += 1
        if self.current_player_index >= len(self.players):
            self.current_player_index = 0
            self.turn_number += 1
        self._check_victory()

    def _check_victory(self) -> None:
        alive = [p for p in self.players if not p.is_eliminated()]
        if len(alive) <= 1:
            self.finished = True

    # ------------------------------------------------------------------
    # Actions : batiments
    # ------------------------------------------------------------------
    def build(
        self, city_id: int, tile_idx: int, building_name: str
    ) -> Tuple[bool, str]:
        player = self.current_player
        city = player.get_city(city_id)
        if city is None:
            return False, "Ville introuvable pour ce joueur."
        building_id = NAME_TO_BUILDING.get(building_name)
        if building_id is None:
            return False, f"Batiment inconnu : {building_name}."
        return player.buy_building(
            city, tile_idx, building_id, self.map, self.map.objects
        )

    # ------------------------------------------------------------------
    # Actions : unites
    # ------------------------------------------------------------------
    def train(self, city_id: int, unit_name: str) -> Tuple[bool, str]:
        player = self.current_player
        city = player.get_city(city_id)
        if city is None:
            return False, "Ville introuvable pour ce joueur."
        unit_type = {v: k for k, v in UNIT_NAMES.items()}.get(unit_name)
        if unit_type is None:
            return False, f"Unite inconnue : {unit_name}."
        return player.train_unit(unit_type, city)

    def move(self, unit: Unit, destination: int) -> Tuple[bool, str]:
        occupied = self.occupied_tiles()
        options = reachable_tiles(unit, self.map, occupied)
        if destination not in options:
            return False, "Case non atteignable."
        row, col = destination // self.map.size, destination % self.map.size
        terrain = self.map[row, col]
        if not can_enter_tile(unit, terrain, occupied.get(destination)):
            return False, "Case non franchissable."
        unit.position = destination
        unit.has_moved = True
        return True, "Deplacement effectue."

    def attack(self, attacker: Unit, defender: Unit) -> Tuple[bool, str]:
        if attacker.owner == defender.owner:
            return False, "Impossible d'attaquer sa propre unite."
        if attacker.has_attacked:
            return False, "Cette unite a deja attaque ce tour-ci."
        if not in_attack_range(attacker, defender, self.map.size):
            return False, "Cible hors de portee."

        terrain_bonus = 1.0
        row, col = defender.position // self.map.size, defender.position % self.map.size
        terrain = self.map[row, col]
        if terrain in (C.FOREST, C.MOUNTAIN):
            terrain_bonus = 1.5

        apply_combat(attacker, defender, terrain_bonus)
        defending_player = self.players[defender.owner]
        defending_player.remove_dead_units()
        return True, "Combat resolu."

    # ------------------------------------------------------------------
    # Technologies
    # ------------------------------------------------------------------
    def research(self, tech_name: str) -> Tuple[bool, str]:
        return self.current_player.research_tech(tech_name)

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def status(self) -> str:
        lines = [
            f"--- Tour {self.turn_number} - joueur : {self.current_player.name} ---"
        ]
        for player in self.players:
            marker = ">" if player is self.current_player else " "
            lines.append(f"{marker} {player}")
            for city in player.cities:
                lines.append(f"    {city}")
        return "\n".join(lines)
