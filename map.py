from typing import Tuple, List, Dict
from dataclasses import dataclass
import numpy as np
from perlin_numpy import generate_perlin_noise_2d

import constants as C


@dataclass
class MapType:

    size: Tuple[int, int]


class Map:

    tiles: List[List[int]]

    def __init__(self, map_type: MapType):
        self.map_type = map_type
        self.objects = List[Dict[Tuple[int, int], int]]
        self.units = List[Dict[Tuple[int, int], int]]

        self._generate_map()

    def _generate_map(self):

        noise = generate_perlin_noise_2d(self.map_type.size, (8, 8))
        noise: np.ndarray = generate_perlin_noise_2d((256, 256), (4, 4))
        # mountains = (noise > 0.5).astype(float)
        # forest = (noise > 0 and noise < 0.5).astype(float) * 0.5
        # plain = (noise > -0.5 and noise < 0).astype(float)
        # water = (noise <= -0.5).astype(float)
        map = np.zeros((256, 256))
        map = np.where(noise > -0.5, 1, map)
        map = np.where(noise > 0, 2, map)
        map = np.where(noise > 0.5, 3, map)

        self.tiles = [[0] * self.map_type.size[0] for _ in range(self.map_type.size[1])]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.tiles[key]
        else:
            if len(key) != 2:
                raise ValueError("You must give one or two arguments.")
            return self.tiles[key[0]][key[1]]

    def __str__(self):

        return "\n".join([str(row) for row in self.tiles])
