import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle, Ellipse, Triangle
from kivy.core.window import Window
from kivy.clock import Clock


# --- Game constants ---
BOARD_ROWS = 4
BOARD_COLS = 4

# Colors (RGBA 0..1)
COLOR_BG = (28/255, 33/255, 38/255, 1)
COLOR_GRID = (0.78, 0.78, 0.78, 1)
COLOR_MOVE = (80/255, 170/255, 255/255, 1)
COLOR_HL = (1.0, 0.84, 0.0, 1)
COLOR_TEXT = (0.96, 0.96, 0.96, 1)
COLOR_SUBTEXT = (0.72, 0.72, 0.72, 1)

COLOR_P1 = (64/255, 160/255, 255/255, 1)
COLOR_P2 = (255/255, 100/255, 100/255, 1)
COLOR_P1_DARK = (40/255, 110/255, 180/255, 1)
COLOR_P2_DARK = (180/255, 60/255, 60/255, 1)

PIECE_CIRCLE = "circle"
PIECE_SQUARE = "square"
PIECE_TRIANGLE = "triangle"

PLAYER_ONE = 1
PLAYER_TWO = 2


@dataclass
class Piece:
    owner_id: int
    piece_type: str
    row: int
    col: int
    forward_dir: int
    piece_id: int


class GameState:
    def __init__(self) -> None:
        self.pieces: List[Piece] = []
        self.board: Dict[Tuple[int, int], Piece] = {}
        self.current_player: int = PLAYER_ONE
        self.captured_by_player: Dict[int, int] = {PLAYER_ONE: 0, PLAYER_TWO: 0}
        self.winner: Optional[int] = None
        self._next_piece_id: int = 1
        self.moved_piece_ids_this_turn: Set[int] = set()

    def _new_id(self) -> int:
        pid = self._next_piece_id
        self._next_piece_id += 1
        return pid

    def _are_adjacent(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1

    def _generate_non_adjacent_start_positions(self) -> List[Tuple[int, int]]:
        cells = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)]
        for _ in range(2000):
            placements = random.sample(cells, 6)
            p1_cells = placements[:3]
            p2_cells = placements[3:]
            ok = True
            for a in p1_cells:
                for b in p2_cells:
                    if self._are_adjacent(a, b):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return placements
        # Fallback: P1 top row, P2 bottom row
        cols = list(range(BOARD_COLS))
        random.shuffle(cols)
        p1_cols = cols[:3]
        random.shuffle(cols)
        p2_cols = cols[:3]
        p1_cells = [(0, c) for c in p1_cols]
        p2_cells = [(BOARD_ROWS - 1, c) for c in p2_cols]
        return p1_cells + p2_cells

    def setup_random(self) -> None:
        self.pieces.clear()
        self.board.clear()
        self.current_player = PLAYER_ONE
        self.captured_by_player = {PLAYER_ONE: 0, PLAYER_TWO: 0}
        self.winner = None
        self.moved_piece_ids_this_turn.clear()
        self._next_piece_id = 1

        placements = self._generate_non_adjacent_start_positions()
        # P1 forward down
        self.pieces.append(Piece(PLAYER_ONE, PIECE_CIRCLE, placements[0][0], placements[0][1], +1, self._new_id()))
        self.pieces.append(Piece(PLAYER_ONE, PIECE_SQUARE, placements[1][0], placements[1][1], +1, self._new_id()))
        self.pieces.append(Piece(PLAYER_ONE, PIECE_TRIANGLE, placements[2][0], placements[2][1], +1, self._new_id()))
        # P2 forward up
        self.pieces.append(Piece(PLAYER_TWO, PIECE_CIRCLE, placements[3][0], placements[3][1], -1, self._new_id()))
        self.pieces.append(Piece(PLAYER_TWO, PIECE_SQUARE, placements[4][0], placements[4][1], -1, self._new_id()))
        self.pieces.append(Piece(PLAYER_TWO, PIECE_TRIANGLE, placements[5][0], placements[5][1], -1, self._new_id()))

        self.rebuild_board_index()

    def rebuild_board_index(self) -> None:
        self.board.clear()
        for p in self.pieces:
            self.board[(p.row, p.col)] = p

    def piece_at(self, row: int, col: int) -> Optional[Piece]:
        return self.board.get((row, col))

    def is_inside(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS

    def can_capture(self, attacker: Piece, defender: Piece) -> bool:
        if attacker.owner_id == defender.owner_id:
            return False
        if attacker.piece_type == PIECE_TRIANGLE:
            return defender.piece_type == PIECE_CIRCLE
        if attacker.piece_type == PIECE_CIRCLE:
            return defender.piece_type == PIECE_SQUARE
        if attacker.piece_type == PIECE_SQUARE:
            return defender.piece_type == PIECE_TRIANGLE
        return False

    def get_legal_moves_for(self, piece: Piece) -> List[Tuple[int, int]]:
        # Disallow moving same piece twice in a turn
        if piece.piece_id in self.moved_piece_ids_this_turn:
            return []

        directions: List[Tuple[int, int]] = []
        if piece.piece_type == PIECE_CIRCLE:
            directions = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        elif piece.piece_type == PIECE_SQUARE:
            directions = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
        elif piece.piece_type == PIECE_TRIANGLE:
            f = piece.forward_dir
            directions = [(f, -1), (f, +1), (-f, 0)]

        legal: List[Tuple[int, int]] = []
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            if not self.is_inside(nr, nc):
                continue
            occ = self.piece_at(nr, nc)
            if occ is None:
                legal.append((nr, nc))
                continue
            if occ.owner_id == piece.owner_id:
                continue
            if self.can_capture(piece, occ):
                legal.append((nr, nc))
        return legal

    def has_any_legal_move(self, owner_id: int) -> bool:
        for p in self.pieces:
            if p.owner_id != owner_id:
                continue
            # For a fresh check at start of a turn, ignore the moved set
            saved = self.moved_piece_ids_this_turn
            self.moved_piece_ids_this_turn = set()
            has = len(self.get_legal_moves_for(p)) > 0
            self.moved_piece_ids_this_turn = saved
            if has:
                return True
        return False

    def _maybe_end_turn(self) -> None:
        if self.winner is not None:
            return
        # If current player has no remaining movable pieces this turn, end turn
        remaining_can_move = False
        for p in self.pieces:
            if p.owner_id != self.current_player:
                continue
            if p.piece_id in self.moved_piece_ids_this_turn:
                continue
            if len(self.get_legal_moves_for(p)) > 0:
                remaining_can_move = True
                break
        if not remaining_can_move:
            self.current_player = PLAYER_TWO if self.current_player == PLAYER_ONE else PLAYER_ONE
            self.moved_piece_ids_this_turn.clear()
            # Trap check at start of opponent's turn
            if not self.has_any_legal_move(self.current_player):
                self.winner = PLAYER_TWO if self.current_player == PLAYER_ONE else PLAYER_ONE

    def apply_move(self, piece: Piece, target_row: int, target_col: int) -> None:
        if self.winner is not None:
            return
        # Must be current player's piece and not moved already
        if piece.owner_id != self.current_player:
            return
        if piece.piece_id in self.moved_piece_ids_this_turn:
            return
        legal = self.get_legal_moves_for(piece)
        if (target_row, target_col) not in legal:
            return

        # Capture if enemy present
        target_piece = self.piece_at(target_row, target_col)
        if target_piece is not None and target_piece.owner_id != piece.owner_id:
            if not self.can_capture(piece, target_piece):
                return
            self.pieces.remove(target_piece)
            self.captured_by_player[piece.owner_id] += 1
            self.board.pop((target_piece.row, target_piece.col), None)

        # Move
        self.board.pop((piece.row, piece.col), None)
        piece.row = target_row
        piece.col = target_col
        # Triangle orientation flip at edges
        if piece.piece_type == PIECE_TRIANGLE:
            if piece.row == 0:
                piece.forward_dir = +1
            elif piece.row == BOARD_ROWS - 1:
                piece.forward_dir = -1
        self.board[(piece.row, piece.col)] = piece

        # Mark moved
        self.moved_piece_ids_this_turn.add(piece.piece_id)

        # Capture win condition
        if self.captured_by_player[piece.owner_id] >= 2:
            self.winner = piece.owner_id
            return

        # Maybe end turn automatically
        self._maybe_end_turn()


class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = GameState()
        self.state.setup_random()

        self.margin = 20
        self.info_h = 120
        self.cell_size = 60
        self.grid_w = 3
        self.board_origin_x = 0
        self.board_origin_y = 0

        self.selected: Optional[Piece] = None
        self.legal_moves: List[Tuple[int, int]] = []

        self.status_label = Label(text="", color=COLOR_TEXT, size_hint=(None, None))
        self.add_widget(self.status_label)

        self.bind(size=self.on_resize, pos=self.on_resize)
        Clock.schedule_once(lambda dt: self.refresh(), 0)

    # --- Layout helpers ---
    def compute_layout(self) -> None:
        w, h = self.width, self.height
        min_dim = min(w, h)
        self.margin = max(10, int(min_dim * 0.04))
        self.info_h = max(90, int(min_dim * 0.18))
        avail_w = max(1, int(w) - 2 * self.margin)
        avail_h = max(1, int(h) - 2 * self.margin - self.info_h)
        self.cell_size = max(48, min(avail_w // BOARD_COLS, avail_h // BOARD_ROWS))
        self.grid_w = max(2, self.cell_size // 20)
        board_w = self.cell_size * BOARD_COLS
        board_h = self.cell_size * BOARD_ROWS
        self.board_origin_x = (w - board_w) // 2
        self.board_origin_y = self.margin + self.info_h

    def on_resize(self, *args):
        self.refresh()

    # --- Board mapping ---
    def cell_rect(self, row: int, col: int) -> Tuple[float, float, float, float]:
        # Row 0 is top, Kivy y=0 bottom
        x = self.board_origin_x + col * self.cell_size
        y = self.board_origin_y + (BOARD_ROWS - 1 - row) * self.cell_size
        return x, y, self.cell_size, self.cell_size

    def point_to_cell(self, px: float, py: float) -> Optional[Tuple[int, int]]:
        board_w = self.cell_size * BOARD_COLS
        board_h = self.cell_size * BOARD_ROWS
        if not (self.board_origin_x <= px < self.board_origin_x + board_w and self.board_origin_y <= py < self.board_origin_y + board_h):
            return None
        col = int((px - self.board_origin_x) // self.cell_size)
        row_from_bottom = int((py - self.board_origin_y) // self.cell_size)
        row = BOARD_ROWS - 1 - row_from_bottom
        if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
            return (row, col)
        return None

    # --- Drawing ---
    def refresh(self) -> None:
        self.compute_layout()
        self.canvas.clear()
        with self.canvas:
            # Background
            if self.state.winner is None:
                Color(*COLOR_BG)
            else:
                win_color = COLOR_P1 if self.state.winner == PLAYER_ONE else COLOR_P2
                Color(*win_color)
            Rectangle(pos=self.pos, size=self.size)

            # Grid only if game not over
            if self.state.winner is None:
                Color(*COLOR_GRID)
                for r in range(BOARD_ROWS + 1):
                    y = self.board_origin_y + r * self.cell_size
                    Line(points=[self.board_origin_x, y, self.board_origin_x + self.cell_size * BOARD_COLS, y], width=self.grid_w)
                for c in range(BOARD_COLS + 1):
                    x = self.board_origin_x + c * self.cell_size
                    Line(points=[x, self.board_origin_y, x, self.board_origin_y + self.cell_size * BOARD_ROWS], width=self.grid_w)

                # Selection and legal moves
                if self.selected is not None and len(self.legal_moves) > 0:
                    Color(*COLOR_HL)
                    sx, sy, sw, sh = self.cell_rect(self.selected.row, self.selected.col)
                    Line(rectangle=(sx + 4, sy + 4, sw - 8, sh - 8), width=3)
                    Color(*COLOR_MOVE)
                    for (mr, mc) in self.legal_moves:
                        x, y, w, h = self.cell_rect(mr, mc)
                        Line(rectangle=(x + 6, y + 6, w - 12, h - 12), width=3)

                # Pieces
                for owner in (PLAYER_TWO, PLAYER_ONE):
                    for p in self.state.pieces:
                        if p.owner_id != owner:
                            continue
                        # Piece base color
                        color = COLOR_P1 if p.owner_id == PLAYER_ONE else COLOR_P2
                        dark = COLOR_P1_DARK if p.owner_id == PLAYER_ONE else COLOR_P2_DARK
                        x, y, w, h = self.cell_rect(p.row, p.col)
                        cx = x + w / 2
                        cy = y + h / 2

                        # Draw shapes
                        if p.piece_type == PIECE_CIRCLE:
                            Color(*color)
                            Ellipse(pos=(cx - w/3, cy - h/3), size=(w*2/3, h*2/3))
                            Color(*dark)
                            Line(circle=(cx, cy, min(w, h) / 3), width=2)
                        elif p.piece_type == PIECE_SQUARE:
                            m = w / 6
                            Color(*color)
                            Rectangle(pos=(x + m, y + m), size=(w - 2*m, h - 2*m))
                            Color(*dark)
                            Line(rectangle=(x + m, y + m, w - 2*m, h - 2*m), width=2)
                        elif p.piece_type == PIECE_TRIANGLE:
                            m2 = w / 7
                            if p.forward_dir == +1:
                                pt1 = (cx, y + h - m2)
                                pt2 = (x + m2, y + m2)
                                pt3 = (x + w - m2, y + m2)
                            else:
                                pt1 = (cx, y + m2)
                                pt2 = (x + m2, y + h - m2)
                                pt3 = (x + w - m2, y + h - m2)
                            Color(*color)
                            Triangle(points=[pt1[0], pt1[1], pt2[0], pt2[1], pt3[0], pt3[1]])
                            Color(*dark)
                            Line(points=[pt1[0], pt1[1], pt2[0], pt2[1], pt3[0], pt3[1], pt1[0], pt1[1]], width=2)

        # Update status text
        turn_text = "Победа! Игрок {}".format(1 if self.state.winner == PLAYER_ONE else 2) if self.state.winner else "Ход: Игрок {}".format(1 if self.state.current_player == PLAYER_ONE else 2)
        self.status_label.text = turn_text + "\n" + "Съедено — Игрок 1: {} | Игрок 2: {} (до 2)".format(
            self.state.captured_by_player[PLAYER_ONE], self.state.captured_by_player[PLAYER_TWO]
        ) if self.state.winner is None else turn_text
        self.status_label.pos = (self.margin, self.board_origin_y - 10)
        self.status_label.size = (self.width, self.info_h)

    # --- Input handling ---
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        # If game over, ignore touches (use Reset button)
        if self.state.winner is not None:
            return True

        cell = self.point_to_cell(*touch.pos)
        if cell is None:
            # Outside board: clear selection
            self.selected = None
            self.legal_moves = []
            self.refresh()
            return True

        row, col = cell
        clicked = self.state.piece_at(row, col)

        if self.selected is not None:
            # If clicked a legal move, apply
            if (row, col) in self.legal_moves:
                self.state.apply_move(self.selected, row, col)
                self.selected = None
                self.legal_moves = []
                self.refresh()
                return True
            # Else if clicked own piece that can still move this turn, reselect
            if clicked is not None and clicked.owner_id == self.state.current_player and clicked.piece_id not in self.state.moved_piece_ids_this_turn:
                self.selected = clicked
                self.legal_moves = self.state.get_legal_moves_for(clicked)
                self.refresh()
                return True
            # Otherwise clear selection
            self.selected = None
            self.legal_moves = []
            self.refresh()
            return True
        else:
            # No selection yet; select if own piece that hasn't moved this turn
            if clicked is not None and clicked.owner_id == self.state.current_player and clicked.piece_id not in self.state.moved_piece_ids_this_turn:
                self.selected = clicked
                self.legal_moves = self.state.get_legal_moves_for(clicked)
                self.refresh()
                return True
            else:
                self.selected = None
                self.legal_moves = []
                self.refresh()
                return True


class GameRoot(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = GameWidget(size_hint=(1, 1))
        self.add_widget(self.game)

        # Reset and Exit buttons
        self.btn_reset = Button(text="Сброс", size_hint=(None, None), size=(160, 56))
        self.btn_exit = Button(text="Выход", size_hint=(None, None), size=(160, 56))
        self.add_widget(self.btn_reset)
        self.add_widget(self.btn_exit)

        self.btn_reset.bind(on_release=self.on_reset)
        self.btn_exit.bind(on_release=self.on_exit)

        self.bind(size=self.on_resize, pos=self.on_resize)
        Clock.schedule_once(lambda dt: self.on_resize(), 0)

    def on_resize(self, *args):
        # Place buttons at bottom center
        margin = max(10, int(min(self.width, self.height) * 0.04))
        gap = max(8, int(min(self.width, self.height) * 0.02))
        y = margin
        total_w = self.btn_reset.width + gap + self.btn_exit.width
        x = (self.width - total_w) / 2
        self.btn_reset.pos = (x, y)
        self.btn_exit.pos = (x + self.btn_reset.width + gap, y)

    def on_reset(self, *args):
        self.game.state.setup_random()
        # Trap check at game start for first player
        if not self.game.state.has_any_legal_move(self.game.state.current_player):
            self.game.state.winner = PLAYER_TWO if self.game.state.current_player == PLAYER_ONE else PLAYER_ONE
        self.game.selected = None
        self.game.legal_moves = []
        self.game.refresh()

    def on_exit(self, *args):
        App.get_running_app().stop()


class KivyDuelApp(App):
    def build(self):
        self.title = "4x4 Duel (Kivy)"
        return GameRoot()


if __name__ == "__main__":
    KivyDuelApp().run()