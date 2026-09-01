"""
Génération de carte inspirée de l'algorithme du jeu original Polytopia,
elle-même inspirée du générateur non-officiel de QuasiStellar
(https://github.com/QuasiStellar/Polytopia-Map-Generator).

Principe general (contrairement a un simple seuillage de bruit de Perlin) :

    1. Decouper la carte en quadrants (un par capitale potentielle).
    2. Faire "pousser" la terre depuis des graines aleatoires jusqu'a
       atteindre le pourcentage de terre voulu (`initial_land`).
    3. Lisser les cotes avec un automate cellulaire (`smoothing` passes).
    4. Faire pousser les montagnes en clusters sur la terre (`relief`),
       puis les forets sur le reste des cases plates.
    5. Placer une capitale par quadrant, sur une case plate, en respectant
       une distance minimale entre elles.
    6. Placer les ressources (fruit, gibier, poisson, minerai, baleine)
       en fonction du terrain, avec un bonus de densite pres des capitales.
"""

from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass, field
import random

import constants as C
from utils import circle, round_, distance, plus_sign


@dataclass
class MapType:
    size: Tuple[int, int]
    n_players: int = 2
    initial_land: float = 0.5  # fraction de terre voulue (0-1)
    smoothing: int = 2  # nb de passes de lissage des cotes
    relief: float = 0.15  # fraction de la terre en montagnes
    forest_density: float = 0.35  # fraction du reste en foret
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Ressources
# ---------------------------------------------------------------------------
FRUIT, CROP, GAME, ORE, FISH, WHALE, RUIN = range(7)

RESOURCE_NAMES = {
    FRUIT: "fruit",
    CROP: "crop",
    GAME: "game",
    ORE: "ore",
    FISH: "fish",
    WHALE: "whale",
    RUIN: "ruin",
}

# terrain -> [(ressource, proba_de_base)]
RESOURCE_RULES = {
    C.PLAIN: [(FRUIT, 0.06), (CROP, 0.05), (RUIN, 0.015)],
    C.FOREST: [(GAME, 0.10), (RUIN, 0.02)],
    C.MOUNTAIN: [(ORE, 0.18)],
    C.WATER: [(FISH, 0.06), (WHALE, 0.01)],
}


class Map:
    """Carte carree/rectangulaire representee par une grille de terrains.

    Les tiles sont accessibles en `[row][col]` (via __getitem__), mais en
    interne beaucoup d'operations passent par des index "plats"
    (row * width + col) pour reutiliser les helpers de utils.py.
    """

    tiles: List[List[int]]

    def __init__(self, map_type: MapType):
        self.map_type = map_type
        self.width, self.height = map_type.size
        if self.width != self.height:
            raise ValueError(
                "Seules les cartes carrees sont supportees pour le moment."
            )
        self.size = self.width

        self.rng = random.Random(map_type.seed)

        self.objects: Dict[int, int] = {}  # index -> resource id
        self.units: Dict[int, int] = {}  # index -> unit id (rempli par le jeu)
        self.capitals: List[int] = []  # index des capitales
        self.quadrants: List[Tuple[int, int, int, int]] = []

        self._generate_map()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def _generate_map(self):
        n = self.size

        self._flat = [C.WATER] * (n * n)
        self.quadrants = self._make_quadrants(self.map_type.n_players)

        self._grow_land(self.map_type.initial_land)
        for _ in range(self.map_type.smoothing):
            self._smooth_coastline()

        self._grow_mountains(self.map_type.relief)
        self._grow_forests(self.map_type.forest_density)

        self.capitals = self._place_capitals()
        self._place_resources()

        # Conversion finale en grille 2D [row][col]
        self.tiles = [[self._flat[r * n + c] for c in range(n)] for r in range(n)]

    def _make_quadrants(self, n_players: int) -> List[Tuple[int, int, int, int]]:
        """Decoupe la carte en zones (x0, y0, x1, y1) - une par joueur,
        comme le fait le jeu original pour repartir les capitales."""
        if n_players <= 4:
            grid = 2
        elif n_players <= 9:
            grid = 3
        else:
            grid = 4

        n = self.size
        step = n / grid
        quadrants = []
        for row in range(grid):
            for col in range(grid):
                x0, y0 = int(col * step), int(row * step)
                x1, y1 = int((col + 1) * step), int((row + 1) * step)
                quadrants.append((x0, y0, x1, y1))
        self.rng.shuffle(quadrants)
        return quadrants[: max(n_players, 1)]

    def _grow_land(self, target_fraction: float):
        """Fait germer des blobs de terre depuis des graines aleatoires
        jusqu'a atteindre la fraction de terre voulue. C'est ce que fait
        (en substance) le generateur JS plutot qu'un seuillage de bruit."""
        n = self.size
        total = n * n
        target = int(total * target_fraction)

        # une graine par quadrant pour garantir de la terre partout,
        # + quelques graines libres pour varier les cotes
        seeds = []
        for x0, y0, x1, y1 in self.quadrants:
            cx = self.rng.randint(x0, max(x0, x1 - 1))
            cy = self.rng.randint(y0, max(y0, y1 - 1))
            seeds.append(cy * n + cx)

        extra_seeds = max(1, len(self.quadrants) // 2)
        for _ in range(extra_seeds):
            seeds.append(self.rng.randint(0, total - 1))

        frontier = list(seeds)
        land_count = 0
        for idx in seeds:
            if self._flat[idx] == C.WATER:
                self._flat[idx] = C.PLAIN
                land_count += 1

        # croissance type "random walk / flood growth" ponderee, en
        # piochant un point de la frontiere au hasard a chaque etape
        while land_count < target and frontier:
            idx = frontier[self.rng.randrange(len(frontier))]
            neighbours = plus_sign(idx, n)
            self.rng.shuffle(neighbours)
            grown = False
            for nb in neighbours:
                if self._flat[nb] == C.WATER:
                    self._flat[nb] = C.PLAIN
                    land_count += 1
                    frontier.append(nb)
                    grown = True
                    if land_count >= target:
                        break
            if not grown:
                frontier.remove(idx)

    def _smooth_coastline(self):
        """Automate cellulaire simple : une case devient terre/eau selon
        la majorite de ses 8 voisins, pour eviter les cotes trop bruitees."""
        n = self.size
        new_flat = list(self._flat)
        for row in range(n):
            for col in range(n):
                idx = row * n + col
                land_neighbours = 0
                total_neighbours = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        r, c = row + dr, col + dc
                        if 0 <= r < n and 0 <= c < n:
                            total_neighbours += 1
                            if self._flat[r * n + c] != C.WATER:
                                land_neighbours += 1
                if total_neighbours == 0:
                    continue
                ratio = land_neighbours / total_neighbours
                if self._flat[idx] == C.WATER and ratio > 0.6:
                    new_flat[idx] = C.PLAIN
                elif self._flat[idx] != C.WATER and ratio < 0.25:
                    new_flat[idx] = C.WATER
        self._flat = new_flat

    def _grow_mountains(self, relief: float):
        """Fait pousser des montagnes en clusters sur une fraction de la
        terre disponible (relief eleve = chaines de montagnes plus grandes)."""
        n = self.size
        land_indices = [i for i, t in enumerate(self._flat) if t != C.WATER]
        if not land_indices:
            return
        target = int(len(land_indices) * relief)
        if target <= 0:
            return

        mountain_count = 0
        attempts = 0
        max_attempts = target * 10 + 50
        while mountain_count < target and attempts < max_attempts:
            attempts += 1
            seed = self.rng.choice(land_indices)
            if self._flat[seed] != C.PLAIN:
                continue
            cluster_size = self.rng.randint(1, 4)
            for idx in round_(seed, cluster_size, n):
                if 0 <= idx < n * n and self._flat[idx] == C.PLAIN:
                    self._flat[idx] = C.MOUNTAIN
                    mountain_count += 1
                    if mountain_count >= target:
                        break

    def _grow_forests(self, density: float):
        """Foret disposee en clusters (comme les montagnes) sur les cases
        encore plates."""
        n = self.size
        plain_indices = [i for i, t in enumerate(self._flat) if t == C.PLAIN]
        if not plain_indices:
            return
        target = int(len(plain_indices) * density)
        if target <= 0:
            return

        forest_count = 0
        attempts = 0
        max_attempts = target * 10 + 50
        while forest_count < target and attempts < max_attempts:
            attempts += 1
            seed = self.rng.choice(plain_indices)
            if self._flat[seed] != C.PLAIN:
                continue
            cluster_size = self.rng.randint(1, 3)
            for idx in round_(seed, cluster_size, n):
                if 0 <= idx < n * n and self._flat[idx] == C.PLAIN:
                    self._flat[idx] = C.FOREST
                    forest_count += 1
                    if forest_count >= target:
                        break

    def _place_capitals(self) -> List[int]:
        """Une capitale par quadrant, sur une case plate (PLAIN ou FOREST),
        en respectant une distance minimale entre capitales."""
        n = self.size
        min_dist = max(3, n // max(1, int(len(self.quadrants) ** 0.5) + 2))
        capitals: List[int] = []

        for x0, y0, x1, y1 in self.quadrants:
            candidates = [
                row * n + col
                for row in range(y0, min(y1, n))
                for col in range(x0, min(x1, n))
                if self._flat[row * n + col] in (C.PLAIN, C.FOREST)
            ]
            self.rng.shuffle(candidates)

            chosen = None
            for idx in candidates:
                if all(distance(idx, other, n) >= min_dist for other in capitals):
                    chosen = idx
                    break
            if chosen is None and candidates:
                chosen = candidates[0]  # fallback si le quadrant est trop petit
            if chosen is None:
                # dernier recours : force une case plate au centre du quadrant
                cx = (x0 + min(x1, n)) // 2
                cy = (y0 + min(y1, n)) // 2
                chosen = cy * n + cx
                self._flat[chosen] = C.PLAIN

            self._flat[chosen] = C.PLAIN  # une capitale n'est jamais en foret/montagne
            capitals.append(chosen)

        return capitals

    def _place_resources(self):
        """Ressources dependantes du terrain, avec un bonus de densite pres
        des capitales (comme dans le jeu, les villages/capitales ont
        souvent des ressources a portee de case)."""
        n = self.size
        near_capital = set()
        for cap in self.capitals:
            near_capital.update(round_(cap, 2, n))

        for idx, terrain in enumerate(self._flat):
            rules = RESOURCE_RULES.get(terrain)
            if not rules:
                continue
            bonus = 1.8 if idx in near_capital else 1.0
            for resource, base_proba in rules:
                if self.rng.random() < base_proba * bonus:
                    self.objects[idx] = resource
                    break  # une seule ressource par case

    # ------------------------------------------------------------------
    # Acces
    # ------------------------------------------------------------------
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.tiles[key]
        else:
            if len(key) != 2:
                raise ValueError("You must give one or two arguments.")
            return self.tiles[key[0]][key[1]]

    def __str__(self):
        symbols = {C.WATER: "~", C.PLAIN: ".", C.FOREST: "f", C.MOUNTAIN: "^"}
        lines = []
        for row in range(self.size):
            chars = []
            for col in range(self.size):
                idx = row * self.size + col
                if idx in self.capitals:
                    chars.append("C")
                elif idx in self.objects:
                    chars.append(RESOURCE_NAMES[self.objects[idx]][0].upper())
                else:
                    chars.append(symbols[self._flat[idx]])
            lines.append("".join(chars))
        return "\n".join(lines)
