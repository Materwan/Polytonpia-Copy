import constants as C
from dataclasses import dataclass
from typing import Optional

WARRIOR, RIDER, ARCHER, DEFENDER, SWORDSMAN, CATAPULT = range(6)

UNIT_NAMES = {
    WARRIOR: "warrior",
    RIDER: "rider",
    ARCHER: "archer",
    DEFENDER: "defender",
    SWORDSMAN: "swordsman",
    CATAPULT: "catapult",
}


@dataclass(frozen=True)
class UnitSpec:
    name: str
    cost: int
    attack: int
    defense: int
    max_hp: int
    move: int
    attack_range: int
    requires_tech: Optional[str] = None  # tech id needed to train this unit


UNIT_SPECS = {
    WARRIOR: UnitSpec(
        "warrior", cost=2, attack=2, defense=2, max_hp=10, move=1, attack_range=1
    ),
    RIDER: UnitSpec(
        "rider",
        cost=3,
        attack=2,
        defense=1,
        max_hp=10,
        move=2,
        attack_range=1,
        requires_tech="riding",
    ),
    ARCHER: UnitSpec(
        "archer",
        cost=3,
        attack=2,
        defense=1,
        max_hp=10,
        move=1,
        attack_range=2,
        requires_tech="archery",
    ),
    DEFENDER: UnitSpec(
        "defender",
        cost=3,
        attack=1,
        defense=3,
        max_hp=15,
        move=1,
        attack_range=1,
        requires_tech="strategy",
    ),
    SWORDSMAN: UnitSpec(
        "swordsman",
        cost=5,
        attack=3,
        defense=3,
        max_hp=15,
        move=1,
        attack_range=1,
        requires_tech="smithery",
    ),
    CATAPULT: UnitSpec(
        "catapult",
        cost=6,
        attack=4,
        defense=1,
        max_hp=10,
        move=1,
        attack_range=3,
        requires_tech="mathematics",
    ),
}

N_UNIT_TYPES = len(UNIT_SPECS)
