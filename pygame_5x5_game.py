import sys
import pygame
from typing import Optional


# Game constants
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500
BOARD_ROWS = 5
BOARD_COLS = 5
CELL_SIZE = WINDOW_WIDTH // BOARD_COLS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT = (220, 220, 220)
DARK = (180, 180, 180)
RED = (230, 60, 60)
BLUE = (60, 90, 230)
YELLOW = (240, 220, 70)
GREEN = (70, 200, 120)

# Types
PIECE_TRIANGLE = "triangle"
PIECE_SQUARE = "square"
PIECE_CIRCLE = "circle"


def create_initial_pieces():
    pieces = [
        {"row": 4, "col": 0, "type": PIECE_TRIANGLE, "player": 1, "direction": -1},
        {"row": 4, "col": 2, "type": PIECE_SQUARE, "player": 1, "direction": 0},
        {"row": 4, "col": 4, "type": PIECE_CIRCLE, "player": 1, "direction": 0},
        {"row": 0, "col": 0, "type": PIECE_CIRCLE, "player": 2, "direction": 0},
        {"row": 0, "col": 2, "type": PIECE_SQUARE, "player": 2, "direction": 0},
        {"row": 0, "col": 4, "type": PIECE_TRIANGLE, "player": 2, "direction": 1},
    ]
    return pieces


def inside_board(row_index: int, col_index: int) -> bool:
    return 0 <= row_index < BOARD_ROWS and 0 <= col_index < BOARD_COLS


def get_piece_at(pieces, row_index: int, col_index: int):
    for piece in pieces:
        if piece["row"] == row_index and piece["col"] == col_index:
            return piece
    return None


def battle_winner_type(type_a: str, type_b: str):
    # Returns the winning type (string) or None for tie/non-winning interaction
    beats = {
        (PIECE_TRIANGLE, PIECE_CIRCLE): PIECE_TRIANGLE,
        (PIECE_CIRCLE, PIECE_SQUARE): PIECE_CIRCLE,
        (PIECE_SQUARE, PIECE_TRIANGLE): PIECE_SQUARE,
    }
    if type_a == type_b:
        return None
    winner = beats.get((type_a, type_b))
    if winner is not None:
        return winner
    return beats.get((type_b, type_a))


def attacker_beats_defender(attacker_type: str, defender_type: str) -> bool:
    winner = battle_winner_type(attacker_type, defender_type)
    return winner == attacker_type


def legal_moves_for_piece(pieces, piece):
    # Returns (moves, captures), where each is a list of (row, col)
    row_index = piece["row"]
    col_index = piece["col"]
    piece_type = piece["type"]

    candidate_deltas = []
    if piece_type == PIECE_SQUARE:
        candidate_deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    elif piece_type == PIECE_CIRCLE:
        candidate_deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    elif piece_type == PIECE_TRIANGLE:
        direction = piece.get("direction", -1)
        # Forward, forward-left, forward-right, and side moves
        candidate_deltas = [
            (direction, 0),
            (direction, -1),
            (direction, 1),
            (0, -1),
            (0, 1),
        ]

    empty_moves = []
    capture_moves = []

    for delta_row, delta_col in candidate_deltas:
        next_row = row_index + delta_row
        next_col = col_index + delta_col
        if not inside_board(next_row, next_col):
            continue
        occupant = get_piece_at(pieces, next_row, next_col)
        if occupant is None:
            empty_moves.append((next_row, next_col))
        else:
            if occupant["player"] != piece["player"] and attacker_beats_defender(piece_type, occupant["type"]):
                capture_moves.append((next_row, next_col))

    return empty_moves, capture_moves


def move_piece(pieces, piece, dest_row: int, dest_col: int):
    # Perform move or capture. Returns True if a move happened.
    occupant = get_piece_at(pieces, dest_row, dest_col)
    if occupant is not None:
        if occupant["player"] == piece["player"]:
            return False
        if not attacker_beats_defender(piece["type"], occupant["type"]):
            return False
        pieces.remove(occupant)

    piece["row"] = dest_row
    piece["col"] = dest_col

    # Triangle bounce logic when reaching the far edge after moving
    if piece["type"] == PIECE_TRIANGLE:
        if piece.get("direction", -1) == -1 and piece["row"] == 0:
            piece["direction"] = 1
        elif piece.get("direction", 1) == 1 and piece["row"] == BOARD_ROWS - 1:
            piece["direction"] = -1

    return True


def draw_board(surface: pygame.Surface):
    surface.fill(WHITE)
    for row_index in range(BOARD_ROWS):
        for col_index in range(BOARD_COLS):
            rect = pygame.Rect(
                col_index * CELL_SIZE,
                row_index * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE,
            )
            color = LIGHT if (row_index + col_index) % 2 == 0 else DARK
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


def draw_piece(surface: pygame.Surface, piece):
    center_x = piece["col"] * CELL_SIZE + CELL_SIZE // 2
    center_y = piece["row"] * CELL_SIZE + CELL_SIZE // 2
    radius = CELL_SIZE // 3
    color = RED if piece["player"] == 1 else BLUE

    if piece["type"] == PIECE_CIRCLE:
        pygame.draw.circle(surface, color, (center_x, center_y), radius)

    elif piece["type"] == PIECE_SQUARE:
        rect = pygame.Rect(0, 0, CELL_SIZE // 2, CELL_SIZE // 2)
        rect.center = (center_x, center_y)
        pygame.draw.rect(surface, color, rect)

    elif piece["type"] == PIECE_TRIANGLE:
        direction = piece.get("direction", -1)
        if direction == -1:
            # pointing up
            points = [
                (center_x, center_y - radius),
                (center_x - radius, center_y + radius),
                (center_x + radius, center_y + radius),
            ]
        else:
            # pointing down
            points = [
                (center_x, center_y + radius),
                (center_x - radius, center_y - radius),
                (center_x + radius, center_y - radius),
            ]
        pygame.draw.polygon(surface, color, points)


def draw_highlight(surface: pygame.Surface, row_index: int, col_index: int, color, width: int = 3):
    rect = pygame.Rect(
        col_index * CELL_SIZE,
        row_index * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE,
    )
    pygame.draw.rect(surface, color, rect, width)


def draw_move_dots(surface: pygame.Surface, cells, color):
    for row_index, col_index in cells:
        center_x = col_index * CELL_SIZE + CELL_SIZE // 2
        center_y = row_index * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, color, (center_x, center_y), max(6, CELL_SIZE // 12))


def draw_status(surface: pygame.Surface, player_turn: int, winner: Optional[int]):
    font = pygame.font.SysFont(None, 28)
    if winner is None:
        text_surface = font.render(f"Ход игрока {player_turn}", True, BLACK)
    else:
        text_surface = font.render(f"Победил игрок {winner}. Нажмите R, чтобы начать заново", True, BLACK)

    surface.blit(text_surface, (8, 8))


def pixel_to_cell(pos):
    x, y = pos
    col_index = x // CELL_SIZE
    row_index = y // CELL_SIZE
    return int(row_index), int(col_index)


def check_winner(pieces) -> Optional[int]:
    p1_alive = any(p["player"] == 1 for p in pieces)
    p2_alive = any(p["player"] == 2 for p in pieces)
    if p1_alive and p2_alive:
        return None
    if p1_alive and not p2_alive:
        return 1
    if p2_alive and not p1_alive:
        return 2
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("5x5 Фигуры")
    clock = pygame.time.Clock()

    pieces = create_initial_pieces()
    player_turn = 1
    selected_piece = None
    cached_empty_moves = []
    cached_capture_moves = []
    winner = None

    def select_piece_at_cell(row_index: int, col_index: int):
        nonlocal selected_piece, cached_empty_moves, cached_capture_moves
        piece = get_piece_at(pieces, row_index, col_index)
        if piece is not None and piece["player"] == player_turn and winner is None:
            selected_piece = piece
            cached_empty_moves, cached_capture_moves = legal_moves_for_piece(pieces, piece)
        else:
            # Keep selection if click is invalid
            pass

    def try_move_selected_to(row_index: int, col_index: int):
        nonlocal selected_piece, player_turn, winner, cached_empty_moves, cached_capture_moves
        if selected_piece is None or winner is not None:
            return

        target_cell = (row_index, col_index)
        valid_cells = set(cached_empty_moves) | set(cached_capture_moves)
        if target_cell not in valid_cells:
            return

        moved = move_piece(pieces, selected_piece, row_index, col_index)
        if moved:
            selected_piece = None
            cached_empty_moves = []
            cached_capture_moves = []
            player_turn = 2 if player_turn == 1 else 1
            winner = check_winner(pieces)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    # Restart game
                    pieces = create_initial_pieces()
                    player_turn = 1
                    selected_piece = None
                    cached_empty_moves = []
                    cached_capture_moves = []
                    winner = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if winner is not None:
                    continue
                mouse_pos = pygame.mouse.get_pos()
                row_index, col_index = pixel_to_cell(mouse_pos)
                if not inside_board(row_index, col_index):
                    continue
                piece_at_click = get_piece_at(pieces, row_index, col_index)
                if selected_piece is None:
                    if piece_at_click is not None and piece_at_click["player"] == player_turn:
                        select_piece_at_cell(row_index, col_index)
                else:
                    if piece_at_click is not None and piece_at_click["player"] == player_turn:
                        select_piece_at_cell(row_index, col_index)
                    else:
                        try_move_selected_to(row_index, col_index)
            elif event.type == pygame.FINGERDOWN:
                if winner is not None:
                    continue
                # Touch input support (Android/SDL): event.x, event.y are normalized [0..1]
                px = int(event.x * WINDOW_WIDTH)
                py = int(event.y * WINDOW_HEIGHT)
                row_index, col_index = pixel_to_cell((px, py))
                if not inside_board(row_index, col_index):
                    continue
                piece_at_click = get_piece_at(pieces, row_index, col_index)
                if selected_piece is None:
                    if piece_at_click is not None and piece_at_click["player"] == player_turn:
                        select_piece_at_cell(row_index, col_index)
                else:
                    if piece_at_click is not None and piece_at_click["player"] == player_turn:
                        select_piece_at_cell(row_index, col_index)
                    else:
                        try_move_selected_to(row_index, col_index)

        draw_board(screen)
        # Highlights
        if selected_piece is not None:
            draw_highlight(screen, selected_piece["row"], selected_piece["col"], YELLOW, 4)
            draw_move_dots(screen, cached_empty_moves, GREEN)
            draw_move_dots(screen, cached_capture_moves, RED)

        # Pieces
        for piece in pieces:
            draw_piece(screen, piece)

        # Status
        draw_status(screen, player_turn, winner)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()