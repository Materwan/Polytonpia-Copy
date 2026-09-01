"""
Définition des unités et de leurs règles de fonctionnement
(déplacement, attaque, embarquement naval...).

Ce module reste volontairement générique : les valeurs (cout, attaque,
defense, pv...) sont des approximations "jouables" inspirées des grandes
lignes du genre 4X/Polytopia-like, pas une reproduction exacte d'un jeu
existant. Libre à toi d'ajuster les chiffres dans UNIT_SPECS.
"""

import constants as C
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple

from utils import distance, plus_sign

# ---------------------------------------------------------------------------
# Identifiants des unités
# ---------------------------------------------------------------------------
(
    WARRIOR,
    RIDER,
    ARCHER,
    DEFENDER,
    SWORDSMAN,
    CATAPULT,
    KNIGHT,
    MIND_BENDER,
    GIANT,
    POLYTAUR,
    DAGGER,
    CLOAK,
    DRAGON_EGG,
    BABY_DRAGON,
    FIRE_DRAGON,
    # unités navales / amphibies
    RAFT,
    SCOUT,
    RAMMER,
    BOMBER,
    BATTLESHIP,
) = range(20)

UNIT_NAMES = {
    WARRIOR: "warrior",
    RIDER: "rider",
    ARCHER: "archer",
    DEFENDER: "defender",
    SWORDSMAN: "swordsman",
    CATAPULT: "catapult",
    KNIGHT: "knight",
    MIND_BENDER: "mind_bender",
    GIANT: "giant",
    POLYTAUR: "polytaur",
    DAGGER: "dagger",
    CLOAK: "cloak",
    DRAGON_EGG: "dragon_egg",
    BABY_DRAGON: "baby_dragon",
    FIRE_DRAGON: "fire_dragon",
    RAFT: "raft",
    SCOUT: "scout",
    RAMMER: "rammer",
    BOMBER: "bomber",
    BATTLESHIP: "battleship",
}


class Domain(Enum):
    """Milieu dans lequel l'unité peut se déplacer."""

    LAND = auto()
    NAVAL = auto()
    AIR = auto()  # ex: dragons, vole au dessus de tout
    AMPHIBIOUS = auto()  # peut entrer sur l'eau ET la terre (ex: futur usage)


class MoveClass(Enum):
    """Classe de mouvement, utile pour les capacités spéciales
    (ex: le Cloak/Dagger peuvent traverser du terrain autrement infranchissable)."""

    NORMAL = auto()
    STEALTH = auto()  # invisible tant qu'il ne bouge pas à côté d'un ennemi
    SIEGE = auto()  # bonus contre les villes, malus contre unités hors ville


@dataclass(frozen=True)
class UnitSpec:
    name: str
    cost: int
    attack: int
    defense: int
    max_hp: int
    move: int
    attack_range: int
    domain: Domain = Domain.LAND
    move_class: MoveClass = MoveClass.NORMAL
    requires_tech: Optional[str] = None  # tech nécessaire pour entraîner l'unité
    is_healer: bool = False  # ex: Mind Bender
    convert_enemy: bool = False  # capacité de conversion (Mind Bender)
    can_carry_units: bool = False  # transport naval (Raft, Battleship...)
    carry_capacity: int = 0
    splash_damage: bool = False  # dégâts de zone (Catapult, Bomber)
    ignores_defense_terrain: bool = (
        False  # ex: Giant ignore le bonus de terrain défensif
    )


UNIT_SPECS: Dict[int, UnitSpec] = {
    # ------------------------------------------------------------------
    # Unités terrestres de base
    # ------------------------------------------------------------------
    WARRIOR: UnitSpec(
        "warrior",
        cost=2,
        attack=2,
        defense=2,
        max_hp=10,
        move=1,
        attack_range=1,
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
        move_class=MoveClass.SIEGE,
        splash_damage=True,
    ),
    # ------------------------------------------------------------------
    # Unités avancées
    # ------------------------------------------------------------------
    KNIGHT: UnitSpec(
        "knight",
        cost=6,
        attack=3,
        defense=1,
        max_hp=15,
        move=3,
        attack_range=1,
        requires_tech="chivalry",
    ),
    MIND_BENDER: UnitSpec(
        "mind_bender",
        cost=5,
        attack=0,
        defense=1,
        max_hp=10,
        move=1,
        attack_range=1,
        requires_tech="meditation",
        is_healer=True,
        convert_enemy=True,
    ),
    GIANT: UnitSpec(
        "giant",
        cost=20,
        attack=5,
        defense=4,
        max_hp=40,
        move=1,
        attack_range=1,
        requires_tech="ramming",  # unité "épique" typiquement issue d'une ruine
        ignores_defense_terrain=True,
    ),
    POLYTAUR: UnitSpec(
        "polytaur",
        cost=9,
        attack=3,
        defense=2,
        max_hp=15,
        move=2,
        attack_range=1,
        requires_tech="riding",
    ),
    DAGGER: UnitSpec(
        "dagger",
        cost=6,
        attack=2,
        defense=1,
        max_hp=10,
        move=1,
        attack_range=1,
        domain=Domain.NAVAL,
        requires_tech="navigation",
        move_class=MoveClass.STEALTH,
    ),
    CLOAK: UnitSpec(
        "cloak",
        cost=9,
        attack=1,
        defense=1,
        max_hp=10,
        move=1,
        attack_range=1,
        requires_tech="smithery",
        move_class=MoveClass.STEALTH,
    ),
    # ------------------------------------------------------------------
    # Ligne des dragons
    # ------------------------------------------------------------------
    DRAGON_EGG: UnitSpec(
        "dragon_egg",
        cost=9,
        attack=0,
        defense=3,
        max_hp=15,
        move=1,
        attack_range=0,
        requires_tech="spiritualism",
    ),
    BABY_DRAGON: UnitSpec(
        "baby_dragon",
        cost=0,
        attack=4,
        defense=4,
        max_hp=20,
        move=2,
        attack_range=1,
        domain=Domain.AIR,
        requires_tech="spiritualism",
    ),
    FIRE_DRAGON: UnitSpec(
        "fire_dragon",
        cost=0,
        attack=6,
        defense=4,
        max_hp=25,
        move=3,
        attack_range=2,
        domain=Domain.AIR,
        requires_tech="spiritualism",
        splash_damage=True,
    ),
    # ------------------------------------------------------------------
    # Unités navales
    # ------------------------------------------------------------------
    RAFT: UnitSpec(
        "raft",
        cost=0,
        attack=0,
        defense=1,
        max_hp=10,
        move=2,
        attack_range=0,
        domain=Domain.NAVAL,
        can_carry_units=True,
        carry_capacity=1,
    ),
    SCOUT: UnitSpec(
        "scout",
        cost=5,
        attack=1,
        defense=1,
        max_hp=10,
        move=3,
        attack_range=1,
        domain=Domain.NAVAL,
        requires_tech="navigation",
        can_carry_units=True,
        carry_capacity=1,
    ),
    RAMMER: UnitSpec(
        "rammer",
        cost=4,
        attack=3,
        defense=1,
        max_hp=10,
        move=3,
        attack_range=1,
        domain=Domain.NAVAL,
        requires_tech="navigation",
        can_carry_units=True,
        carry_capacity=1,
    ),
    BOMBER: UnitSpec(
        "bomber",
        cost=8,
        attack=3,
        defense=1,
        max_hp=10,
        move=2,
        attack_range=3,
        domain=Domain.NAVAL,
        requires_tech="navigation",
        can_carry_units=True,
        carry_capacity=1,
        splash_damage=True,
    ),
    BATTLESHIP: UnitSpec(
        "battleship",
        cost=12,
        attack=4,
        defense=4,
        max_hp=20,
        move=2,
        attack_range=1,
        domain=Domain.NAVAL,
        requires_tech="navigation",
        can_carry_units=True,
        carry_capacity=2,
    ),
}

N_UNIT_TYPES = len(UNIT_SPECS)

NAVAL_UNIT_TYPES = {RAFT, SCOUT, RAMMER, BOMBER, BATTLESHIP}
LAND_UNIT_TYPES = {t for t, s in UNIT_SPECS.items() if s.domain == Domain.LAND}
AIR_UNIT_TYPES = {t for t, s in UNIT_SPECS.items() if s.domain == Domain.AIR}

# unité navale de base -> upgrade obtenu quand l'unité embarquée gagne un
# niveau (mécanique "level up" façon Polytopia : Raft -> Scout/Rammer/Bomber -> Battleship)
NAVAL_UPGRADE_PATH = {
    RAFT: [SCOUT, RAMMER, BOMBER],
    SCOUT: [BATTLESHIP],
    RAMMER: [BATTLESHIP],
    BOMBER: [BATTLESHIP],
}


# ---------------------------------------------------------------------------
# Instance d'unité (état de jeu, distinct de sa "spec" statique)
# ---------------------------------------------------------------------------
@dataclass
class Unit:
    unit_type: int
    owner: int  # id du joueur
    position: int  # index plat sur la carte
    hp: int = field(init=False)
    has_moved: bool = False
    has_attacked: bool = False
    veteran: bool = False  # a déjà tué une unité -> bonus
    kills: int = 0
    carried_unit: Optional["Unit"] = None  # unité transportée si bateau

    def __post_init__(self):
        self.hp = self.spec.max_hp

    @property
    def spec(self) -> UnitSpec:
        return UNIT_SPECS[self.unit_type]

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def effective_attack(self) -> int:
        base = self.spec.attack
        if self.veteran:
            base += 1
        return base

    @property
    def effective_defense(self) -> int:
        base = self.spec.defense
        if self.veteran:
            base += 1
        return base

    def reset_turn(self):
        """A appeler en début de tour pour ce joueur."""
        self.has_moved = False
        self.has_attacked = False


# ---------------------------------------------------------------------------
# Règles de déplacement
# ---------------------------------------------------------------------------
def terrain_move_cost(terrain: int, spec: UnitSpec) -> Optional[int]:
    """Coût en points de mouvement pour entrer sur une case de ce terrain.
    Retourne None si le terrain est infranchissable pour cette unité."""
    if spec.domain == Domain.AIR:
        # les unités volantes ignorent le relief et l'eau
        return 1

    if terrain == C.WATER:
        if spec.domain == Domain.NAVAL:
            return 1
        # une unité terrestre ne peut entrer sur l'eau que si elle est
        # embarquée (voir `board_ship` / `Unit.carried_unit`)
        return None

    if spec.domain == Domain.NAVAL:
        # un bateau ne peut pas s'aventurer sur la terre ferme
        return None

    if terrain == C.MOUNTAIN:
        # les montagnes coûtent tout le mouvement restant (comme dans
        # l'original) sauf pour certaines unités qui ignorent le terrain
        return 2 if not spec.ignores_defense_terrain else 1

    return 1  # plaine, forêt...


def can_enter_tile(
    unit: Unit, dest_terrain: int, dest_occupied_by: Optional[Unit]
) -> bool:
    """Vérifie qu'une unité peut légalement entrer sur une case."""
    if dest_occupied_by is not None and dest_occupied_by.owner != unit.owner:
        return False  # il faut attaquer, pas marcher dessus

    cost = terrain_move_cost(dest_terrain, unit.spec)
    if cost is None:
        return False

    if dest_occupied_by is not None and dest_occupied_by.owner == unit.owner:
        # une case alliée est franchissable seulement si c'est un bateau
        # avec de la place (embarquement) ou l'inverse (débarquement)
        return _can_stack_for_transport(unit, dest_occupied_by)

    return True


def _can_stack_for_transport(mover: Unit, other: Unit) -> bool:
    """Un bateau et une unité terrestre peuvent partager une case le temps
    d'un embarquement/débarquement."""
    if mover.spec.can_carry_units and other.spec.domain == Domain.LAND:
        return other.carried_unit is None if hasattr(other, "carried_unit") else True
    if other.spec.can_carry_units and mover.spec.domain == Domain.LAND:
        return other.carried_unit is None
    return False


def reachable_tiles(unit: Unit, game_map, occupied: Dict[int, Unit]) -> List[int]:
    """BFS simple limité par les points de mouvement de l'unité.
    `game_map` doit exposer `.size` et permettre `game_map[idx]` (terrain).
    `occupied` associe index -> Unit présente sur la carte (bateaux compris)."""
    n = game_map.size
    frontier = [(unit.position, unit.spec.move)]
    visited = {unit.position: unit.spec.move}
    reachable = []

    while frontier:
        idx, remaining = frontier.pop()
        for nb in plus_sign(idx, n):
            row, col = nb // n, nb % n
            terrain = game_map[row, col] if hasattr(game_map, "__getitem__") else None
            occupant = occupied.get(nb)
            cost = terrain_move_cost(terrain, unit.spec) if terrain is not None else 1
            if cost is None or cost > remaining:
                continue
            if occupant is not None and occupant.owner != unit.owner:
                continue  # on ne traverse pas les unités ennemies
            new_remaining = remaining - cost
            if nb not in visited or visited[nb] < new_remaining:
                visited[nb] = new_remaining
                reachable.append(nb)
                frontier.append((nb, new_remaining))

    return reachable


# ---------------------------------------------------------------------------
# Règles de combat
# ---------------------------------------------------------------------------
def in_attack_range(attacker: Unit, target: Unit, map_size: int) -> bool:
    return (
        distance(attacker.position, target.position, map_size)
        <= attacker.spec.attack_range
    )


def resolve_combat(
    attacker: Unit, defender: Unit, terrain_defense_bonus: float = 1.0
) -> Tuple[int, int]:
    """Calcule les dégâts infligés dans les deux sens, façon Polytopia :
    dégâts proportionnels au ratio attaque/défense et aux HP restants.
    Retourne (dégâts subis par le défenseur, dégâts de riposte subis par l'attaquant).

    `terrain_defense_bonus` : multiplicateur de défense dû au terrain
    (ex: 1.5 en forêt, 1.5 sur montagne), à fournir par l'appelant selon la
    case du défenseur. Ignoré si `defender` a `ignores_defense_terrain`
    côté attaquant (cas du Giant qui l'ignore lui-même, pas le défenseur).
    """
    atk = attacker.effective_attack * (attacker.hp / attacker.spec.max_hp)
    dfs = defender.effective_defense * (defender.hp / defender.spec.max_hp)
    if not attacker.spec.ignores_defense_terrain:
        dfs *= terrain_defense_bonus

    total = atk + dfs
    if total == 0:
        return 0, 0

    # dégâts au défenseur
    defender_damage = round(attacker.spec.attack * (atk / total))
    defender_damage = min(defender_damage, defender.hp)

    # riposte : seulement si le défenseur est encore en vie, à portée 1,
    # et que ce n'est pas une attaque à distance (range > 1) subie par le défenseur
    counter_damage = 0
    if defender.hp - defender_damage > 0 and attacker.spec.attack_range == 1:
        counter_damage = round(defender.spec.defense * (dfs / total))
        counter_damage = min(counter_damage, attacker.hp)

    return defender_damage, counter_damage


def apply_combat(
    attacker: Unit, defender: Unit, terrain_defense_bonus: float = 1.0
) -> None:
    """Applique le combat : modifie les HP en place et gère les morts,
    la promotion "vétéran" et les dégâts de zone (splash) sont à gérer par
    l'appelant pour les unités secondaires touchées."""
    dmg_to_def, dmg_to_atk = resolve_combat(attacker, defender, terrain_defense_bonus)
    defender.hp = max(0, defender.hp - dmg_to_def)
    attacker.hp = max(0, attacker.hp - dmg_to_atk)

    if not defender.is_alive:
        attacker.veteran = True
        attacker.kills += 1
    if not attacker.is_alive and defender.is_alive:
        defender.veteran = True
        defender.kills += 1

    attacker.has_attacked = True


# ---------------------------------------------------------------------------
# Règles navales : embarquement / débarquement
# ---------------------------------------------------------------------------
def board_ship(land_unit: Unit, ship: Unit) -> bool:
    """Fait monter une unité terrestre à bord d'un bateau si celui-ci a
    de la place et se trouve sur une case adjacente ou identique."""
    if not ship.spec.can_carry_units:
        return False
    if ship.carried_unit is not None:
        return False  # capacité simplifiée : 1 unité "active" transportée
    if land_unit.spec.domain != Domain.LAND:
        return False

    ship.carried_unit = land_unit
    land_unit.position = ship.position
    return True


def disembark(
    ship: Unit,
    dest_terrain: int,
    dest_index: int,
    dest_occupied_by: Optional[Unit] = None,
) -> bool:
    """Fait débarquer l'unité transportée sur une case de terre valide."""
    land_unit = ship.carried_unit
    if land_unit is None:
        return False
    if dest_terrain == C.WATER:
        return False
    if not can_enter_tile(land_unit, dest_terrain, dest_occupied_by):
        return False

    land_unit.position = dest_index
    ship.carried_unit = None
    return True


def maybe_upgrade_ship(ship: Unit, preferred_type: Optional[int] = None) -> Unit:
    """Mécanique façon Polytopia : un navire "de base" (Raft) qui survit à
    un combat, ou dont le passager gagne assez d'expérience, peut être
    remplacé par une variante plus solide (Scout/Rammer/Bomber -> Battleship).
    Retourne l'unité navale à utiliser à partir de maintenant (peut être la
    même si aucune amélioration n'est possible)."""
    upgrades = NAVAL_UPGRADE_PATH.get(ship.unit_type)
    if not upgrades:
        return ship

    new_type = preferred_type if preferred_type in (upgrades or []) else upgrades[0]
    upgraded = Unit(unit_type=new_type, owner=ship.owner, position=ship.position)
    upgraded.hp = upgraded.spec.max_hp
    upgraded.carried_unit = ship.carried_unit
    upgraded.veteran = ship.veteran
    upgraded.kills = ship.kills
    return upgraded
