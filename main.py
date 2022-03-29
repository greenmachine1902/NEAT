from __future__ import annotations

import os
import pygame as pg
import random

from connect4 import Connect4
from connect4 import visualize
from neat import NEAT

import mattslib as ml
import mattslib.pygame as mlpg

__version__ = '1.5.1'
__date__ = '29/03/2022'

# Constants
WIDTH, HEIGHT = 1120, 640
GAME_PANEL = (HEIGHT, HEIGHT)
ADDON_PANEL = (WIDTH - GAME_PANEL[0], HEIGHT)
NETWORK_BOX = (ADDON_PANEL[0], ADDON_PANEL[1] * (1 / 2))
INFO_BOX = (ADDON_PANEL[0], 80)
MENU_WIDTH, MENU_HEIGHT = ADDON_PANEL[0], NETWORK_BOX[1] - INFO_BOX[1]
OPTION_WIDTH, OPTION_HEIGHT = WIDTH, HEIGHT

FPS = 40
display = True

GAME = 'connect4'
PLAYER_TYPES = ['Human', 'NEAT', '1', '1000', '6000']
SHOW_EVERY = ['Genome', 'Generation', 'None']
SPEEDS = [1, 5, 25, 100, 500]
DIRECTORY = os.path.dirname(os.path.realpath(__file__))


# Globals - Defaults
players = {1: PLAYER_TYPES[1], 2: PLAYER_TYPES[1]}
neats = {1: None, 2: None}
game_speed = SPEEDS[-1]
evolution_speed = SPEEDS[-1]
show_every = SHOW_EVERY[1]
max_fps = max(FPS, max(game_speed, evolution_speed))

# Globals - Pygame
if display:
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,30"
    pg.init()
    display = pg.display.set_mode((WIDTH, HEIGHT), depth=32)

    pg.display.set_caption("Connect 4 with NEAT - v" + __version__)
    game_display = pg.Surface(GAME_PANEL)
    network_display = pg.Surface(NETWORK_BOX)
    info_display = pg.Surface(INFO_BOX)
    menu_display = pg.Surface((MENU_WIDTH, MENU_HEIGHT))
    options_display = pg.Surface((OPTION_WIDTH, OPTION_HEIGHT))
    display.fill(mlpg.BLACK)
    clock = pg.time.Clock()

connect4 = Connect4(GAME_PANEL)
network = None
info = None
menu = None
options = None


def getSpeedShow(current_player: int) -> tuple:
    """
    Returns that speed and show values depending on neat details.
    :param current_player: int
    :return:
        - speed, show - tuple[int, bool]
    """
    if players[current_player] != PLAYER_TYPES[0]:
        if show_every == 'Generation':
            for player_id in [current_player, connect4.PLAYERS[connect4.opponent]['id']]:
                if neats[player_id] is not None:
                    if neats[player_id].current_species == 0 and neats[player_id].current_genome == 0:
                        return game_speed, True
            return evolution_speed, False
        elif show_every == 'None':
            return evolution_speed, False
    return game_speed, True


def setupAi(player_id: int, inputs: int = 4, outputs: int = 1, population: int = 100) -> NEAT:
    """
    Sets up neat with game settings in mind.
    :rtype: object
    :param player_id: int
    :param inputs: int
    :param outputs: int
    :param population: int
    :return:
        - neat - NEAT
    """
    if players[player_id] == PLAYER_TYPES[1]:
        if os.path.isfile(f"{DIRECTORY}\\{GAME}\\ai_{player_id}.neat"):
            neat = NEAT.load(f"ai_{player_id}", f"{DIRECTORY}\\{GAME}")
            return neat
    else:
        if os.path.isfile(f"{DIRECTORY}\\{GAME}\\ai_{player_id}_gen_{players[player_id]}.neat"):
            neat = NEAT.load(f"ai_{player_id}_gen_{players[player_id]}", f"{DIRECTORY}\\{GAME}")
            return neat
    neat = NEAT(DIRECTORY, f"\\{GAME}")
    neat.generate(inputs, outputs, population=population)
    return neat


def neatMove(genome: Genome) -> int:
    """
    Calculates the best move for the current genome to make.
    :param genome: Genome
    :return:
        - move - int
    """
    possible_moves = {}
    for i in range(connect4.COLUMNS):
        possible_move = connect4.getPossibleMove(i)
        if possible_move[0] != connect4.INVALID_MOVE:
            possible_moves[possible_move] = 0
    for possible_move in possible_moves:
        directions, _ = connect4.getPieceSlices(possible_move)
        for direction_pair in directions:
            for direction in directions[direction_pair]:
                if directions[direction_pair][direction] is not None:
                    inputs = directions[direction_pair][direction]
                    possible_moves[possible_move] += sum(genome.forward(inputs))
    sorted_moves = ml.dict.combineByValues(possible_moves)
    max_min_keys = ml.list.findMaxMin(list(sorted_moves.keys()))
    move = random.choice(sorted_moves[max_min_keys['max']['value']])
    return move[1]


def setup() -> None:
    """
    Sets up the global variables and neat players.
    :return:
        - None
    """
    global connect4, network, info, menu, options, players, neats
    connect4 = Connect4(GAME_PANEL)
    network = visualize.Network(NETWORK_BOX)
    info = visualize.Info(INFO_BOX)
    options = Options()
    menu = Menu()
    for player_id in players:
        neats[player_id] = None
        if players[player_id] != PLAYER_TYPES[0]:
            neats[player_id] = setupAi(player_id)


def close() -> None:
    """
    Closes and quits pygame and python.
    :return:
        - None
    """
    for player_id in players:
        if players[player_id] == PLAYER_TYPES[1]:
            neats[player_id].save(f"\\ai_{player_id}")
    pg.quit()
    quit()


class Menu:
    """
    Menu is a class that allows buttons to be accessed during the main loop and handles the assigned action.
    """

    BOARDER = 30

    def __init__(self):
        self.colour = {'background': mlpg.WHITE}

        self.buttons = [
            mlpg.Button("Reset", (MENU_WIDTH * (1 / 3), MENU_HEIGHT * (1 / 3)), mlpg.GREY, handler=connect4.reset),
            mlpg.Button("Options", (MENU_WIDTH * (2 / 3), MENU_HEIGHT * (1 / 3)), mlpg.GREY, handler=options.main),
            mlpg.Button("Switch", (MENU_WIDTH * (1 / 3), MENU_HEIGHT * (2 / 3)), mlpg.GREY,
                        handler=connect4.switchPlayer),
            mlpg.Button("QUIT", (MENU_WIDTH * (2 / 3), MENU_HEIGHT * (2 / 3)), mlpg.GREY, handler=close)]

        self.update()

    def update(self, *args: Any) -> None:
        """
        Updates the menu buttons and passes environment information.
        :param args: Any
        :return:
            - None
        """
        if len(args) == 2:
            for button in self.buttons:
                button.update(args[0], args[1], origin=(GAME_PANEL[0], ADDON_PANEL[1] - MENU_HEIGHT))

    def draw(self, surface: Any) -> None:
        """
        Draws the background and buttons to the given surface.
        :param surface: Any
        :return:
            - None
        """
        surface.fill(self.colour['background'])
        for button in self.buttons:
            button.draw(surface)


class Options:
    """
    Options handles changing the global variables like a settings menu.
    """
    BOARDER = 60

    def __init__(self):
        self.colour = {'background': mlpg.WHITE}

        self.players = {}
        self.buttons = {}
        self.group_buttons = {}
        self.messages = []

        self.update()

    def generate(self) -> None:
        """
        Generates the options messages and buttons with default and global values.
        :return:
            - None
        """
        self.buttons = {'back': mlpg.Button("Back", (OPTION_WIDTH * (2 / 5), OPTION_HEIGHT * (5 / 6)),
                                            mlpg.GREY, handler=True),
                        'quit': mlpg.Button("QUIT", (OPTION_WIDTH * (3 / 5), OPTION_HEIGHT * (5 / 6)),
                                            mlpg.GREY, handler=close)}
        self.messages = []

        gbi = {'Player 1:': {'selected': players[1], 'options': PLAYER_TYPES},
               'Player 2:': {'selected': players[2], 'options': PLAYER_TYPES},
               'Game Speed:': {'selected': game_speed, 'options': SPEEDS},
               'Evolution Speed:': {'selected': evolution_speed, 'options': SPEEDS},
               'Show Every:': {'selected': show_every, 'options': SHOW_EVERY}}
        for group_key in gbi:
            button_states = [True if option == gbi[group_key]['selected'] else False
                             for option in gbi[group_key]['options']]
            self.group_buttons[group_key] = mlpg.ButtonGroup(gbi[group_key]['options'],
                                                             (self.BOARDER + (OPTION_WIDTH * (1 / 6) + 100),
                                                              self.BOARDER + (len(self.messages) * 90)),
                                                             mlpg.GREY, mlpg.GREEN, button_states=button_states)
            self.messages.append(mlpg.Message(group_key, (self.BOARDER + (OPTION_WIDTH * (1 / 6)),
                                                          self.BOARDER + (len(self.messages) * 90)), align='mr'))

    def update(self, mouse_pos: tuple = None, mouse_clicked: bool = False) -> bool:
        """
        Updates the option buttons, global variables and other related attributes.
        :param mouse_pos: tuple[int, int]
        :param mouse_clicked: bool
        :return:
            - continue - bool
        """
        global players, game_speed, evolution_speed, max_fps, show_every
        self.generate()
        if mouse_pos is not None:
            for button_key in self.buttons:
                action = self.buttons[button_key].update(mouse_pos, mouse_clicked)
                if action is not None:
                    return True

        if players[1] != PLAYER_TYPES[1] or players[2] != PLAYER_TYPES[1]:
            evolution_speed = SPEEDS[0]
            show_every = SHOW_EVERY[0]
            self.group_buttons['Evolution Speed:'].update(active=False)
            self.group_buttons['Show Every:'].update(active=False)
        else:
            if game_speed > evolution_speed:
                evolution_speed = game_speed
            self.group_buttons['Evolution Speed:'].update(active=True)
            self.group_buttons['Show Every:'].update(active=True)

        if players[1] == PLAYER_TYPES[0] or players[2] == PLAYER_TYPES[0]:
            game_speed = SPEEDS[0]
            self.group_buttons['Game Speed:'].update(active=False)
        else:
            self.group_buttons['Game Speed:'].update(active=True)

        if mouse_pos is not None:
            for group in self.group_buttons:
                button_key = self.group_buttons[group].update(mouse_pos, mouse_clicked)
                if button_key is not None and self.group_buttons[group].active:
                    if group in ['Player 1:', 'Player 2:']:
                        if button_key == 0:
                            game_speed = SPEEDS[0]
                            show_every = SHOW_EVERY[0]
                        players[int(group[-2])] = PLAYER_TYPES[button_key]
                        if button_key != 1:
                            game_speed = SPEEDS[0]
                            show_every = SHOW_EVERY[0]
                        setup()
                    elif group == 'Game Speed:':
                        game_speed = SPEEDS[button_key]
                    elif group == 'Evolution Speed:':
                        evolution_speed = SPEEDS[button_key] if game_speed <= SPEEDS[button_key] else game_speed
                    elif group == 'Show Every:':
                        show_every = SHOW_EVERY[0]
                        if players[1] == players[2] == PLAYER_TYPES[1]:
                            show_every = SHOW_EVERY[button_key]

                    max_fps = max(FPS, max(game_speed, evolution_speed))

    def draw(self, surface: Any) -> None:
        """
        Draws the option buttons and texts to the surface.
        :param surface: Any
            - None
        :return:
        """
        surface.fill(self.colour['background'])
        for message in self.messages:
            message.draw(surface)
        for group in self.group_buttons:
            self.group_buttons[group].draw(surface)
        for button_keys in self.buttons:
            self.buttons[button_keys].draw(surface)

    def main(self) -> bool:
        """
        Main is the main loop for the options state and will display, update and check
        collisions with objects.
        :return:
            - continue - bool
        """
        global display, options_display
        run, typing = True, False
        while run:
            mouse_clicked = False
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    close()
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouse_clicked = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        close()
                    if typing:
                        if event.key in [pg.K_1, pg.K_KP1]:
                            pass
            mouse_pos = pg.mouse.get_pos()
            if self.update(mouse_pos, mouse_clicked) is not None:
                return True

            self.draw(options_display)
            display.blit(options_display, (0, 0))

            pg.display.update()
            clock.tick(FPS)


def main() -> None:
    """
    Main is the main loop for the project and will display, update and check
    collisions with objects.
    :return:
        - None
    """
    global display, connect4, network, info, menu, options

    setup()

    frame_count, speed, show = 1, game_speed, True
    run = True
    while run:
        current_player = connect4.PLAYERS[connect4.current_player]['id']
        speed, show = getSpeedShow(current_player)

        possible_move = None
        mouse_clicked = False
        if display:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    close()
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouse_clicked = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        close()
                    if connect4.match and players[current_player] == PLAYER_TYPES[0]:
                        if event.key in [pg.K_1, pg.K_KP1]:
                            possible_move = 0
                        elif event.key in [pg.K_2, pg.K_KP2]:
                            possible_move = 1
                        elif event.key in [pg.K_3, pg.K_KP3]:
                            possible_move = 2
                        elif event.key in [pg.K_4, pg.K_KP4]:
                            possible_move = 3
                        elif event.key in [pg.K_5, pg.K_KP5]:
                            possible_move = 4
                        elif event.key in [pg.K_6, pg.K_KP6]:
                            possible_move = 5
                        elif event.key in [pg.K_7, pg.K_KP7]:
                            possible_move = 6
                if possible_move is not None:
                    break

            mouse_pos = pg.mouse.get_pos()
            menu.update(mouse_pos, mouse_clicked)

        if connect4.match:
            if players[current_player] != PLAYER_TYPES[0]:
                if frame_count >= max_fps / speed:
                    frame_count = 1

                    if players[current_player] == PLAYER_TYPES[1] and neats[current_player].shouldEvolve():
                        current_genome = neats[current_player].getGenome()
                    else:
                        current_genome = neats[current_player].best_genome

                    possible_move = neatMove(current_genome)
                    connect4.main(possible_move)

                    if show and display:
                        network.generate(current_genome)
                        info.update(neats[current_player].getInfo())

            elif players[current_player] == PLAYER_TYPES[0]:
                if possible_move is not None:
                    connect4.main(possible_move)
                    if not connect4.match:
                        frame_count = 1

        if not connect4.match:
            if frame_count >= max_fps / speed:
                fitness = connect4.fitnessEvaluation()
                for i, player_key in enumerate([current_player, connect4.PLAYERS[connect4.opponent]['id']]):
                    if players[player_key] == PLAYER_TYPES[1] and neats[player_key].shouldEvolve():
                        current_genome = neats[player_key].getGenome()
                        current_genome.fitness = fitness[i]
                        neats[player_key].nextGenome(f"ai_{player_key}")
                connect4.reset()

        if display:
            menu.draw(menu_display)
            display.blit(menu_display, (GAME_PANEL[0], GAME_PANEL[1] - MENU_HEIGHT))

            if show or players[current_player] == PLAYER_TYPES[0]:
                connect4.draw(game_display)
                network.draw(network_display)
                info.draw(info_display)

            display.blit(game_display, (0, 0))
            display.blit(network_display, (GAME_PANEL[0], 0))
            display.blit(info_display, (GAME_PANEL[0], NETWORK_BOX[1]))

            pg.display.update()
            clock.tick(max_fps)
            frame_count += 1

    close()


if __name__ == '__main__':
    main()
