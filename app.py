"""Pygame desktop interface for Pocket Arcade."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pygame

from .logic import (
    Card,
    ChessGame,
    FlappyBirdGame,
    Game2048,
    GeometryDashGame,
    LeftRightGame,
    PacmanGame,
    PaintCanvas,
    SolitaireGame,
    SnakeGame,
    TetrisGame,
    TicTacToeGame,
    WordleGame,
)

BACKGROUND = (23, 26, 24)
PANEL = (34, 39, 35)
PANEL_LIGHT = (43, 49, 43)
PAPER = (238, 239, 228)
MUTED = (155, 164, 151)
LINE = (67, 76, 67)
MINT = (217, 255, 135)
CORAL = (255, 121, 95)
GOLD = (240, 199, 104)
GREEN_DARK = (31, 48, 36)
GRID = (48, 59, 49)
TETRIS_COLORS = {
    "I": (101, 225, 232),
    "O": (240, 199, 104),
    "T": (190, 133, 255),
    "S": (145, 208, 112),
    "Z": (255, 121, 95),
    "J": (111, 157, 255),
    "L": (255, 170, 91),
}
TILE_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}
WORDLE_COLORS = {
    WordleGame.correct: (83, 141, 78),
    WordleGame.present: (181, 159, 59),
    WordleGame.absent: (58, 58, 60),
}

GAME_INFO = {
    "snake": ("NEON SNAKE", "ARCADE", "Keep moving. Stay sharp."),
    "paint": ("POCKET PAINT", "CREATIVE", "Make something of your own."),
    "left_right": ("MAZE RUNNER", "PUZZLE", "Guide the ball through the maze."),
    "tetris": ("POCKET TETRIS", "ARCADE", "Stack blocks. Clear lines."),
    "pacman": ("PAC-MAN", "ARCADE", "Collect every dot. Dodge ghosts."),
    "solitaire": ("POCKET SOLITAIRE", "CARD GAME", "Build four suits from ace to king."),
    "tictactoe": ("TIC-TAC-TOE", "2 PLAYERS", "Three in a row wins."),
    "chess": ("POCKET CHESS", "2 PLAYERS", "A classic strategy game."),
    "2048": ("2048", "PUZZLE", "Slide tiles. Build the 2048 tile."),
    "wordle": ("WORDLE", "PUZZLE", "Guess the five-letter word."),
    "flappy": ("FLAPPY BIRD", "ARCADE", "Tap to flap. Fly through the pipes."),
    "geometry_dash": ("GEOMETRY DASH", "ARCADE", "Jump over spikes. Keep the beat."),
}


def make_font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def draw_text(
    surface: pygame.Surface,
    value: str,
    position: tuple[int, int],
    font: pygame.font.Font,
    color: tuple[int, int, int] = PAPER,
    anchor: str = "topleft",
) -> pygame.Rect:
    image = font.render(value, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


def rounded(surface: pygame.Surface, color: tuple[int, int, int], rect: pygame.Rect, radius: int = 8, width: int = 0) -> None:
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


class ArcadeApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Pocket Arcade")
        self.android_mode = bool(os.environ.get("ANDROID_ARGUMENT"))
        self.touch_controls = self.android_mode
        if self.android_mode:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1120, 780), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.page = "home"
        self.game_id: str | None = None
        self.snake = SnakeGame()
        self.tetris = TetrisGame()
        self.game2048 = Game2048()
        self.wordle = WordleGame()
        self.flappy = FlappyBirdGame()
        self.geometry_dash = GeometryDashGame()
        self.pacman = PacmanGame()
        self.paint = PaintCanvas()
        self.paint_pointer_down = False
        self.paint_mouse_buttons: set[int] = set()
        self.paint_status = ""
        self.left_right = LeftRightGame()
        self.solitaire = SolitaireGame()
        self.tictactoe = TicTacToeGame()
        self.chess = ChessGame()
        self.chess_selection: tuple[int, int] | None = None
        self.chess_moves = []
        self.solitaire_selection: tuple[str, int, int] | None = None
        self.solitaire_mouse_down: tuple[int, int] | None = None
        self.solitaire_mouse_source: tuple[str, int, int] | None = None
        self.solitaire_dragging = False
        self.solitaire_drag_position: tuple[int, int] | None = None
        self.snake_tick = 0
        self.tetris_tick = 0
        self.flappy_tick = 0
        self.geometry_dash_tick = 0
        self.pacman_tick = 0
        self.left_right_tick = 0
        self.score_path = Path.home() / ".pocket_arcade_scores.json"
        self.best_scores = self.load_scores()
        self.font_small = make_font(12)
        self.font_label = make_font(11, True)
        self.font_body = make_font(15)
        self.font_heading = make_font(28, True)
        self.font_display = make_font(48, True)

    def load_scores(self) -> dict[str, int]:
        try:
            data = json.loads(self.score_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {key: 0 for key in GAME_INFO}
            return {key: max(0, int(data.get(key, 0))) for key in GAME_INFO}
        except (OSError, ValueError, TypeError):
            return {key: 0 for key in GAME_INFO}

    def save_score(self, key: str, score: int) -> None:
        if score <= self.best_scores.get(key, 0):
            return
        self.best_scores[key] = score
        try:
            self.score_path.write_text(json.dumps(self.best_scores, indent=2), encoding="utf-8")
        except OSError:
            pass

    def start_game(self, game_id: str) -> None:
        self.game_id = game_id
        self.page = "game"
        if game_id == "snake":
            self.snake.reset()
            self.snake_tick = pygame.time.get_ticks()
        elif game_id == "tetris":
            self.tetris.reset()
            self.tetris_tick = pygame.time.get_ticks()
        elif game_id == "2048":
            self.game2048.reset()
        elif game_id == "wordle":
            self.wordle.reset()
        elif game_id == "flappy":
            self.flappy.reset()
            self.flappy_tick = pygame.time.get_ticks()
        elif game_id == "geometry_dash":
            self.geometry_dash.reset()
            self.geometry_dash_tick = pygame.time.get_ticks()
        elif game_id == "pacman":
            self.pacman.reset()
            self.pacman_tick = pygame.time.get_ticks()
        elif game_id == "solitaire":
            self.solitaire.reset()
            self.solitaire_selection = None
            self.solitaire_mouse_down = None
            self.solitaire_mouse_source = None
            self.solitaire_dragging = False
            self.solitaire_drag_position = None
        elif game_id == "tictactoe":
            self.tictactoe.reset()
        elif game_id == "chess":
            self.chess.reset()
            self.chess_selection = None
            self.chess_moves = []
        elif game_id == "paint":
            self.paint.reset()
            self.paint_status = ""
            self.paint_pointer_down = False
            self.paint_mouse_buttons.clear()
        elif game_id == "left_right":
            self.left_right.reset()
            self.left_right_tick = pygame.time.get_ticks()

    def return_home(self) -> None:
        self.page = "home"
        self.game_id = None

    def run(self) -> None:
        while self.running:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            if self.page == "home":
                self.draw_home()
            elif self.page == "scores":
                self.draw_high_scores()
            else:
                self.draw_game()
            pygame.display.flip()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if self.android_mode:
                    continue
                size = (max(900, event.w), max(720, event.h))
                self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key, getattr(event, "unicode", ""))
            elif event.type == pygame.FINGERDOWN and self.touch_controls:
                width, height = self.screen.get_size()
                position = (round(event.x * width), round(event.y * height))
                self.handle_touch(position)
            elif event.type == pygame.FINGERMOTION and self.touch_controls and self.game_id == "paint":
                width, height = self.screen.get_size()
                position = (round(event.x * width), round(event.y * height))
                self.paint.continue_stroke(self.paint_point(position))
            elif event.type == pygame.FINGERUP and self.touch_controls and self.game_id == "paint":
                self.paint.end_stroke()
                self.paint_pointer_down = False
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and not self.android_mode
                and self.game_id == "paint"
                and event.button in (1, 3)
            ):
                self.handle_paint_click(event.pos, event.button)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.android_mode:
                if self.page in ("home", "scores"):
                    self.handle_home_click(event.pos)
                elif self.game_id == "solitaire":
                    self.handle_solitaire_mouse_down(event.pos)
                elif self.game_id == "flappy" and not self.flappy.over:
                    self.flappy.flap()
                elif self.game_id == "geometry_dash" and not self.geometry_dash.over:
                    self.geometry_dash.jump()
                elif self.game_id in ("tictactoe", "chess"):
                    self.handle_board_game_tap(event.pos)
                elif self.game_id == "wordle":
                    self.handle_wordle_tap(event.pos)
                elif self.touch_controls:
                    self.handle_touch(event.pos)
            elif event.type == pygame.MOUSEMOTION and self.game_id == "solitaire":
                self.handle_solitaire_mouse_motion(event.pos, event.buttons)
            elif event.type == pygame.MOUSEMOTION and self.game_id == "paint" and self.paint_mouse_buttons:
                self.paint.continue_stroke(self.paint_point(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.game_id == "solitaire":
                self.handle_solitaire_mouse_up(event.pos)
            elif (
                event.type == pygame.MOUSEBUTTONUP
                and self.game_id == "paint"
                and event.button in (1, 3)
            ):
                self.paint_mouse_buttons.discard(event.button)
                self.paint_pointer_down = bool(self.paint_mouse_buttons)
                if not self.paint_pointer_down:
                    self.paint.end_stroke()

    def handle_key(self, key: int, text: str = "") -> None:
        if key == pygame.K_ESCAPE:
            if self.page in ("game", "scores"):
                self.return_home()
            else:
                self.running = False
            return
        if self.page == "home":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_game("snake")
            return
        if key == pygame.K_r and (self.game_id != "wordle" or self.wordle.over):
            self.start_game(self.game_id or "snake")
            return
        if self.game_id == "snake" and not self.snake.over:
            directions = {
                pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            }
            if key in directions:
                self.snake.set_direction(directions[key])
        elif self.game_id == "left_right" and not self.left_right.over:
            if key in (pygame.K_LEFT, pygame.K_a):
                self.left_right.move(-1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.left_right.move(1)
        elif self.game_id == "pacman" and not self.pacman.over:
            directions = {
                pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            }
            if key in directions:
                self.pacman.set_direction(directions[key])
        elif self.game_id == "2048":
            directions = {
                pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
            }
            if key in directions and self.game2048.move(directions[key]):
                self.save_score("2048", self.game2048.score)
        elif self.game_id == "wordle":
            if key == pygame.K_RETURN:
                self.wordle.submit_guess()
            elif key == pygame.K_BACKSPACE:
                self.wordle.remove_letter()
            elif text:
                self.wordle.add_letter(text)
            elif pygame.K_a <= key <= pygame.K_z:
                self.wordle.add_letter(chr(key))
        elif self.game_id == "flappy" and not self.flappy.over:
            if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.flappy.flap()
        elif self.game_id == "geometry_dash" and not self.geometry_dash.over:
            if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.geometry_dash.jump()
        elif self.game_id == "tetris" and not self.tetris.over:
            if key in (pygame.K_LEFT, pygame.K_a):
                self.tetris.move(-1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.tetris.move(1)
            elif key in (pygame.K_UP, pygame.K_w):
                self.tetris.rotate()
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.tetris.step()
            elif key == pygame.K_SPACE:
                self.tetris.hard_drop()
            if self.tetris.over:
                self.save_score("tetris", self.tetris.score)

    def handle_home_click(self, position: tuple[int, int]) -> None:
        if self.page == "scores":
            if self.high_scores_navigation_rect().collidepoint(position):
                self.return_home()
            return
        if self.touch_controls:
            if self.high_scores_navigation_rect().collidepoint(position):
                self.page = "scores"
                return
            for game_id, rect in self.mobile_home_buttons().items():
                if rect.collidepoint(position):
                    self.start_game(game_id)
                    return
            return
        width, height = self.screen.get_size()
        margin = 54
        if self.high_scores_navigation_rect().collidepoint(position):
            self.page = "scores"
            return
        feature = pygame.Rect(margin, 245, width - margin * 2, 188)
        play = pygame.Rect(feature.left + 30, feature.bottom - 57, 145, 38)
        if play.collidepoint(position):
            self.start_game("snake")
            return
        gap = 14
        card_top = min(height - 240, 517)
        columns = 4
        card_width = (width - margin * 2 - gap * (columns - 1)) // columns
        for index, key in enumerate(GAME_INFO):
            card = pygame.Rect(
                margin + (index % columns) * (card_width + gap),
                card_top + (index // columns) * 82,
                card_width,
                76,
            )
            if card.collidepoint(position):
                self.start_game(key)
                return

    def handle_touch(self, position: tuple[int, int]) -> None:
        if self.page == "home":
            self.handle_home_click(position)
            return
        if self.game_id is None:
            return
        home, restart = self.mobile_navigation_buttons()
        if home.collidepoint(position):
            self.return_home()
            return
        if restart.collidepoint(position):
            self.start_game(self.game_id)
            return
        if self.game_id == "paint":
            self.handle_paint_click(position)
            return
        if self.game_id == "wordle":
            self.handle_wordle_tap(position)
            return
        if self.game_id == "solitaire":
            self.handle_solitaire_tap(position)
            return
        if self.game_id in ("tictactoe", "chess"):
            self.handle_board_game_tap(position)
            return
        elif self.game_id == "flappy":
            if not self.flappy.over:
                self.flappy.flap()
            return
        elif self.game_id == "geometry_dash":
            if not self.geometry_dash.over:
                self.geometry_dash.jump()
            return
        for action, rect in self.mobile_game_buttons().items():
            if rect.collidepoint(position):
                if self.game_id == "left_right" and not self.left_right.over:
                    self.left_right.move(-1 if action == "left" else 1)
                elif self.game_id in ("snake", "pacman", "2048"):
                    direction = {
                        "left": (-1, 0), "up": (0, -1),
                        "down": (0, 1), "right": (1, 0),
                    }[action]
                    if self.game_id == "snake" and not self.snake.over:
                        self.snake.set_direction(direction)
                    elif self.game_id == "pacman" and not self.pacman.over:
                        self.pacman.set_direction(direction)
                    elif self.game_id == "2048" and self.game2048.move(direction):
                        self.save_score("2048", self.game2048.score)
                elif self.game_id == "flappy" and not self.flappy.over:
                    self.flappy.flap()
                elif self.game_id == "tetris" and not self.tetris.over:
                    if action == "left":
                        self.tetris.move(-1)
                    elif action == "right":
                        self.tetris.move(1)
                    elif action == "rotate":
                        self.tetris.rotate()
                    elif action == "down":
                        self.tetris.step()
                    elif action == "drop":
                        self.tetris.hard_drop()
                    if self.tetris.over:
                        self.save_score("tetris", self.tetris.score)
                return

    def handle_board_game_tap(self, position: tuple[int, int]) -> None:
        if self.game_id == "tictactoe":
            if self.board_game_mode_rect().collidepoint(position):
                self._cycle_board_bot_mode(self.tictactoe)
                return
            if self.tictactoe.bot_mode and self.tictactoe.current_player == "O":
                return
            board = self.tictactoe_board_rect()
            if not board.collidepoint(position) or self.tictactoe.over:
                return
            cell = board.width // 3
            column = (position[0] - board.left) // cell
            row = (position[1] - board.top) // cell
            if self.tictactoe.play(row * 3 + column) and self.tictactoe.bot_mode and not self.tictactoe.over:
                self.tictactoe.bot_move(self.tictactoe.bot_difficulty)
        elif self.game_id == "chess":
            if self.board_game_mode_rect().collidepoint(position):
                self._cycle_board_bot_mode(self.chess)
                self.chess_selection = None
                self.chess_moves = []
                return
            if self.chess.bot_mode and not self.chess.white_to_move:
                return
            board = self.chess_board_rect()
            if not board.collidepoint(position) or self.chess.over:
                return
            cell = board.width // 8
            square = (
                (position[1] - board.top) // cell,
                (position[0] - board.left) // cell,
            )
            piece = self.chess.board[square[0]][square[1]]
            if self.chess_selection is not None:
                move = next(
                    (candidate for candidate in self.chess_moves if candidate.end == square),
                    None,
                )
                if move is not None:
                    if self.chess.move(move.start, move.end) and self.chess.bot_mode and not self.chess.over:
                        self.chess.bot_move(self.chess.bot_difficulty)
                    self.chess_selection = None
                    self.chess_moves = []
                    return
            if piece is not None and piece.isupper() == self.chess.white_to_move:
                self.chess_selection = square
                self.chess_moves = self.chess.legal_moves(square)
            else:
                self.chess_selection = None
                self.chess_moves = []

    @staticmethod
    def _cycle_board_bot_mode(game: TicTacToeGame | ChessGame) -> None:
        modes = ("two_players", "normal", "hard")
        game.bot_difficulty = modes[(modes.index(game.bot_difficulty) + 1) % len(modes)]
        if game.bot_difficulty == "two_players":
            return
        if isinstance(game, TicTacToeGame) and game.current_player == "O":
            game.bot_move(game.bot_difficulty)
        elif isinstance(game, ChessGame) and not game.white_to_move:
            game.bot_move(game.bot_difficulty)

    def tictactoe_board_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        size = min(width - 80, height - 160, 510)
        size = max(120, size)
        cell = size // 3
        board = pygame.Rect(0, 0, cell * 3, cell * 3)
        board.center = (width // 2, height // 2 + 60)
        return board

    def chess_board_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        size = min(width - 64, height - 148, 560)
        size = max(160, size)
        cell = size // 8
        board = pygame.Rect(0, 0, cell * 8, cell * 8)
        board.center = (width // 2, height // 2 + 60)
        return board

    def board_game_mode_rect(self) -> pygame.Rect:
        width, _ = self.screen.get_size()
        return pygame.Rect(width // 2 - 78, 66, 156, 30)

    def mobile_home_buttons(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        margin, gap = 18, 10
        button_width = (width - margin * 2 - gap) // 2
        rows = (len(GAME_INFO) + 1) // 2
        top = max(height // 3, self.high_scores_navigation_rect().bottom + 10)
        button_height = min(
            72,
            max(24, (height - top - 52 - gap * (rows - 1)) // rows),
        )
        return {
            game_id: pygame.Rect(
                margin + (index % 2) * (button_width + gap),
                top + (index // 2) * (button_height + gap),
                button_width,
                button_height,
            )
            for index, game_id in enumerate(GAME_INFO)
        }

    def high_scores_navigation_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        if self.touch_controls:
            if self.page == "scores":
                return pygame.Rect(width // 2 - 85, 12, 170, 36)
            return pygame.Rect(width - 188, max(88, height // 4) - 17, 170, 34)
        return pygame.Rect(width - 54 - 144, 18, 144, 36)

    def mobile_navigation_buttons(self) -> tuple[pygame.Rect, pygame.Rect]:
        width, _ = self.screen.get_size()
        return pygame.Rect(16, 12, 104, 40), pygame.Rect(width - 120, 12, 104, 40)

    def paint_canvas_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        margin = 20 if self.touch_controls else 34
        return pygame.Rect(margin, 150, width - margin * 2, max(100, height - 172))

    def paint_toolbar_buttons(self) -> dict[str, pygame.Rect]:
        width = self.screen.get_width()
        swatch_size, swatch_gap = 28, 8
        palette_width = len(self.paint.palette) * swatch_size + (len(self.paint.palette) - 1) * swatch_gap
        left = (width - palette_width) // 2
        buttons = {
            f"color_{index}": pygame.Rect(
                left + index * (swatch_size + swatch_gap), 74, swatch_size, swatch_size
            )
            for index in range(len(self.paint.palette))
        }
        action_labels = (
            ("undo", "UNDO", 62),
            ("eraser", "ERASER", 72),
            ("smaller", "−", 34),
            ("size", f"{round(self.paint.brush_size * 500):02}", 42),
            ("larger", "+", 34),
            ("clear", "CLEAR", 62),
            ("save", "SAVE", 58),
        )
        gap = 6
        total_width = sum(item[2] for item in action_labels) + gap * (len(action_labels) - 1)
        left = (width - total_width) // 2
        for action, _label, button_width in action_labels:
            buttons[action] = pygame.Rect(left, 109, button_width, 28)
            left += button_width + gap
        return buttons

    def paint_point(self, position: tuple[int, int]) -> tuple[float, float]:
        canvas = self.paint_canvas_rect()
        return (
            (position[0] - canvas.left) / canvas.width,
            (position[1] - canvas.top) / canvas.height,
        )

    def handle_paint_click(self, position: tuple[int, int], mouse_button: int | None = None) -> None:
        for action, rect in self.paint_toolbar_buttons().items():
            if not rect.collidepoint(position):
                continue
            if action.startswith("color_"):
                self.paint.select_color(self.paint.palette[int(action.removeprefix("color_"))])
            elif action == "undo":
                self.paint.undo()
            elif action == "eraser":
                self.paint.toggle_eraser()
            elif action == "smaller":
                self.paint.set_brush_size(self.paint.brush_size - 0.004)
            elif action == "larger":
                self.paint.set_brush_size(self.paint.brush_size + 0.004)
            elif action == "clear":
                self.paint.clear()
            elif action == "save":
                path = Path.home() / "PocketArcade-Paint.svg"
                try:
                    self.paint.save_svg(path)
                except OSError as error:
                    self.paint_status = f"Could not save: {error}"
                else:
                    self.paint_status = f"Saved to {path}"
            return
        if self.paint_canvas_rect().collidepoint(position):
            self.paint_pointer_down = True
            if mouse_button is not None:
                self.paint_mouse_buttons.add(mouse_button)
            self.paint.begin_stroke(self.paint_point(position))

    def mobile_game_buttons(self) -> dict[str, pygame.Rect]:
        if self.game_id in ("solitaire", "tictactoe", "chess", "wordle", "paint"):
            return {}
        width, height = self.screen.get_size()
        if self.game_id == "tetris":
            actions = ("left", "rotate", "right", "down", "drop")
        elif self.game_id == "flappy":
            actions = ("flap",)
        elif self.game_id == "geometry_dash":
            actions = ("jump",)
        elif self.game_id == "left_right":
            actions = ("left", "right")
        else:
            actions = ("left", "up", "down", "right")
        margin = 12
        gap = max(5, min(10, width // 80))
        button_width = min(88 if len(actions) == 5 else 76, (width - margin * 2 - gap * (len(actions) - 1)) // len(actions))
        button_height = min(60, max(48, height // 8))
        total_width = button_width * len(actions) + gap * (len(actions) - 1)
        left = (width - total_width) // 2
        top = height - button_height - 10
        return {
            action: pygame.Rect(left + index * (button_width + gap), top, button_width, button_height)
            for index, action in enumerate(actions)
        }

    def wordle_keyboard_rects(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        gap = max(3, min(7, width // 100))
        rows = self.wordle_keyboard_rows()
        key_height = min(42, max(22, (height - 250) // len(rows)))
        unit = min(44, (width - 32 - gap * 9) // 10)
        top = height - (key_height * len(rows) + gap * (len(rows) - 1)) - 12
        rects = {}
        for row_index, keys in enumerate(rows):
            units = sum(1.5 if key in ("ENTER", "BACK") else 1 for key in keys)
            row_width = unit * units + gap * (len(keys) - 1)
            left = (width - row_width) // 2
            for key in keys:
                key_width = int(unit * (1.5 if key in ("ENTER", "BACK") else 1))
                rects[key] = pygame.Rect(
                    left,
                    top + row_index * (key_height + gap),
                    key_width,
                    key_height,
                )
                left += key_width + gap
        return rects

    def wordle_keyboard_rows(self) -> tuple[tuple[str, ...], ...]:
        if self.wordle.language == "de":
            return (
                tuple("QWERTZUIOP"),
                tuple("ASDFGHJKL"),
                tuple("YXCVBNMÄÖÜ"),
                ("ENTER", "ß", "BACK"),
            )
        return (
            tuple("QWERTYUIOP"),
            tuple("ASDFGHJKL"),
            ("ENTER", *tuple("ZXCVBNM"), "BACK"),
        )

    def wordle_language_rect(self) -> pygame.Rect:
        width, _ = self.screen.get_size()
        return pygame.Rect(width // 2 - 86, 66, 172, 28)

    def toggle_wordle_language(self) -> None:
        language = "de" if self.wordle.language == "en" else "en"
        self.wordle.set_language(language)

    def handle_wordle_action(self, action: str) -> None:
        if action == "ENTER":
            self.wordle.submit_guess()
        elif action == "BACK":
            self.wordle.remove_letter()
        else:
            self.wordle.add_letter(action)

    def handle_wordle_tap(self, position: tuple[int, int]) -> None:
        if self.wordle_language_rect().collidepoint(position):
            self.toggle_wordle_language()
            return
        for action, rect in self.wordle_keyboard_rects().items():
            if rect.collidepoint(position):
                self.handle_wordle_action(action)
                return

    def solitaire_layout(self) -> tuple[list[int], int, int, int, int]:
        width = self.screen.get_width()
        card_width = max(46, min(88, (width - 120) // 10))
        card_height = card_width * 7 // 5
        gap = max(8, card_width // 6)
        total_width = card_width * 7 + gap * 6
        left = (width - total_width) // 2
        columns = [left + index * (card_width + gap) for index in range(7)]
        top = 72 if self.touch_controls else 82
        return columns, top, top + card_height + 24, card_width, card_height

    def solitaire_card_rect(
        self,
        kind: str,
        index: int = 0,
        card_index: int | None = None,
    ) -> pygame.Rect:
        columns, top, tableau_top, card_width, card_height = self.solitaire_layout()
        if kind == "tableau":
            pile = self.solitaire.tableau[index]
            y = tableau_top
            if card_index is not None:
                for card in pile[:card_index]:
                    y += max(12, card_height // 6) if not card.face_up else max(17, card_height // 4)
            return pygame.Rect(columns[index], y, card_width, card_height)
        row = 0 if kind == "stock" else 1 if kind == "waste" else index + 3
        return pygame.Rect(columns[row], top, card_width, card_height)

    def solitaire_source_at(self, position: tuple[int, int]) -> tuple[str, int, int] | None:
        if self.solitaire.waste and self.solitaire_card_rect("waste").collidepoint(position):
            return ("waste", 0, len(self.solitaire.waste) - 1)
        for index, pile in enumerate(self.solitaire.foundations):
            if pile and self.solitaire_card_rect("foundation", index).collidepoint(position):
                return ("foundation", index, len(pile) - 1)

        for column, pile in reversed(list(enumerate(self.solitaire.tableau))):
            for card_index in range(len(pile) - 1, -1, -1):
                card = pile[card_index]
                rect = self.solitaire_card_rect("tableau", column, card_index)
                if card.face_up and rect.collidepoint(position):
                    return ("tableau", column, card_index)
        return None

    def solitaire_target_at(self, position: tuple[int, int]) -> tuple[str, int] | None:
        for index in range(4):
            if self.solitaire_card_rect("foundation", index).collidepoint(position):
                return ("foundation", index)
        columns, _, tableau_top, card_width, _ = self.solitaire_layout()
        if position[1] >= tableau_top:
            for index, left in enumerate(columns):
                if left <= position[0] <= left + card_width:
                    return ("tableau", index)
        return None

    def _try_solitaire_move(self, destination: tuple[str, int]) -> bool:
        if self.solitaire_selection is None:
            return False
        kind, source, start_index = self.solitaire_selection
        target_kind, target = destination
        moved = False
        if target_kind == "tableau":
            if kind == "waste":
                moved = self.solitaire.move_waste_to_tableau(target)
            elif kind == "tableau":
                moved = self.solitaire.move_tableau_to_tableau(source, target, start_index)
            elif kind == "foundation":
                moved = self.solitaire.move_foundation_to_tableau(source, target)
        elif target_kind == "foundation":
            if kind == "waste":
                moved = self.solitaire.move_waste_to_foundation(target)
            elif kind == "tableau" and start_index == len(self.solitaire.tableau[source]) - 1:
                moved = self.solitaire.move_tableau_to_foundation(source, target)
        if moved:
            self.solitaire_selection = None
            self._finish_solitaire_move()
        return moved

    def _auto_move_solitaire_to_foundation(self) -> bool:
        if self.solitaire_selection is None:
            return False
        kind, source, start_index = self.solitaire_selection
        if kind == "waste" and self.solitaire.waste:
            card = self.solitaire.waste[-1]
        elif kind == "tableau" and self.solitaire.tableau[source]:
            pile = self.solitaire.tableau[source]
            if start_index != len(pile) - 1:
                return False
            card = pile[-1]
        else:
            return False
        destination = self.solitaire.suits.index(card.suit)
        return self._try_solitaire_move(("foundation", destination))

    def _finish_solitaire_move(self) -> None:
        if self.solitaire.won:
            self.save_score("solitaire", self.solitaire.score)

    def handle_solitaire_tap(self, position: tuple[int, int]) -> None:
        if self.solitaire_card_rect("stock").collidepoint(position):
            self.solitaire.draw_stock()
            self.solitaire_selection = None
            return

        source = self.solitaire_source_at(position)
        if source is not None and source == self.solitaire_selection:
            self._auto_move_solitaire_to_foundation()
            return

        destination = self.solitaire_target_at(position)
        if self.solitaire_selection is not None and destination is not None:
            if self._try_solitaire_move(destination):
                return
        self.solitaire_selection = source

    def handle_solitaire_mouse_down(self, position: tuple[int, int]) -> None:
        self.solitaire_mouse_down = position
        self.solitaire_mouse_source = self.solitaire_source_at(position)
        self.solitaire_dragging = False
        self.solitaire_drag_position = position

    def handle_solitaire_mouse_motion(
        self,
        position: tuple[int, int],
        buttons: tuple[bool, ...],
    ) -> None:
        if self.solitaire_mouse_down is None or not buttons or not buttons[0]:
            return
        dx = position[0] - self.solitaire_mouse_down[0]
        dy = position[1] - self.solitaire_mouse_down[1]
        if dx * dx + dy * dy > 64:
            self.solitaire_dragging = True
        self.solitaire_drag_position = position

    def handle_solitaire_mouse_up(self, position: tuple[int, int]) -> None:
        if self.solitaire_mouse_down is None:
            return
        if self.solitaire_dragging and self.solitaire_mouse_source is not None:
            self.solitaire_selection = self.solitaire_mouse_source
            destination = self.solitaire_target_at(position)
            if destination is not None:
                self._try_solitaire_move(destination)
        else:
            self.handle_solitaire_tap(position)
        self.solitaire_mouse_down = None
        self.solitaire_mouse_source = None
        self.solitaire_dragging = False
        self.solitaire_drag_position = None

    def draw_touch_button(self, rect: pygame.Rect, label: str) -> None:
        rounded(self.screen, (48, 59, 65), rect, 8)
        pygame.draw.rect(self.screen, (91, 108, 115), rect, width=1, border_radius=8)
        draw_text(self.screen, label, rect.center, self.font_body if len(label) > 2 else self.font_heading, PAPER, "center")

    def update(self) -> None:
        if self.page != "game" or self.game_id is None:
            return
        if self.game_id == "snake" and not self.snake.over:
            now = pygame.time.get_ticks()
            if now - self.snake_tick >= 135:
                self.snake_tick = now
                self.snake.step()
                if self.snake.over:
                    self.save_score("snake", self.snake.score)
        elif self.game_id == "tetris" and not self.tetris.over:
            now = pygame.time.get_ticks()
            interval = max(90, 550 - (self.tetris.lines // 10) * 45)
            if now - self.tetris_tick >= interval:
                self.tetris_tick = now
                self.tetris.step()
                if self.tetris.over:
                    self.save_score("tetris", self.tetris.score)
        elif self.game_id == "pacman" and not self.pacman.over:
            now = pygame.time.get_ticks()
            if now - self.pacman_tick >= 125:
                self.pacman_tick = now
                self.pacman.step()
                if self.pacman.over:
                    self.save_score("pacman", self.pacman.score)
        elif self.game_id == "left_right" and not self.left_right.over:
            now = pygame.time.get_ticks()
            interval = max(90, 220 - (self.left_right.score // 10) * 12)
            if now - self.left_right_tick >= interval:
                self.left_right_tick = now
                self.left_right.step()
                if self.left_right.over:
                    self.save_score("left_right", self.left_right.score)
        elif self.game_id == "flappy" and not self.flappy.over:
            now = pygame.time.get_ticks()
            if now - self.flappy_tick >= 30:
                self.flappy_tick = now
                self.flappy.step()
                if self.flappy.over:
                    self.save_score("flappy", self.flappy.score)
        elif self.game_id == "geometry_dash" and not self.geometry_dash.over:
            now = pygame.time.get_ticks()
            if now - self.geometry_dash_tick >= 30:
                self.geometry_dash_tick = now
                self.geometry_dash.step()
                if self.geometry_dash.over:
                    self.save_score("geometry_dash", self.geometry_dash.score)

    def draw_background(self) -> None:
        self.screen.fill(BACKGROUND)
        width, height = self.screen.get_size()
        for x in range(10, width, 18):
            for y in range(10, height, 18):
                self.screen.set_at((x, y), (31, 35, 31))

    def draw_button(self, rect: pygame.Rect, label: str, icon: str = ">") -> None:
        hover = rect.collidepoint(pygame.mouse.get_pos())
        rounded(self.screen, (230, 255, 171) if hover else MINT, rect, 5)
        draw_text(self.screen, label, (rect.left + 14, rect.centery), self.font_label, BACKGROUND, "midleft")
        draw_text(self.screen, icon, (rect.right - 15, rect.centery), self.font_body, BACKGROUND, "center")

    def draw_home(self) -> None:
        self.draw_background()
        if self.touch_controls:
            self.draw_mobile_home()
            return
        width, height = self.screen.get_size()
        margin = 54
        draw_text(self.screen, "[+]", (margin, 34), self.font_heading, MINT, "midleft")
        draw_text(self.screen, "pocket", (margin + 47, 22), make_font(21, True), PAPER)
        draw_text(self.screen, "arcade", (margin + 113, 22), make_font(21), MUTED)
        self.draw_button(self.high_scores_navigation_rect(), "HIGH SCORES")
        pygame.draw.line(self.screen, LINE, (margin, 66), (width - margin, 66), 1)

        draw_text(self.screen, "A FEW MINUTES. BETTER SPENT.", (margin, 91), self.font_label, MUTED)
        draw_text(self.screen, "Press play.", (margin, 111), self.font_display, PAPER)
        draw_text(self.screen, "Find your flow.", (margin, 163), self.font_display, MINT)
        draw_text(self.screen, "Quick games for the space between everything else.", (margin + 2, 216), self.font_body, MUTED)

        feature = pygame.Rect(margin, 245, width - margin * 2, 188)
        rounded(self.screen, GREEN_DARK, feature, 8)
        pygame.draw.rect(self.screen, (70, 104, 67), feature, width=1, border_radius=8)
        art = pygame.Rect(feature.left + 20, feature.top + 17, max(260, feature.width // 2 - 30), feature.height - 34)
        rounded(self.screen, (25, 38, 29), art, 6)
        for x in range(art.left + 13, art.right, 25):
            pygame.draw.line(self.screen, (39, 59, 42), (x, art.top), (x, art.bottom), 1)
        for y in range(art.top + 12, art.bottom, 25):
            pygame.draw.line(self.screen, (39, 59, 42), (art.left, y), (art.right, y), 1)
        snake_points = [(art.left + 53, art.top + 94), (art.left + 78, art.top + 94), (art.left + 103, art.top + 94), (art.left + 128, art.top + 94), (art.left + 128, art.top + 69)]
        for index, point in enumerate(snake_points):
            segment = pygame.Rect(point[0], point[1], 21, 21)
            rounded(self.screen, MINT if index == 0 else (151, 218, 112), segment, 5)
        pygame.draw.circle(self.screen, CORAL, (art.right - 37, art.top + 36), 7)
        draw_text(self.screen, "01  /  THE CLASSIC", (art.left + 12, art.bottom - 10), self.font_label, (160, 181, 154), "bottomleft")

        copy_x = art.right + 30
        draw_text(self.screen, "ARCADE   ·   2-5 MIN", (copy_x, feature.top + 25), self.font_label, MINT)
        draw_text(self.screen, "Neon Snake", (copy_x, feature.top + 52), self.font_heading, PAPER)
        draw_text(self.screen, "Keep moving. Stay sharp. Try not to eat your tail.", (copy_x, feature.top + 91), self.font_small, MUTED)
        play = pygame.Rect(copy_x, feature.bottom - 55, 145, 38)
        self.draw_button(play, "PLAY NOW")
        draw_text(self.screen, "ARROW KEYS / WASD", (play.right + 15, play.centery), self.font_label, MUTED, "midleft")

        draw_text(self.screen, "THE COLLECTION", (margin, 436), self.font_label, MUTED)
        draw_text(self.screen, "More to get into", (margin, 454), make_font(21, True), PAPER)
        card_top = min(height - 240, 517)
        gap = 14
        columns = 4
        card_width = (width - margin * 2 - gap * (columns - 1)) // columns
        colors = {
            "snake": MINT,
            "tetris": CORAL,
            "pacman": GOLD,
            "solitaire": (166, 183, 255),
            "tictactoe": (130, 205, 255),
            "chess": (240, 199, 104),
            "2048": (237, 194, 46),
            "wordle": MINT,
            "flappy": (111, 190, 235),
            "paint": (235, 119, 170),
            "left_right": (112, 204, 211),
            "geometry_dash": (136, 104, 255),
        }
        for index, (key, (name, category, description)) in enumerate(GAME_INFO.items()):
            card = pygame.Rect(
                margin + (index % 4) * (card_width + gap),
                card_top + (index // 4) * 82,
                card_width,
                76,
            )
            hover = card.collidepoint(pygame.mouse.get_pos())
            rounded(self.screen, PANEL_LIGHT if hover else PANEL, card, 6)
            pygame.draw.rect(self.screen, (89, 99, 82) if hover else LINE, card, width=1, border_radius=6)
            color = colors[key]
            draw_text(self.screen, f"0{index + 1}", (card.right - 10, card.top + 8), self.font_label, MUTED, "topright")
            self.draw_card_art(card, key, color)
            draw_text(self.screen, category, (card.left + 84, card.top + 13), self.font_label, color)
            draw_text(self.screen, name, (card.left + 84, card.top + 31), make_font(16, True), PAPER)
            draw_text(self.screen, description, (card.left + 84, card.top + 57), self.font_small, MUTED)

    def draw_mobile_home(self) -> None:
        width, height = self.screen.get_size()
        draw_text(self.screen, "POCKET ARCADE", (width // 2, max(28, height // 8)), self.font_heading, MINT, "center")
        draw_text(self.screen, "CHOOSE A GAME", (18, max(88, height // 4)), self.font_label, MUTED, "midleft")
        scores_button = self.high_scores_navigation_rect()
        rounded(self.screen, PANEL, scores_button, 6)
        pygame.draw.rect(self.screen, LINE, scores_button, width=1, border_radius=6)
        draw_text(self.screen, "HIGH SCORES", scores_button.center, self.font_label, MINT, "center")
        colors = {
            "snake": MINT,
            "tetris": CORAL,
            "pacman": GOLD,
            "solitaire": (166, 183, 255),
            "tictactoe": (130, 205, 255),
            "chess": (240, 199, 104),
            "2048": (237, 194, 46),
            "wordle": MINT,
            "flappy": (111, 190, 235),
            "paint": (235, 119, 170),
            "left_right": (112, 204, 211),
            "geometry_dash": (136, 104, 255),
        }
        for game_id, rect in self.mobile_home_buttons().items():
            name, _, _ = GAME_INFO[game_id]
            rounded(self.screen, PANEL, rect, 8)
            pygame.draw.rect(self.screen, LINE, rect, width=1, border_radius=8)
            title_font = make_font(min(15, max(11, rect.height // 2 + 1)))
            detail_font = make_font(min(11, max(8, rect.height // 3)))
            draw_text(self.screen, name, (rect.centerx, rect.centery - 5), title_font, colors[game_id], "center")
            detail = (
                "2 PLAYERS" if game_id in ("tictactoe", "chess")
                else "6 GUESSES" if game_id == "wordle"
                else "DRAW" if game_id == "paint"
                else "LEFT / RIGHT" if game_id == "left_right"
                else f"BEST {self.best_scores[game_id]:02}"
            )
            draw_text(self.screen, detail, (rect.centerx, rect.centery + 7), detail_font, MUTED, "center")
        draw_text(self.screen, "TAP A GAME", (width // 2, height - 24), self.font_label, MUTED, "center")

    def draw_high_scores(self) -> None:
        self.draw_background()
        width, height = self.screen.get_size()
        navigation = self.high_scores_navigation_rect()
        if self.touch_controls:
            rounded(self.screen, PANEL, navigation, 6)
            pygame.draw.rect(self.screen, LINE, navigation, width=1, border_radius=6)
            draw_text(self.screen, "<  ARCADE", navigation.center, self.font_label, MINT, "center")
            draw_text(self.screen, "HIGH SCORES", (width // 2, 70), self.font_heading, PAPER, "center")
            draw_text(self.screen, "PERSONAL BESTS  ·  THIS DEVICE", (width // 2, 94), self.font_label, MUTED, "center")
            row_height = min(48, max(18, (height - 130) // len(GAME_INFO)))
            panel = pygame.Rect(18, 112, width - 36, row_height * len(GAME_INFO) + 12)
        else:
            margin = 54
            draw_text(self.screen, "[+]", (margin, 34), self.font_heading, MINT, "midleft")
            draw_text(self.screen, "pocket", (margin + 47, 22), make_font(21, True), PAPER)
            draw_text(self.screen, "arcade", (margin + 113, 22), make_font(21), MUTED)
            self.draw_button(navigation, "ARCADE", "<")
            pygame.draw.line(self.screen, LINE, (margin, 66), (width - margin, 66), 1)
            draw_text(self.screen, "YOUR BEST RUNS", (width // 2, 110), self.font_heading, PAPER, "center")
            draw_text(self.screen, "PERSONAL BESTS  ·  SAVED ON THIS DEVICE", (width // 2, 145), self.font_label, MUTED, "center")
            row_height = min(48, max(34, (height - 240) // len(GAME_INFO)))
            panel = pygame.Rect(max(54, width // 4), 174, min(600, width - 108), row_height * len(GAME_INFO) + 16)

        rounded(self.screen, PANEL, panel, 8)
        for index, (game_id, (name, _category, _description)) in enumerate(GAME_INFO.items()):
            row_top = panel.top + 8 + index * row_height
            if index:
                pygame.draw.line(
                    self.screen,
                    LINE,
                    (panel.left + 12, row_top),
                    (panel.right - 12, row_top),
                    1,
                )
            score = self.best_scores.get(game_id, 0)
            score_text = f"{score:,}" if score else "—"
            font = self.font_body if self.touch_controls else make_font(16, True)
            draw_text(self.screen, name, (panel.left + 18, row_top + row_height // 2), font, PAPER, "midleft")
            draw_text(self.screen, score_text, (panel.right - 18, row_top + row_height // 2), font, MINT if score else MUTED, "midright")

    def draw_card_art(self, card: pygame.Rect, key: str, color: tuple[int, int, int]) -> None:
        center = (card.left + 43, card.centery)
        if key == "snake":
            points = [(center[0] - 20, center[1] + 7), (center[0] - 6, center[1] + 7), (center[0] + 8, center[1] + 7), (center[0] + 8, center[1] - 7)]
            for index, point in enumerate(points):
                rounded(self.screen, color if index == 0 else (143, 204, 106), pygame.Rect(point[0], point[1], 12, 12), 3)
        elif key == "tetris":
            blocks = ((-1, 0), (0, 0), (1, 0), (0, 1))
            for dx, dy in blocks:
                rect = pygame.Rect(center[0] + dx * 13 - 5, center[1] + dy * 13 - 5, 11, 11)
                rounded(self.screen, color, rect, 3)
        elif key == "solitaire":
            back = pygame.Rect(center[0] - 20, center[1] - 24, 31, 44)
            front = pygame.Rect(center[0] - 9, center[1] - 18, 31, 44)
            rounded(self.screen, (48, 62, 94), back, 5)
            rounded(self.screen, PAPER, front, 5)
            draw_text(self.screen, "A", (front.left + 7, front.top + 5), self.font_label, color)
            draw_text(self.screen, "♥", front.center, make_font(16, True), CORAL, "center")
        elif key == "tictactoe":
            pygame.draw.line(self.screen, color, (center[0] - 12, center[1] - 13), (center[0] + 12, center[1] + 13), 4)
            pygame.draw.line(self.screen, color, (center[0] + 12, center[1] - 13), (center[0] - 12, center[1] + 13), 4)
            pygame.draw.circle(self.screen, PAPER, (center[0], center[1]), 21, 3)
        elif key == "chess":
            rounded(self.screen, (69, 61, 43), pygame.Rect(center[0] - 24, center[1] - 24, 48, 48), 10)
            draw_text(self.screen, "K", center, make_font(30, True), color, "center")
        elif key == "2048":
            rounded(self.screen, TILE_COLORS[2], pygame.Rect(center[0] - 24, center[1] - 24, 22, 22), 4)
            rounded(self.screen, TILE_COLORS[8], pygame.Rect(center[0] + 2, center[1] + 2, 22, 22), 4)
            draw_text(self.screen, "2", (center[0] - 13, center[1] - 13), self.font_label, (70, 62, 52), "center")
            draw_text(self.screen, "8", (center[0] + 13, center[1] + 13), self.font_label, PAPER, "center")
        elif key == "wordle":
            for index, tile_color in enumerate(WORDLE_COLORS.values()):
                rounded(
                    self.screen,
                    tile_color,
                    pygame.Rect(center[0] - 24 + index * 17, center[1] - 8, 15, 16),
                    3,
                )
        elif key == "flappy":
            pygame.draw.rect(self.screen, (75, 162, 96), (center[0] + 13, center[1] - 22, 12, 44), border_radius=4)
            pygame.draw.rect(self.screen, (75, 162, 96), (center[0] + 13, center[1] + 5, 20, 10), border_radius=3)
            pygame.draw.circle(self.screen, GOLD, (center[0] - 10, center[1]), 14)
            pygame.draw.circle(self.screen, PAPER, (center[0] - 4, center[1] - 5), 4)
            pygame.draw.circle(self.screen, BACKGROUND, (center[0] - 3, center[1] - 5), 2)
        elif key == "geometry_dash":
            pygame.draw.polygon(self.screen, color, ((center[0] - 21, center[1] + 19), (center[0] - 7, center[1] - 8), (center[0] + 7, center[1] + 19)))
            pygame.draw.polygon(self.screen, color, ((center[0] + 3, center[1] + 19), (center[0] + 17, center[1] - 8), (center[0] + 31, center[1] + 19)))
            rounded(self.screen, GOLD, pygame.Rect(center[0] - 31, center[1] - 20, 21, 21), 3)
        elif key == "paint":
            pygame.draw.line(self.screen, color, (center[0] - 20, center[1] + 13), (center[0] + 14, center[1] - 11), 7)
            pygame.draw.polygon(self.screen, GOLD, ((center[0] + 14, center[1] - 11), (center[0] + 22, center[1] - 19), (center[0] + 18, center[1] - 6)))
        elif key == "left_right":
            pygame.draw.polygon(self.screen, color, ((center[0] - 23, center[1]), (center[0] - 10, center[1] - 12), (center[0] - 10, center[1] - 5), (center[0] + 2, center[1] - 5), (center[0] + 2, center[1] + 5), (center[0] - 10, center[1] + 5), (center[0] - 10, center[1] + 12)))
            pygame.draw.circle(self.screen, GOLD, (center[0] + 13, center[1]), 10)
        else:
            pygame.draw.circle(self.screen, color, center, 20)
            pygame.draw.polygon(self.screen, PANEL, (center, (center[0] + 21, center[1] - 9), (center[0] + 21, center[1] + 9)))
            for dx, dy in ((-28, -18), (0, -24), (28, -18), (-28, 18), (28, 18)):
                pygame.draw.circle(self.screen, PAPER, (center[0] + dx, center[1] + dy), 2)

    def draw_game_header(self, title: str, best: int) -> None:
        width, _ = self.screen.get_size()
        draw_text(self.screen, "<  ARCADE", (48, 34), self.font_label, MUTED, "midleft")
        draw_text(self.screen, title, (width // 2, 34), make_font(17, True), PAPER, "center")
        if not self.touch_controls:
            draw_text(self.screen, f"BEST  {best:02}", (width - 48, 34), self.font_label, GOLD, "midright")
        pygame.draw.line(self.screen, LINE, (48, 62), (width - 48, 62), 1)

    def draw_touch_ui(self) -> None:
        home, restart = self.mobile_navigation_buttons()
        self.draw_touch_button(home, "HOME")
        self.draw_touch_button(restart, "RESTART")
        labels = {
            "left": "←", "up": "↑", "down": "↓", "right": "→",
            "rotate": "ROTATE", "drop": "DROP", "flap": "FLAP", "jump": "JUMP",
        }
        for action, rect in self.mobile_game_buttons().items():
            self.draw_touch_button(rect, labels[action])

    def draw_game(self) -> None:
        self.draw_background()
        if self.game_id == "snake":
            self.draw_snake()
        elif self.game_id == "tetris":
            self.draw_tetris()
        elif self.game_id == "2048":
            self.draw_2048()
        elif self.game_id == "wordle":
            self.draw_wordle()
        elif self.game_id == "flappy":
            self.draw_flappy()
        elif self.game_id == "geometry_dash":
            self.draw_geometry_dash()
        elif self.game_id == "pacman":
            self.draw_pacman()
        elif self.game_id == "solitaire":
            self.draw_solitaire()
        elif self.game_id == "tictactoe":
            self.draw_tictactoe()
        elif self.game_id == "chess":
            self.draw_chess()
        elif self.game_id == "paint":
            self.draw_paint()
        elif self.game_id == "left_right":
            self.draw_left_right()
        if self.touch_controls and self.game_id is not None:
            self.draw_touch_ui()

    def draw_paint(self) -> None:
        self.draw_board_game_header("POCKET PAINT")
        toolbar = self.paint_toolbar_buttons()
        action_labels = {
            "undo": "UNDO",
            "eraser": "ERASE",
            "smaller": "−",
            "size": f"{round(self.paint.brush_size * 500):02}",
            "larger": "+",
            "clear": "CLEAR",
            "save": "SAVE",
        }
        for index, color in enumerate(self.paint.palette):
            rect = toolbar[f"color_{index}"]
            rounded(self.screen, color, rect, 6)
            selected = color == self.paint.color and not self.paint.erasing
            pygame.draw.rect(
                self.screen,
                MINT if selected else PAPER,
                rect,
                width=3 if selected else 1,
                border_radius=6,
            )
        for action, label in action_labels.items():
            rect = toolbar[action]
            active = action == "eraser" and self.paint.erasing
            rounded(self.screen, MINT if active else PANEL, rect, 5)
            pygame.draw.rect(self.screen, LINE, rect, width=1, border_radius=5)
            color = BACKGROUND if active else PAPER
            draw_text(self.screen, label, rect.center, self.font_label, color, "center")
        canvas = self.paint_canvas_rect()
        rounded(self.screen, PAPER, canvas, 7)
        pygame.draw.rect(self.screen, LINE, canvas, width=1, border_radius=7)
        scale = min(canvas.width, canvas.height)
        for stroke in self.paint.strokes:
            points = [
                (round(canvas.left + x * canvas.width), round(canvas.top + y * canvas.height))
                for x, y in stroke.points
            ]
            brush_width = max(1, round(stroke.width * scale))
            radius = max(1, brush_width // 2)
            if len(points) == 1:
                pygame.draw.circle(self.screen, stroke.color, points[0], radius)
                continue
            pygame.draw.lines(self.screen, stroke.color, False, points, brush_width)
            pygame.draw.circle(self.screen, stroke.color, points[0], radius)
            pygame.draw.circle(self.screen, stroke.color, points[-1], radius)
        if self.paint_status:
            draw_text(
                self.screen,
                self.paint_status,
                (self.screen.get_width() // 2, 140),
                self.font_small,
                MUTED,
                "center",
            )

    def draw_board_game_header(self, title: str) -> None:
        width, _ = self.screen.get_size()
        if self.touch_controls:
            draw_text(self.screen, title, (width // 2, 34), self.font_label, PAPER, "center")
        else:
            draw_text(self.screen, "<  ARCADE", (48, 34), self.font_label, MUTED, "midleft")
            draw_text(self.screen, title, (width // 2, 34), make_font(17, True), PAPER, "center")
            pygame.draw.line(self.screen, LINE, (48, 62), (width - 48, 62), 1)

    def draw_board_game_mode(self, difficulty: str) -> None:
        rect = self.board_game_mode_rect()
        color = MINT if difficulty == "hard" else GOLD if difficulty == "normal" else PANEL_LIGHT
        text_color = BACKGROUND if difficulty != "two_players" else PAPER
        rounded(self.screen, color, rect, 6)
        label = {"two_players": "TWO PLAYERS", "normal": "NORMAL", "hard": "HARD"}[difficulty]
        draw_text(self.screen, label, rect.center, self.font_label, text_color, "center")

    def draw_tictactoe(self) -> None:
        self.draw_board_game_header("TIC-TAC-TOE")
        self.draw_board_game_mode(self.tictactoe.bot_difficulty)
        board = self.tictactoe_board_rect()
        cell = board.width // 3
        rounded(self.screen, (36, 44, 41), board, 8)
        for row in range(3):
            for column in range(3):
                square = pygame.Rect(
                    board.left + column * cell + 4,
                    board.top + row * cell + 4,
                    cell - 8,
                    cell - 8,
                )
                rounded(self.screen, PANEL, square, 8)
                mark = self.tictactoe.board[row * 3 + column]
                if mark is not None:
                    color = CORAL if mark == "X" else MINT
                    draw_text(
                        self.screen,
                        mark,
                        square.center,
                        make_font(max(36, cell * 2 // 3), True),
                        color,
                        "center",
                    )

        if self.tictactoe.winning_line:
            start_index, _, end_index = self.tictactoe.winning_line
            start = (
                board.left + (start_index % 3) * cell + cell // 2,
                board.top + (start_index // 3) * cell + cell // 2,
            )
            end = (
                board.left + (end_index % 3) * cell + cell // 2,
                board.top + (end_index // 3) * cell + cell // 2,
            )
            pygame.draw.line(self.screen, GOLD, start, end, max(4, cell // 18))

        if self.tictactoe.winner:
            status = f"{self.tictactoe.winner} WINS!"
        elif self.tictactoe.draw:
            status = "DRAW GAME"
        else:
            status = f"{self.tictactoe.current_player} TO MOVE"
        if self.tictactoe.bot_mode and not self.tictactoe.over:
            status += "  ·  YOU ARE X"
        draw_text(self.screen, status, (board.centerx, board.top - 30), self.font_body, MINT, "midbottom")
        if not self.touch_controls:
            controls = (
                "BOT MODE   ·   CLICK AN EMPTY SQUARE   ·   R NEW GAME"
                if self.tictactoe.bot_mode
                else "LOCAL TWO-PLAYER   ·   CLICK A SQUARE   ·   R NEW GAME"
            )
            draw_text(
                self.screen,
                controls,
                (board.centerx, board.bottom + 18),
                self.font_label,
                MUTED,
                "midtop",
            )
        if self.tictactoe.over:
            title = f"{self.tictactoe.winner} WINS!" if self.tictactoe.winner else "DRAW GAME"
            self.draw_game_overlay(title, "NICE PLAY!", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_chess(self) -> None:
        self.draw_board_game_header("POCKET CHESS")
        self.draw_board_game_mode(self.chess.bot_difficulty)
        board = self.chess_board_rect()
        cell = board.width // 8
        light_square = (226, 218, 190)
        dark_square = (79, 119, 93)
        destinations = {move.end for move in self.chess_moves}
        last_start = self.chess_selection

        for row in range(8):
            for column in range(8):
                square = (row, column)
                rect = pygame.Rect(
                    board.left + column * cell,
                    board.top + row * cell,
                    cell,
                    cell,
                )
                color = light_square if (row + column) % 2 == 0 else dark_square
                if square == last_start:
                    color = (182, 170, 105)
                pygame.draw.rect(self.screen, color, rect)
                piece = self.chess.board[row][column]
                if piece is not None:
                    white_piece = piece.isupper()
                    radius = max(10, cell // 3)
                    center = rect.center
                    pygame.draw.circle(
                        self.screen,
                        (247, 244, 224) if white_piece else (37, 43, 42),
                        center,
                        radius,
                    )
                    pygame.draw.circle(
                        self.screen,
                        (54, 60, 53) if white_piece else (218, 220, 202),
                        center,
                        radius,
                        width=max(1, cell // 30),
                    )
                    draw_text(
                        self.screen,
                        piece.upper(),
                        center,
                        make_font(max(17, cell // 2), True),
                        (39, 45, 54) if white_piece else (244, 239, 215),
                        "center",
                    )
                if square in destinations:
                    target_center = rect.center
                    if piece is None:
                        pygame.draw.circle(
                            self.screen,
                            (45, 64, 46),
                            target_center,
                            max(4, cell // 10),
                        )
                    else:
                        pygame.draw.circle(
                            self.screen,
                            GOLD,
                            target_center,
                            cell // 2 - 3,
                            width=max(2, cell // 18),
                        )

        for index in range(8):
            draw_text(
                self.screen,
                str(8 - index),
                (board.left - 10, board.top + index * cell + cell // 2),
                self.font_label,
                PAPER,
                "midright",
            )
            draw_text(
                self.screen,
                ChessGame.files[index],
                (board.left + index * cell + cell // 2, board.bottom + 5),
                self.font_label,
                PAPER,
                "midtop",
            )

        if self.chess.over:
            if self.chess.winner is not None:
                status = f"CHECKMATE  ·  {'WHITE' if self.chess.winner else 'BLACK'} WINS"
            else:
                status = self.chess.draw_reason or "DRAW"
        elif self.chess.in_check:
            status = f"{self.chess.turn_name.upper()} IN CHECK"
        else:
            status = f"{self.chess.turn_name.upper()} TO MOVE"
        if self.chess.bot_mode and not self.chess.over:
            status += "  ·  YOU ARE WHITE"
        draw_text(self.screen, status, (board.centerx, board.top - 12), self.font_label, GOLD if self.chess.in_check else PAPER, "midbottom")
        if not self.touch_controls:
            controls = (
                "BOT MODE   ·   SELECT A PIECE, THEN A HIGHLIGHTED SQUARE   ·   PAWNS PROMOTE TO QUEEN"
                if self.chess.bot_mode
                else "LOCAL TWO-PLAYER   ·   SELECT A PIECE, THEN A HIGHLIGHTED SQUARE   ·   PAWNS PROMOTE TO QUEEN"
            )
            draw_text(
                self.screen,
                controls,
                (board.centerx, board.bottom + 20),
                self.font_label,
                MUTED,
                "midtop",
            )
        if self.chess.over:
            title = "CHECKMATE" if self.chess.winner is not None else (self.chess.draw_reason or "DRAW")
            subtitle = f"{'WHITE' if self.chess.winner else 'BLACK'} WINS" if self.chess.winner is not None else "DRAW GAME"
            self.draw_game_overlay(title, subtitle, "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_solitaire(self) -> None:
        width, height = self.screen.get_size()
        self.screen.fill((27, 86, 59))
        if self.touch_controls:
            draw_text(self.screen, "POCKET SOLITAIRE", (width // 2, 34), self.font_label, PAPER, "center")
        else:
            self.draw_game_header("POCKET SOLITAIRE", self.best_scores["solitaire"])

        columns, top, tableau_top, card_width, card_height = self.solitaire_layout()
        stock_rect = self.solitaire_card_rect("stock")
        waste_rect = self.solitaire_card_rect("waste")
        if self.solitaire.stock:
            self.draw_solitaire_card(Card(1, "♠", False), stock_rect)
        else:
            self.draw_solitaire_slot(stock_rect, "↻")
        if self.solitaire.waste:
            self.draw_solitaire_card(self.solitaire.waste[-1], waste_rect)
        else:
            self.draw_solitaire_slot(waste_rect)

        for index, suit in enumerate(self.solitaire.suits):
            rect = self.solitaire_card_rect("foundation", index)
            pile = self.solitaire.foundations[index]
            if pile:
                self.draw_solitaire_card(pile[-1], rect)
            else:
                self.draw_solitaire_slot(rect, suit, self._solitaire_suit_color(suit))

        draw_text(self.screen, f"MOVES  {self.solitaire.moves:03}", (columns[2], top + card_height // 3), self.font_label, PAPER)
        draw_text(self.screen, f"SCORE  {self.solitaire.score:04}", (columns[2], top + card_height // 3 + 22), self.font_label, GOLD)

        for column, pile in enumerate(self.solitaire.tableau):
            if not pile:
                self.draw_solitaire_slot(
                    self.solitaire_card_rect("tableau", column),
                    "K",
                    (118, 166, 137),
                )
            for card_index, card in enumerate(pile):
                rect = self.solitaire_card_rect("tableau", column, card_index)
                self.draw_solitaire_card(card, rect)

        selection = self.solitaire_selection
        if self.solitaire_dragging and self.solitaire_mouse_source is not None:
            selection = self.solitaire_mouse_source
        if selection is not None:
            kind, index, start_index = selection
            selected_rect = self.solitaire_card_rect(
                kind,
                index,
                start_index if kind == "tableau" else None,
            )
            pygame.draw.rect(self.screen, GOLD, selected_rect, width=2, border_radius=8)

        if self.solitaire_dragging and self.solitaire_mouse_source is not None and self.solitaire_drag_position is not None:
            kind, index, start_index = self.solitaire_mouse_source
            if kind == "tableau":
                cards = self.solitaire.tableau[index][start_index:]
            elif kind == "waste":
                cards = self.solitaire.waste[-1:]
            else:
                cards = self.solitaire.foundations[index][-1:]
            x = self.solitaire_drag_position[0] - card_width // 2
            y = self.solitaire_drag_position[1] - card_height // 2
            for card_index, card in enumerate(cards):
                self.draw_solitaire_card(
                    card,
                    pygame.Rect(x, y + card_index * max(18, card_height // 4), card_width, card_height),
                )

        if not self.touch_controls:
            draw_text(
                self.screen,
                "CLICK OR DRAG CARDS   ·   CLICK STOCK TO DEAL   ·   DOUBLE-CLICK A CARD FOR FOUNDATION",
                (width // 2, height - 23),
                self.font_label,
                PAPER,
                "midbottom",
            )
        if self.solitaire.won:
            self.draw_game_overlay("SOLITAIRE!", f"{self.solitaire.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_solitaire_slot(
        self,
        rect: pygame.Rect,
        label: str = "",
        color: tuple[int, int, int] = (88, 132, 103),
    ) -> None:
        rounded(self.screen, (25, 77, 53), rect, 8)
        pygame.draw.rect(self.screen, (111, 153, 125), rect, width=1, border_radius=8)
        if label:
            draw_text(self.screen, label, rect.center, make_font(max(18, rect.width // 3), True), color, "center")

    def draw_solitaire_card(self, card: Card, rect: pygame.Rect) -> None:
        if not card.face_up:
            rounded(self.screen, (42, 57, 91), rect, 8)
            inner = rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, (128, 150, 195), inner, width=1, border_radius=5)
            for x in range(inner.left + 8, inner.right, 12):
                pygame.draw.line(self.screen, (86, 108, 153), (x, inner.top), (x, inner.bottom), 1)
            return

        rounded(self.screen, (246, 245, 232), rect, 8)
        pygame.draw.rect(self.screen, (198, 202, 190), rect, width=1, border_radius=8)
        color = self._solitaire_suit_color(card.suit)
        label = SolitaireGame.rank_labels[card.rank]
        draw_text(self.screen, label, (rect.left + 6, rect.top + 4), make_font(max(12, rect.width // 5), True), color)
        draw_text(self.screen, card.suit, (rect.left + 6, rect.top + rect.height // 5), make_font(max(11, rect.width // 6), True), color)
        draw_text(self.screen, card.suit, rect.center, make_font(max(20, rect.width // 2), True), color, "center")

    @staticmethod
    def _solitaire_suit_color(suit: str) -> tuple[int, int, int]:
        return (198, 57, 66) if suit in ("♥", "♦") else (39, 45, 54)

    def draw_snake(self) -> None:
        self.draw_game_header("NEON SNAKE", self.best_scores["snake"])
        width, height = self.screen.get_size()
        unit = max(18, min((width - 120) // self.snake.width, (height - 225) // self.snake.height))
        board = pygame.Rect(0, 0, unit * self.snake.width, unit * self.snake.height)
        vertical_offset = 72 if self.touch_controls else 0
        board.center = (width // 2, (height - vertical_offset) // 2 + 20)
        rounded(self.screen, (30, 39, 32), board, 5)
        for x in range(self.snake.width + 1):
            pygame.draw.line(self.screen, GRID, (board.left + x * unit, board.top), (board.left + x * unit, board.bottom), 1)
        for y in range(self.snake.height + 1):
            pygame.draw.line(self.screen, GRID, (board.left, board.top + y * unit), (board.right, board.top + y * unit), 1)
        if self.snake.food:
            food_rect = pygame.Rect(board.left + self.snake.food[0] * unit + 4, board.top + self.snake.food[1] * unit + 4, unit - 8, unit - 8)
            pygame.draw.ellipse(self.screen, CORAL, food_rect)
        for index, (x, y) in enumerate(self.snake.snake):
            segment = pygame.Rect(board.left + x * unit + 2, board.top + y * unit + 2, unit - 4, unit - 4)
            rounded(self.screen, MINT if index == 0 else (145, 208, 112), segment, max(3, unit // 5))
        draw_text(self.screen, f"SCORE  {self.snake.score:02}", (board.left, board.top - 29), self.font_label, MINT)
        if not self.touch_controls:
            draw_text(self.screen, "ARROWS / WASD     ·     R RESTART     ·     ESC ARCADE", (width // 2, board.bottom + 27), self.font_label, MUTED, "midtop")
        if self.snake.over:
            title = "BOARD CLEARED" if self.snake.won else "THAT'S A WRAP"
            self.draw_game_overlay(title, f"{self.snake.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_tetris(self) -> None:
        self.draw_game_header("POCKET TETRIS", self.best_scores["tetris"])
        width, height = self.screen.get_size()
        unit = max(16, min((width - 180) // self.tetris.width, (height - 220) // self.tetris.height))
        board = pygame.Rect(0, 0, unit * self.tetris.width, unit * self.tetris.height)
        vertical_offset = 72 if self.touch_controls else 0
        board.center = (width // 2 - 75, (height - vertical_offset) // 2 + 15)
        rounded(self.screen, (30, 39, 32), board, 5)
        for y, row in enumerate(self.tetris.board):
            for x, piece in enumerate(row):
                if piece:
                    rect = pygame.Rect(board.left + x * unit + 1, board.top + y * unit + 1, unit - 2, unit - 2)
                    rounded(self.screen, TETRIS_COLORS[piece], rect, max(2, unit // 7))
        if not self.tetris.over:
            for dx, dy in self.tetris.piece:
                rect = pygame.Rect(board.left + (self.tetris.x + dx) * unit + 1, board.top + (self.tetris.y + dy) * unit + 1, unit - 2, unit - 2)
                rounded(self.screen, TETRIS_COLORS[self.tetris.current_piece], rect, max(2, unit // 7))
        side_x = board.right + 30
        draw_text(self.screen, "SCORE", (side_x, board.top + 20), self.font_label, MUTED)
        draw_text(self.screen, f"{self.tetris.score:06}", (side_x, board.top + 40), self.font_heading, PAPER)
        draw_text(self.screen, "LINES", (side_x, board.top + 105), self.font_label, MUTED)
        draw_text(self.screen, f"{self.tetris.lines:02}", (side_x, board.top + 125), self.font_heading, MINT)
        draw_text(self.screen, "NEXT", (side_x, board.top + 190), self.font_label, MUTED)
        for dx, dy in self.tetris.shapes[self.tetris.next_piece]:
            rect = pygame.Rect(side_x + dx * 19, board.top + 225 + dy * 19, 17, 17)
            rounded(self.screen, TETRIS_COLORS[self.tetris.next_piece], rect, 4)
        if not self.touch_controls:
            draw_text(self.screen, "← → MOVE   ↑ ROTATE", (width // 2, board.bottom + 18), self.font_label, MUTED, "midtop")
            draw_text(self.screen, "↓ DROP   SPACE HARD DROP   R RESTART", (width // 2, board.bottom + 37), self.font_label, MUTED, "midtop")
        if self.tetris.over:
            self.draw_game_overlay("GAME OVER", f"{self.tetris.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_2048(self) -> None:
        self.draw_game_header("2048", self.best_scores["2048"])
        width, height = self.screen.get_size()
        unit = max(24, min((width - 100) // 4, (height - 205) // 4, 112))
        gap = max(5, unit // 10)
        side = unit * 4 + gap * 5
        board = pygame.Rect(0, 0, side, side)
        board.center = (width // 2, (height - (72 if self.touch_controls else 0)) // 2 + 20)
        rounded(self.screen, (95, 83, 72), board, 8)
        for row in range(self.game2048.size):
            for column in range(self.game2048.size):
                value = self.game2048.board[row][column]
                rect = pygame.Rect(
                    board.left + gap + column * (unit + gap),
                    board.top + gap + row * (unit + gap),
                    unit,
                    unit,
                )
                color = TILE_COLORS.get(value, (60, 58, 52)) if value else (117, 105, 94)
                rounded(self.screen, color, rect, max(4, unit // 9))
                if value:
                    text_color = (70, 62, 52) if value <= 4 else PAPER
                    font_size = max(15, unit // (2 if value < 1000 else 2.8))
                    draw_text(
                        self.screen,
                        str(value),
                        rect.center,
                        make_font(int(font_size), True),
                        text_color,
                        "center",
                    )
        draw_text(self.screen, f"SCORE  {self.game2048.score}", (board.left, board.top - 28), self.font_label, GOLD)
        if self.game2048.won and not self.game2048.over:
            draw_text(self.screen, "2048 REACHED  ·  KEEP PLAYING", (board.right, board.top - 28), self.font_label, MINT, "topright")
        if not self.touch_controls:
            draw_text(
                self.screen,
                "ARROWS / WASD TO SLIDE     ·     R RESTART     ·     ESC ARCADE",
                (width // 2, board.bottom + 18),
                self.font_label,
                MUTED,
                "midtop",
            )
        if self.game2048.over:
            title = "2048 REACHED!" if self.game2048.won else "NO MORE MOVES"
            self.draw_game_overlay(title, f"{self.game2048.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_wordle(self) -> None:
        width, height = self.screen.get_size()
        draw_text(self.screen, "<  ARCADE", (48, 34), self.font_label, MUTED, "midleft")
        draw_text(self.screen, "WORDLE", (width // 2, 34), make_font(17, True), PAPER, "center")
        pygame.draw.line(self.screen, LINE, (48, 62), (width - 48, 62), 1)
        language_rect = self.wordle_language_rect()
        rounded(self.screen, PANEL, language_rect, 5)
        draw_text(
            self.screen,
            self.wordle.text("language"),
            language_rect.center,
            self.font_label,
            MINT,
            "center",
        )

        keyboard = self.wordle_keyboard_rects()
        keyboard_top = min(rect.top for rect in keyboard.values())
        cell_gap = 5
        cell = min(
            58,
            (width - 80 - cell_gap * 4) // self.wordle.word_length,
            (keyboard_top - 150 - cell_gap * (self.wordle.max_guesses - 1)) // self.wordle.max_guesses,
        )
        cell = max(16, cell)
        board_width = cell * self.wordle.word_length + cell_gap * (self.wordle.word_length - 1)
        board_height = cell * self.wordle.max_guesses + cell_gap * (self.wordle.max_guesses - 1)
        board_left = (width - board_width) // 2
        board_top = max(104, (keyboard_top - board_height - 18 + 116) // 2)

        draw_text(
            self.screen,
            f"{self.wordle.text('guess')} {min(len(self.wordle.guesses) + 1, self.wordle.max_guesses)} / {self.wordle.max_guesses}",
            (width // 2, 98),
            self.font_label,
            MUTED,
            "midtop",
        )
        status_text = self.wordle.message
        if self.wordle.over and not self.wordle.won:
            answer = "".join(self.wordle.display_letter(letter) for letter in self.wordle.answer)
            status_text = f"{self.wordle.text('answer')} {answer}"
        if status_text:
            draw_text(self.screen, status_text, (width // 2, board_top - 8), self.font_label, MINT, "midbottom")

        for row in range(self.wordle.max_guesses):
            guess = self.wordle.guesses[row] if row < len(self.wordle.guesses) else ""
            if row == len(self.wordle.guesses) and not self.wordle.over:
                guess = self.wordle.current_guess
            feedback = self.wordle.evaluate_guess(guess) if row < len(self.wordle.guesses) else ()
            for column in range(self.wordle.word_length):
                rect = pygame.Rect(
                    board_left + column * (cell + cell_gap),
                    board_top + row * (cell + cell_gap),
                    cell,
                    cell,
                )
                if row < len(self.wordle.guesses):
                    color = WORDLE_COLORS[feedback[column]]
                    border = color
                elif column < len(guess):
                    color = PANEL
                    border = MUTED
                else:
                    color = BACKGROUND
                    border = LINE
                rounded(self.screen, color, rect, 4)
                if row >= len(self.wordle.guesses):
                    pygame.draw.rect(self.screen, border, rect, width=2, border_radius=4)
                if column < len(guess):
                    draw_text(
                        self.screen,
                        self.wordle.display_letter(guess[column]),
                        rect.center,
                        make_font(max(16, cell // 2), True),
                        PAPER,
                        "center",
                    )

        for key, rect in keyboard.items():
            if key in ("ENTER", "BACK"):
                label = self.wordle.text("enter") if key == "ENTER" else "⌫"
                color = (48, 59, 65)
                text_font = self.font_label if key == "ENTER" else self.font_body
            else:
                label = key
                color = WORDLE_COLORS.get(self.wordle.letter_status.get(key.lower()), (48, 59, 65))
                text_font = self.font_body
            rounded(self.screen, color, rect, 5)
            draw_text(self.screen, label, rect.center, text_font, PAPER, "center")

        if self.wordle.won:
            draw_text(self.screen, self.wordle.text("solved"), (width // 2, board_top + board_height + 8), self.font_label, MINT, "midtop")
        elif self.wordle.over:
            draw_text(self.screen, self.wordle.text("restart"), (width // 2, board_top + board_height + 8), self.font_label, MUTED, "midtop")

    def draw_flappy(self) -> None:
        self.draw_game_header("FLAPPY BIRD", self.best_scores["flappy"])
        width, height = self.screen.get_size()
        available_height = height - (150 if self.touch_controls else 130)
        scale = min((width - 80) / self.flappy.width, available_height / self.flappy.height)
        scale = max(0.35, scale)
        scene_width = int(self.flappy.width * scale)
        scene_height = int(self.flappy.height * scale)
        scene = pygame.Rect(0, 0, scene_width, scene_height)
        scene.center = (
            width // 2,
            (height - (72 if self.touch_controls else 0)) // 2 + 40,
        )
        rounded(self.screen, (113, 190, 230), scene, 8)
        pygame.draw.circle(
            self.screen,
            (165, 221, 239),
            (scene.left + int(55 * scale), scene.top + int(75 * scale)),
            max(8, int(27 * scale)),
        )
        pygame.draw.circle(
            self.screen,
            (165, 221, 239),
            (scene.left + int(286 * scale), scene.top + int(153 * scale)),
            max(8, int(32 * scale)),
        )
        for pipe_x, gap_center in self.flappy.pipes:
            x = scene.left + int(pipe_x * scale)
            gap_top = scene.top + int((gap_center - self.flappy.pipe_gap / 2) * scale)
            gap_bottom = scene.top + int((gap_center + self.flappy.pipe_gap / 2) * scale)
            pipe_width = max(4, int(self.flappy.pipe_width * scale))
            pygame.draw.rect(self.screen, (71, 166, 91), (x, scene.top, pipe_width, gap_top - scene.top))
            pygame.draw.rect(self.screen, (71, 166, 91), (x, gap_bottom, pipe_width, scene.bottom - gap_bottom))
            cap = max(5, int(8 * scale))
            pygame.draw.rect(self.screen, (50, 138, 72), (x - cap // 2, gap_top - cap, pipe_width + cap, cap))
            pygame.draw.rect(self.screen, (50, 138, 72), (x - cap // 2, gap_bottom, pipe_width + cap, cap))
        pygame.draw.rect(
            self.screen,
            (221, 199, 143),
            (scene.left, scene.bottom - max(8, int(14 * scale)), scene.width, max(8, int(14 * scale))),
        )
        bird_center = (
            scene.left + int(self.flappy.bird_x * scale),
            scene.top + int(self.flappy.bird_y * scale),
        )
        pygame.draw.circle(self.screen, GOLD, bird_center, max(5, int(self.flappy.bird_radius * scale)))
        pygame.draw.circle(self.screen, PAPER, (bird_center[0] + max(2, int(5 * scale)), bird_center[1] - max(1, int(4 * scale))), max(2, int(4 * scale)))
        pygame.draw.circle(self.screen, BACKGROUND, (bird_center[0] + max(3, int(6 * scale)), bird_center[1] - max(1, int(4 * scale))), max(1, int(2 * scale)))
        draw_text(self.screen, f"SCORE  {self.flappy.score:02}", (scene.centerx, scene.top + 16), make_font(max(18, int(27 * scale)), True), PAPER, "midtop")
        if not self.touch_controls:
            draw_text(
                self.screen,
                "SPACE / UP / CLICK TO FLAP     ·     R RESTART     ·     ESC ARCADE",
                (width // 2, scene.bottom + 18),
                self.font_label,
                MUTED,
                "midtop",
            )
        if self.flappy.over:
            self.draw_game_overlay("GAME OVER", f"{self.flappy.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_geometry_dash(self) -> None:
        game = self.geometry_dash
        self.draw_game_header("GEOMETRY DASH", self.best_scores["geometry_dash"])
        width, height = self.screen.get_size()
        available_height = height - (150 if self.touch_controls else 130)
        scale = max(0.35, min((width - 80) / game.width, available_height / game.height))
        scene_width = int(game.width * scale)
        scene_height = int(game.height * scale)
        scene = pygame.Rect(0, 0, scene_width, scene_height)
        scene.center = (width // 2, (height - (72 if self.touch_controls else 0)) // 2 + 40)
        rounded(self.screen, (22, 27, 55), scene, 8)

        for x in range(0, game.width + 1, 32):
            position = scene.left + int(x * scale)
            pygame.draw.line(self.screen, (37, 45, 80), (position, scene.top), (position, scene.bottom), 1)
        ground = scene.top + int(game.ground_y * scale)
        pygame.draw.rect(self.screen, (69, 224, 172), (scene.left, ground, scene.width, max(3, int(4 * scale))))
        pygame.draw.rect(
            self.screen,
            (35, 44, 75),
            (scene.left, ground + max(3, int(4 * scale)), scene.width, scene.bottom - ground),
        )

        for obstacle_x in game.obstacles:
            left = scene.left + int(obstacle_x * scale)
            pygame.draw.polygon(
                self.screen,
                (255, 91, 137),
                (
                    (left, ground),
                    (left + int(game.spike_width * scale / 2), ground - int(game.spike_height * scale)),
                    (left + int(game.spike_width * scale), ground),
                ),
            )

        player = pygame.Rect(
            scene.left + int(game.player_x * scale),
            scene.top + int(game.player_y * scale),
            max(1, int(game.player_size * scale)),
            max(1, int(game.player_size * scale)),
        )
        pygame.draw.rect(self.screen, GOLD, player, border_radius=max(2, int(3 * scale)))
        pygame.draw.rect(self.screen, PAPER, player, width=max(1, int(2 * scale)), border_radius=max(2, int(3 * scale)))
        draw_text(
            self.screen,
            f"SPIKES CLEARED  {game.score:02}",
            (scene.centerx, scene.top + 13),
            self.font_label,
            PAPER,
            "midtop",
        )
        if not self.touch_controls:
            draw_text(
                self.screen,
                "SPACE / UP / W / CLICK TO JUMP     ·     R RESTART     ·     ESC ARCADE",
                (width // 2, scene.bottom + 18),
                self.font_label,
                MUTED,
                "midtop",
            )
        if game.over:
            self.draw_game_overlay("CRASHED!", f"{game.score} SPIKES CLEARED", "R  TRY AGAIN     ·     ESC  ARCADE")

    def draw_left_right(self) -> None:
        game = self.left_right
        self.draw_game_header("MAZE RUNNER", self.best_scores["left_right"])
        width, height = self.screen.get_size()
        cell = max(12, min((width - 100) // game.width, (height - 180) // game.height))
        board = pygame.Rect(0, 0, cell * game.width, cell * game.height)
        board.center = (width // 2, height // 2 + (0 if self.touch_controls else 12))
        rounded(self.screen, (16, 23, 24), board, 8)
        for row_index, row in enumerate(game.rows):
            for column, is_open in enumerate(row):
                rect = pygame.Rect(
                    board.left + column * cell + 2,
                    board.top + row_index * cell + 2,
                    cell - 4,
                    cell - 4,
                )
                color = (42, 55, 55) if is_open else (185, 55, 55)
                rounded(self.screen, color, rect, max(2, cell // 6))
        ball_center = (
            board.left + game.x * cell + cell // 2,
            board.top + game.player_row * cell + cell // 2,
        )
        pygame.draw.circle(self.screen, GOLD, ball_center, max(5, cell // 2 - 4))
        pygame.draw.circle(self.screen, PAPER, (ball_center[0] - cell // 8, ball_center[1] - cell // 8), max(2, cell // 10))
        draw_text(
            self.screen,
            f"DISTANCE  {game.score:04}  ·  ENDLESS",
            (board.centerx, board.top - 24),
            self.font_label,
            MINT,
            "midbottom",
        )
        if not self.touch_controls:
            draw_text(
                self.screen,
                "LEFT / RIGHT OR A / D TO STEER     ·     R RESTART     ·     ESC ARCADE",
                (width // 2, board.bottom + 18),
                self.font_label,
                MUTED,
                "midtop",
            )
        if game.over:
            self.draw_game_overlay("WALL AHEAD!", f"DISTANCE  {game.score}", "R  TRY AGAIN     ·     ESC  ARCADE")

    def draw_pacman(self) -> None:
        self.draw_game_header("PAC-MAN", self.best_scores["pacman"])
        width, height = self.screen.get_size()
        maze_height, maze_width = len(self.pacman.grid), len(self.pacman.grid[0])
        unit = max(20, min((width - 120) // maze_width, (height - 220) // maze_height))
        board = pygame.Rect(0, 0, unit * maze_width, unit * maze_height)
        vertical_offset = 72 if self.touch_controls else 0
        board.center = (width // 2, (height - vertical_offset) // 2 + 15)
        rounded(self.screen, (13, 17, 29), board, 5)
        for y, row in enumerate(self.pacman.grid):
            for x, cell in enumerate(row):
                center = (board.left + x * unit + unit // 2, board.top + y * unit + unit // 2)
                if cell == "#":
                    rect = pygame.Rect(board.left + x * unit + 2, board.top + y * unit + 2, unit - 4, unit - 4)
                    rounded(self.screen, (55, 85, 177), rect, max(3, unit // 5))
                elif cell == ".":
                    pygame.draw.circle(self.screen, (244, 215, 164), center, max(2, unit // 12))
                elif cell == "o":
                    pygame.draw.circle(self.screen, PAPER, center, max(4, unit // 5))
        player_center = (board.left + self.pacman.player[0] * unit + unit // 2, board.top + self.pacman.player[1] * unit + unit // 2)
        pygame.draw.circle(self.screen, GOLD, player_center, unit // 2 - 3)
        dx, dy = self.pacman.direction
        if dx or dy:
            mouth = (player_center[0] + dx * unit // 2, player_center[1] + dy * unit // 2)
            pygame.draw.polygon(self.screen, (13, 17, 29), (player_center, (mouth[0] - dy * unit // 4, mouth[1] + dx * unit // 4), (mouth[0] + dy * unit // 4, mouth[1] - dx * unit // 4)))
        ghost_colors = (CORAL, (255, 153, 213), (103, 210, 235))
        for index, (gx, gy) in enumerate(self.pacman.ghosts):
            center = (board.left + gx * unit + unit // 2, board.top + gy * unit + unit // 2)
            color = (89, 107, 230) if self.pacman.power_ticks else ghost_colors[index]
            pygame.draw.circle(self.screen, color, center, unit // 2 - 3)
            eye_y = center[1] - unit // 10
            for eye_x in (center[0] - unit // 7, center[0] + unit // 7):
                pygame.draw.circle(self.screen, PAPER, (eye_x, eye_y), max(2, unit // 9))
                pygame.draw.circle(self.screen, BACKGROUND, (eye_x, eye_y), max(1, unit // 18))
        draw_text(self.screen, f"SCORE  {self.pacman.score:04}", (board.left, board.top - 27), self.font_label, GOLD)
        draw_text(self.screen, f"DOTS  {self.pacman.dots_remaining:03}", (board.right, board.top - 27), self.font_label, MUTED, "topright")
        if not self.touch_controls:
            draw_text(self.screen, "ARROWS / WASD     ·     R RESTART     ·     ESC ARCADE", (width // 2, board.bottom + 22), self.font_label, MUTED, "midtop")
        if self.pacman.over:
            title = "MAZE CLEARED" if self.pacman.won else "CAUGHT!"
            self.draw_game_overlay(title, f"{self.pacman.score} POINTS", "R  PLAY AGAIN     ·     ESC  ARCADE")

    def draw_game_overlay(self, title: str, subtitle: str, footer: str) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((12, 15, 13, 205))
        self.screen.blit(overlay, (0, 0))
        center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        draw_text(self.screen, title, (center[0], center[1] - 30), self.font_heading, MINT, "center")
        draw_text(self.screen, subtitle, (center[0], center[1] + 8), self.font_body, PAPER, "center")
        draw_text(self.screen, footer, (center[0], center[1] + 43), self.font_label, MUTED, "center")


def main() -> None:
    ArcadeApp().run()


if __name__ == "__main__":
    main()