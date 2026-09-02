"""
Point d'entree du jeu : demande le nombre de joueurs, leur tribu et la
taille de la carte, puis lance une boucle de jeu textuelle simple.

Commandes disponibles pendant un tour :
    status                          affiche l'etat de la partie
    map                             affiche la carte
    build <ville_id> <case> <nom>   construit un batiment (ex: build 0 42 farm)
    train <ville_id> <nom_unite>    entraine une unite (ex: train 0 warrior)
    research <tech>                 recherche une technologie (ex: research forestry)
    buildings                       liste les batiments disponibles
    units                           liste les types d'unites disponibles
    end                             termine le tour du joueur courant
    quit                            quitte la partie
"""

import constants as C
from game import Game
from buildings import BUILDING_SPECS
from units import UNIT_SPECS


def ask_int(prompt: str, min_value: int, max_value: int) -> int:
    while True:
        raw = input(f"{prompt} ({min_value}-{max_value}) : ").strip()
        if raw.isdigit() and min_value <= int(raw) <= max_value:
            return int(raw)
        print("Valeur invalide, reessaie.")


def ask_choice(prompt: str, options: list) -> str:
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    while True:
        raw = input("Choix : ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Choix invalide, reessaie.")


def setup_game() -> Game:
    print("=== Nouvelle partie ===")
    n_players = ask_int("Nombre de joueurs", 2, 8)

    player_names = []
    tribes = []
    tribe_names = list(C.TRIBES.keys())
    for i in range(n_players):
        name = input(f"Nom du joueur {i + 1} : ").strip() or f"Joueur {i + 1}"
        tribe = ask_choice(f"Tribu de {name} :", tribe_names)
        player_names.append(name)
        tribes.append(tribe)

    map_size_name = ask_choice("Taille de la carte :", list(C.MAP_SIZES.keys()))

    game = Game()
    game.setup(player_names, tribes, map_size_name)
    return game


def print_buildings():
    print("Batiments disponibles :")
    for spec in BUILDING_SPECS.values():
        if spec.is_level_reward:
            continue
        tech = f", tech: {spec.requires_tech}" if spec.requires_tech else ""
        print(f"  {spec.name:<16} cout {spec.cost:<3} pop +{spec.population}{tech}")


def print_units():
    print("Unites disponibles :")
    for spec in UNIT_SPECS.values():
        tech = f", tech: {spec.requires_tech}" if spec.requires_tech else ""
        print(
            f"  {spec.name:<12} cout {spec.cost:<3} atk {spec.attack} def {spec.defense} pv {spec.max_hp}{tech}"
        )


def run_console(game: Game) -> None:
    print(
        "\nPartie prete ! Tape 'buildings' ou 'units' pour voir les options, 'end' pour finir ton tour.\n"
    )
    income = game.start_turn()
    print(f"{game.current_player.name} collecte {income} etoiles.")

    while not game.finished:
        try:
            raw = input(f"[{game.current_player.name}] > ").strip()
        except EOFError:
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "quit":
            break

        elif cmd == "status":
            print(game.status())

        elif cmd == "map":
            print(game.map)

        elif cmd == "buildings":
            print_buildings()

        elif cmd == "units":
            print_units()

        elif cmd == "build" and len(parts) == 4:
            city_id, tile_idx, name = int(parts[1]), int(parts[2]), parts[3]
            ok, msg = game.build(city_id, tile_idx, name)
            print(msg)

        elif cmd == "train" and len(parts) == 3:
            city_id, name = int(parts[1]), parts[2]
            ok, msg = game.train(city_id, name)
            print(msg)

        elif cmd == "research" and len(parts) == 2:
            ok, msg = game.research(parts[1])
            print(msg)

        elif cmd == "end":
            game.end_turn()
            if game.finished:
                break
            income = game.start_turn()
            print(f"\n--- Tour {game.turn_number} : {game.current_player.name} ---")
            print(f"{game.current_player.name} collecte {income} etoiles.")

        else:
            print(
                "Commande inconnue. Options : status, map, buildings, units, "
                "build <ville> <case> <batiment>, train <ville> <unite>, "
                "research <tech>, end, quit."
            )

    if game.finished:
        alive = [p for p in game.players if not p.is_eliminated()]
        if alive:
            print(f"\nPartie terminee ! Vainqueur : {alive[0].name} ({alive[0].tribe})")
        else:
            print("\nPartie terminee, aucun survivant.")
    else:
        print("\nPartie interrompue.")


if __name__ == "__main__":
    game = setup_game()
    run_console(game)
