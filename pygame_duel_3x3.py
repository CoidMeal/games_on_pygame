import sys
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

import pygame


# --- Constants ---
BOARD_ROWS = 3
BOARD_COLS = 3
CELL_SIZE = 160
GRID_LINE_WIDTH = 4
MARGIN = 32  # outer margin around the board
INFO_PANEL_HEIGHT = 120

WINDOW_WIDTH = MARGIN * 2 + CELL_SIZE * BOARD_COLS
WINDOW_HEIGHT = MARGIN * 2 + CELL_SIZE * BOARD_ROWS + INFO_PANEL_HEIGHT

FPS = 60

# Colors
COLOR_BG = (28, 33, 38)
COLOR_GRID = (200, 200, 200)
COLOR_HL = (255, 215, 0)
COLOR_MOVE = (80, 170, 255)
COLOR_TEXT = (235, 235, 235)
COLOR_SUBTEXT = (180, 180, 180)

COLOR_P1 = (64, 160, 255)   # Player 1 color (blue)
COLOR_P2 = (255, 100, 100)   # Player 2 color (red)
COLOR_P1_DARK = (40, 110, 180)
COLOR_P2_DARK = (180, 60, 60)

# Piece types
PIECE_CIRCLE = "circle"
PIECE_SQUARE = "square"
PIECE_TRIANGLE = "triangle"

# Player identifiers
PLAYER_ONE = 1
PLAYER_TWO = 2


@dataclass
class Piece:
    owner_id: int
    piece_type: str
    row: int
    col: int
    # For triangles: +1 means facing down (towards larger row index), -1 means facing up
    forward_dir: int = +1

    def copy(self) -> "Piece":
        return Piece(
            owner_id=self.owner_id,
            piece_type=self.piece_type,
            row=self.row,
            col=self.col,
            forward_dir=self.forward_dir,
        )


class GameState:
    def __init__(self) -> None:
        self.pieces: List[Piece] = []
        self.board: Dict[Tuple[int, int], Piece] = {}
        self.current_player: int = PLAYER_ONE
        self.captured_by_player: Dict[int, int] = {PLAYER_ONE: 0, PLAYER_TWO: 0}
        self.winner: Optional[int] = None

    def setup_random(self) -> None:
        self.pieces.clear()
        self.board.clear()
        self.current_player = PLAYER_ONE
        self.captured_by_player = {PLAYER_ONE: 0, PLAYER_TWO: 0}
        self.winner = None

        # All cells on the 3x3 board
        cells = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)]
        random.shuffle(cells)

        # Create three pieces per player in random positions
        placements = cells[:6]

        # Player 1 forward: down (+1)
        self.pieces.append(Piece(PLAYER_ONE, PIECE_CIRCLE, placements[0][0], placements[0][1], +1))
        self.pieces.append(Piece(PLAYER_ONE, PIECE_SQUARE, placements[1][0], placements[1][1], +1))
        self.pieces.append(Piece(PLAYER_ONE, PIECE_TRIANGLE, placements[2][0], placements[2][1], +1))
        # Player 2 forward: up (-1)
        self.pieces.append(Piece(PLAYER_TWO, PIECE_CIRCLE, placements[3][0], placements[3][1], -1))
        self.pieces.append(Piece(PLAYER_TWO, PIECE_SQUARE, placements[4][0], placements[4][1], -1))
        self.pieces.append(Piece(PLAYER_TWO, PIECE_TRIANGLE, placements[5][0], placements[5][1], -1))

        self.rebuild_board_index()

    def rebuild_board_index(self) -> None:
        self.board.clear()
        for piece in self.pieces:
            self.board[(piece.row, piece.col)] = piece

    def piece_at(self, row: int, col: int) -> Optional[Piece]:
        return self.board.get((row, col))

    def is_inside(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS

    def is_occupied_by_owner(self, row: int, col: int, owner_id: int) -> bool:
        piece = self.piece_at(row, col)
        return piece is not None and piece.owner_id == owner_id

    def get_legal_moves_for(self, piece: Piece) -> List[Tuple[int, int]]:
        directions: List[Tuple[int, int]] = []

        if piece.piece_type == PIECE_CIRCLE:
            # Diagonals only, 1 step
            directions = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        elif piece.piece_type == PIECE_SQUARE:
            # Orthogonal only, 1 step
            directions = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
        elif piece.piece_type == PIECE_TRIANGLE:
            # Forward/back one step, plus backward diagonals relative to forward
            f = piece.forward_dir
            directions = [
                (f, 0),           # forward
                (-f, 0),          # backward
                (-f, -1),         # backward-left (relative to forward)
                (-f, +1),         # backward-right (relative to forward)
            ]
        else:
            directions = []

        legal_moves: List[Tuple[int, int]] = []
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            if not self.is_inside(nr, nc):
                continue
            if self.is_occupied_by_owner(nr, nc, piece.owner_id):
                continue
            legal_moves.append((nr, nc))

        return legal_moves

    def apply_move(self, piece: Piece, target_row: int, target_col: int) -> None:
        if self.winner is not None:
            return

        # Capture if enemy present
        target_piece = self.piece_at(target_row, target_col)
        if target_piece is not None and target_piece.owner_id != piece.owner_id:
            self.pieces.remove(target_piece)
            self.captured_by_player[piece.owner_id] += 1

        # Move the piece
        # Remove old index
        if (piece.row, piece.col) in self.board:
            self.board.pop((piece.row, piece.col), None)

        piece.row = target_row
        piece.col = target_col

        # Triangle orientation update at top/bottom edges
        if piece.piece_type == PIECE_TRIANGLE:
            if piece.row == 0:
                piece.forward_dir = +1
            elif piece.row == BOARD_ROWS - 1:
                piece.forward_dir = -1

        # Re-index new location
        self.board[(piece.row, piece.col)] = piece

        # Check win condition: capture two enemy pieces
        if self.captured_by_player[piece.owner_id] >= 2:
            self.winner = piece.owner_id

        # Switch turns if no winner yet
        if self.winner is None:
            self.current_player = PLAYER_TWO if self.current_player == PLAYER_ONE else PLAYER_ONE


# --- Rendering helpers ---

def board_to_pixel(row: int, col: int) -> Tuple[int, int, int, int]:
    x = MARGIN + col * CELL_SIZE
    y = MARGIN + row * CELL_SIZE
    return x, y, CELL_SIZE, CELL_SIZE


def draw_grid(surface: pygame.Surface) -> None:
    for r in range(BOARD_ROWS + 1):
        y = MARGIN + r * CELL_SIZE
        pygame.draw.line(surface, COLOR_GRID, (MARGIN, y), (MARGIN + CELL_SIZE * BOARD_COLS, y), GRID_LINE_WIDTH)
    for c in range(BOARD_COLS + 1):
        x = MARGIN + c * CELL_SIZE
        pygame.draw.line(surface, COLOR_GRID, (x, MARGIN), (x, MARGIN + CELL_SIZE * BOARD_ROWS), GRID_LINE_WIDTH)


def draw_piece(surface: pygame.Surface, piece: Piece) -> None:
    x, y, w, h = board_to_pixel(piece.row, piece.col)
    cx = x + w // 2
    cy = y + h // 2

    color = COLOR_P1 if piece.owner_id == PLAYER_ONE else COLOR_P2
    color_dark = COLOR_P1_DARK if piece.owner_id == PLAYER_ONE else COLOR_P2_DARK

    if piece.piece_type == PIECE_CIRCLE:
        radius = min(w, h) // 3
        pygame.draw.circle(surface, color, (cx, cy), radius)
        pygame.draw.circle(surface, color_dark, (cx, cy), radius, 3)

    elif piece.piece_type == PIECE_SQUARE:
        margin = w // 6
        rect = pygame.Rect(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, color_dark, rect, 3)

    elif piece.piece_type == PIECE_TRIANGLE:
        # Triangle pointing in forward_dir
        margin = w // 7
        if piece.forward_dir == +1:
            # Pointing down
            p1 = (cx, y + h - margin)  # tip bottom
            p2 = (x + margin, y + margin)
            p3 = (x + w - margin, y + margin)
        else:
            # Pointing up
            p1 = (cx, y + margin)  # tip top
            p2 = (x + margin, y + h - margin)
            p3 = (x + w - margin, y + h - margin)
        pygame.draw.polygon(surface, color, [p1, p2, p3])
        pygame.draw.polygon(surface, color_dark, [p1, p2, p3], 3)


def draw_highlights(surface: pygame.Surface, moves: List[Tuple[int, int]]) -> None:
    for (r, c) in moves:
        x, y, w, h = board_to_pixel(r, c)
        rect = pygame.Rect(x + 6, y + 6, w - 12, h - 12)
        pygame.draw.rect(surface, COLOR_MOVE, rect, 4, border_radius=10)


def draw_selection(surface: pygame.Surface, piece: Piece) -> None:
    x, y, w, h = board_to_pixel(piece.row, piece.col)
    rect = pygame.Rect(x + 4, y + 4, w - 8, h - 8)
    pygame.draw.rect(surface, COLOR_HL, rect, 5, border_radius=10)


# --- Input helpers ---

def pixel_to_board(mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    x, y = mouse_pos
    board_left = MARGIN
    board_top = MARGIN
    if x < board_left or y < board_top:
        return None
    x_rel = x - board_left
    y_rel = y - board_top
    col = x_rel // CELL_SIZE
    row = y_rel // CELL_SIZE
    if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
        return int(row), int(col)
    return None


def main() -> None:
    pygame.init()
    pygame.display.set_caption("3x3 Duel: Triangle, Square, Circle")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 28)
    small_font = pygame.font.SysFont("arial", 22)

    state = GameState()
    state.setup_random()

    selected: Optional[Piece] = None
    legal_moves: List[Tuple[int, int]] = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state.setup_random()
                    selected = None
                    legal_moves = []
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                board_cell = pixel_to_board(event.pos)
                if board_cell is None:
                    # Clicked outside board; clear selection
                    selected = None
                    legal_moves = []
                else:
                    row, col = board_cell
                    clicked_piece = state.piece_at(row, col)

                    if state.winner is not None:
                        # Ignore clicks when game over except R to restart
                        pass
                    else:
                        if selected is not None:
                            # If clicked a legal move, perform it
                            if (row, col) in legal_moves:
                                state.apply_move(selected, row, col)
                                selected = None
                                legal_moves = []
                            else:
                                # If clicked own piece, change selection
                                if clicked_piece is not None and clicked_piece.owner_id == state.current_player:
                                    selected = clicked_piece
                                    legal_moves = state.get_legal_moves_for(clicked_piece)
                                else:
                                    selected = None
                                    legal_moves = []
                        else:
                            # No selection yet; select if it's current player's piece
                            if clicked_piece is not None and clicked_piece.owner_id == state.current_player:
                                selected = clicked_piece
                                legal_moves = state.get_legal_moves_for(clicked_piece)
                            else:
                                selected = None
                                legal_moves = []

        # --- Draw ---
        screen.fill(COLOR_BG)

        # Board and pieces
        draw_grid(screen)

        # Selection and legal moves first so they appear under the pieces outline but above grid
        if selected is not None:
            draw_selection(screen, selected)
            draw_highlights(screen, legal_moves)

        # Draw pieces
        # Ensure stable draw order: Player 2 then Player 1 so selection highlight remains visible
        for owner in (PLAYER_TWO, PLAYER_ONE):
            for piece in state.pieces:
                if piece.owner_id == owner:
                    draw_piece(screen, piece)

        # Info panel
        panel_top = MARGIN + CELL_SIZE * BOARD_ROWS + 12

        if state.winner is None:
            turn_text = f"Ход: Игрок {1 if state.current_player == PLAYER_ONE else 2}"
        else:
            turn_text = f"Победа! Игрок {1 if state.winner == PLAYER_ONE else 2}"
        turn_surf = font.render(turn_text, True, COLOR_TEXT)
        screen.blit(turn_surf, (MARGIN, panel_top))

        cap_text = (
            f"Съедено — Игрок 1: {state.captured_by_player[PLAYER_ONE]}  |  "
            f"Игрок 2: {state.captured_by_player[PLAYER_TWO]}  (до 2)"
        )
        cap_surf = small_font.render(cap_text, True, COLOR_SUBTEXT)
        screen.blit(cap_surf, (MARGIN, panel_top + 40))

        hint_text = "ЛКМ: выбрать/ходить  •  R: перезапуск  •  Esc: выход"
        hint_surf = small_font.render(hint_text, True, COLOR_SUBTEXT)
        screen.blit(hint_surf, (MARGIN, panel_top + 70))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()