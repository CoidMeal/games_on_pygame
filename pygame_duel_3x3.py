import sys
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

import pygame


# --- Constants ---
BOARD_ROWS = 4
BOARD_COLS = 4
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


@dataclass
class Layout:
    width: int
    height: int
    margin: int
    info_panel_height: int
    cell_size: int
    grid_line_width: int


def compute_layout(win_w: int, win_h: int) -> Layout:
    # Scale UI for mobile screens
    min_dim = min(win_w, win_h)
    margin = max(10, int(min_dim * 0.04))
    info_panel_height = max(90, int(min_dim * 0.18))

    available_w = max(1, win_w - 2 * margin)
    available_h = max(1, win_h - 2 * margin - info_panel_height)
    cell_size = max(48, min(available_w // BOARD_COLS, available_h // BOARD_ROWS))
    grid_line_width = max(2, cell_size // 20)

    return Layout(
        width=win_w,
        height=win_h,
        margin=margin,
        info_panel_height=info_panel_height,
        cell_size=cell_size,
        grid_line_width=grid_line_width,
    )


def compute_ui_rects(layout: Layout) -> Tuple[pygame.Rect, pygame.Rect, int]:
    # Compute panel top and button rects
    board_pixel_h = layout.margin * 2 + layout.cell_size * BOARD_ROWS
    panel_top = board_pixel_h + 12

    gap = max(8, int(min(layout.width, layout.height) * 0.02))
    btn_h = max(44, int(layout.info_panel_height * 0.45))
    btn_w = (layout.width - 2 * layout.margin - gap)
    btn_w = max(100, btn_w // 2)

    btn_y = panel_top + 8
    restart_rect = pygame.Rect(layout.margin, btn_y, btn_w, btn_h)
    exit_rect = pygame.Rect(layout.margin + btn_w + gap, btn_y, btn_w, btn_h)
    return restart_rect, exit_rect, panel_top


def draw_button(surface: pygame.Surface, rect: pygame.Rect, text: str, font: pygame.font.Font, *, primary: bool = False) -> None:
    base_color = COLOR_MOVE if primary else (90, 90, 90)
    border_color = (255, 255, 255) if primary else (160, 160, 160)
    pygame.draw.rect(surface, base_color, rect, border_radius=12)
    pygame.draw.rect(surface, border_color, rect, width=3, border_radius=12)
    label = font.render(text, True, COLOR_TEXT)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)


class GameState:
    def __init__(self) -> None:
        self.pieces: List[Piece] = []
        self.board: Dict[Tuple[int, int], Piece] = {}
        self.current_player: int = PLAYER_ONE
        self.captured_by_player: Dict[int, int] = {PLAYER_ONE: 0, PLAYER_TWO: 0}
        self.winner: Optional[int] = None

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
        # Fallback: P1 on top row, P2 on bottom row (guaranteed non-adjacent)
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

        placements = self._generate_non_adjacent_start_positions()

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
        directions: List[Tuple[int, int]] = []

        if piece.piece_type == PIECE_CIRCLE:
            # Diagonals only, 1 step
            directions = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        elif piece.piece_type == PIECE_SQUARE:
            # Orthogonal only, 1 step
            directions = [(-1, 0), (+1, 0), (0, -1), (0, +1)]
        elif piece.piece_type == PIECE_TRIANGLE:
            # New rules: forward diagonals (left/right) + straight back, 1 step
            f = piece.forward_dir
            directions = [
                (f, -1),          # forward-left
                (f, +1),          # forward-right
                (-f, 0),          # straight back
            ]
        else:
            directions = []

        legal_moves: List[Tuple[int, int]] = []
        for dr, dc in directions:
            nr, nc = piece.row + dr, piece.col + dc
            if not self.is_inside(nr, nc):
                continue
            occupant = self.piece_at(nr, nc)
            if occupant is None:
                legal_moves.append((nr, nc))
                continue
            if occupant.owner_id == piece.owner_id:
                continue
            # Enemy occupant: only legal if capture is allowed by RPS rule
            if self.can_capture(piece, occupant):
                legal_moves.append((nr, nc))

        return legal_moves

    def has_any_legal_move(self, owner_id: int) -> bool:
        for p in self.pieces:
            if p.owner_id == owner_id:
                if self.get_legal_moves_for(p):
                    return True
        return False

    def apply_move(self, piece: Piece, target_row: int, target_col: int) -> None:
        if self.winner is not None:
            return

        # Capture if enemy present (only if allowed)
        target_piece = self.piece_at(target_row, target_col)
        if target_piece is not None and target_piece.owner_id != piece.owner_id:
            if not self.can_capture(piece, target_piece):
                return
            self.pieces.remove(target_piece)
            self.captured_by_player[piece.owner_id] += 1

        # Move the piece
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

        # Switch turns and check trap condition if no winner yet
        if self.winner is None:
            self.current_player = PLAYER_TWO if self.current_player == PLAYER_ONE else PLAYER_ONE
            if not self.has_any_legal_move(self.current_player):
                # Current player has no legal moves -> they are trapped and lose
                self.winner = PLAYER_TWO if self.current_player == PLAYER_ONE else PLAYER_ONE


# --- Rendering helpers ---

def board_to_pixel(layout: Layout, row: int, col: int) -> Tuple[int, int, int, int]:
    x = layout.margin + col * layout.cell_size
    y = layout.margin + row * layout.cell_size
    return x, y, layout.cell_size, layout.cell_size


def draw_grid(surface: pygame.Surface, layout: Layout) -> None:
    for r in range(BOARD_ROWS + 1):
        y = layout.margin + r * layout.cell_size
        pygame.draw.line(surface, COLOR_GRID, (layout.margin, y), (layout.margin + layout.cell_size * BOARD_COLS, y), layout.grid_line_width)
    for c in range(BOARD_COLS + 1):
        x = layout.margin + c * layout.cell_size
        pygame.draw.line(surface, COLOR_GRID, (x, layout.margin), (x, layout.margin + layout.cell_size * BOARD_ROWS), layout.grid_line_width)


def draw_piece(surface: pygame.Surface, layout: Layout, piece: Piece) -> None:
    x, y, w, h = board_to_pixel(layout, piece.row, piece.col)
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


def draw_highlights(surface: pygame.Surface, layout: Layout, moves: List[Tuple[int, int]]) -> None:
    for (r, c) in moves:
        x, y, w, h = board_to_pixel(layout, r, c)
        rect = pygame.Rect(x + 6, y + 6, w - 12, h - 12)
        pygame.draw.rect(surface, COLOR_MOVE, rect, 4, border_radius=10)


def draw_selection(surface: pygame.Surface, layout: Layout, piece: Piece) -> None:
    x, y, w, h = board_to_pixel(layout, piece.row, piece.col)
    rect = pygame.Rect(x + 4, y + 4, w - 8, h - 8)
    pygame.draw.rect(surface, COLOR_HL, rect, 5, border_radius=10)


# --- Input helpers ---

def pixel_to_board(layout: Layout, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    x, y = mouse_pos
    board_left = layout.margin
    board_top = layout.margin
    if x < board_left or y < board_top:
        return None
    x_rel = x - board_left
    y_rel = y - board_top
    col = x_rel // layout.cell_size
    row = y_rel // layout.cell_size
    if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
        return int(row), int(col)
    return None


def main() -> None:
    pygame.init()
    pygame.display.set_caption("3x3 Duel (Mobile)")

    # Prefer fullscreen for mobile; fallback to windowed if needed
    screen: pygame.Surface
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except Exception:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    clock = pygame.time.Clock()

    state = GameState()
    state.setup_random()

    selected: Optional[Piece] = None
    legal_moves: List[Tuple[int, int]] = []

    def handle_pointer_down(px: int, py: int, layout: Layout, restart_rect: pygame.Rect, exit_rect: pygame.Rect) -> Tuple[Optional[Piece], List[Tuple[int, int]], bool]:
        nonlocal state
        nonlocal selected
        nonlocal legal_moves
        # Buttons first
        if restart_rect.collidepoint(px, py):
            state.setup_random()
            selected = None
            legal_moves = []
            return selected, legal_moves, False
        if exit_rect.collidepoint(px, py):
            return selected, legal_moves, True

        # Board interaction
        board_cell = pixel_to_board(layout, (px, py))
        if board_cell is None:
            selected = None
            legal_moves = []
            return selected, legal_moves, False

        row, col = board_cell
        clicked_piece = state.piece_at(row, col)

        if state.winner is not None:
            return selected, legal_moves, False

        if selected is not None:
            if (row, col) in legal_moves:
                state.apply_move(selected, row, col)
                selected = None
                legal_moves = []
            else:
                if clicked_piece is not None and clicked_piece.owner_id == state.current_player:
                    selected = clicked_piece
                    legal_moves = state.get_legal_moves_for(clicked_piece)
                else:
                    selected = None
                    legal_moves = []
        else:
            if clicked_piece is not None and clicked_piece.owner_id == state.current_player:
                selected = clicked_piece
                legal_moves = state.get_legal_moves_for(clicked_piece)
            else:
                selected = None
                legal_moves = []
        return selected, legal_moves, False

    running = True
    while running:
        win_w, win_h = screen.get_size()
        layout = compute_layout(win_w, win_h)
        restart_rect, exit_rect, panel_top = compute_ui_rects(layout)

        # Fonts sized to panel
        font = pygame.font.Font(None, max(22, int(layout.info_panel_height * 0.42)))
        small_font = pygame.font.Font(None, max(18, int(layout.info_panel_height * 0.28)))

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
                sx, sy = event.pos
                _, _, should_quit = handle_pointer_down(sx, sy, layout, restart_rect, exit_rect)
                if should_quit:
                    running = False
            elif event.type == pygame.FINGERDOWN:
                # Convert normalized touch coords to pixels
                sx = int(event.x * win_w)
                sy = int(event.y * win_h)
                _, _, should_quit = handle_pointer_down(sx, sy, layout, restart_rect, exit_rect)
                if should_quit:
                    running = False

        # --- Draw ---
        if state.winner is None:
            screen.fill(COLOR_BG)
        else:
            winner_color = COLOR_P1 if state.winner == PLAYER_ONE else COLOR_P2
            screen.fill(winner_color)

        # Board and pieces
        if state.winner is None:
            draw_grid(screen, layout)

        # Selection and legal moves
        if state.winner is None and selected is not None:
            draw_selection(screen, layout, selected)
            draw_highlights(screen, layout, legal_moves)

        # Draw pieces (order for highlight visibility)
        if state.winner is None:
            for owner in (PLAYER_TWO, PLAYER_ONE):
                for piece in state.pieces:
                    if piece.owner_id == owner:
                        draw_piece(screen, layout, piece)

        # Info panel
        if state.winner is None:
            turn_text = f"Ход: Игрок {1 if state.current_player == PLAYER_ONE else 2}"
        else:
            turn_text = f"Победа! Игрок {1 if state.winner == PLAYER_ONE else 2}"
        turn_surf = font.render(turn_text, True, COLOR_TEXT)
        screen.blit(turn_surf, (layout.margin, panel_top))

        cap_text = (
            f"Съедено — Игрок 1: {state.captured_by_player[PLAYER_ONE]}  |  "
            f"Игрок 2: {state.captured_by_player[PLAYER_TWO]}  (до 2)"
        )
        cap_surf = small_font.render(cap_text, True, COLOR_SUBTEXT)
        if state.winner is None:
            screen.blit(cap_surf, (layout.margin, panel_top + int(layout.info_panel_height * 0.28)))

        # Buttons
        draw_button(screen, restart_rect, "Сброс", small_font, primary=True)
        draw_button(screen, exit_rect, "Выход", small_font, primary=False)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()