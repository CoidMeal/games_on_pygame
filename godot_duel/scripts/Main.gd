extends Control

# Board settings
const BOARD_ROWS: int = 4
const BOARD_COLS: int = 4

# Colors
const COLOR_BG := Color(0.11, 0.13, 0.15)
const COLOR_GRID := Color(0.78, 0.78, 0.78)
const COLOR_MOVE := Color(0.31, 0.67, 1.0)
const COLOR_HL := Color(1.0, 0.84, 0.0)
const COLOR_P1 := Color(0.25, 0.63, 1.0)
const COLOR_P2 := Color(1.0, 0.39, 0.39)
const COLOR_P1_DARK := Color(0.16, 0.43, 0.71)
const COLOR_P2_DARK := Color(0.71, 0.24, 0.24)

# Piece types
const PT_CIRCLE := "circle"
const PT_SQUARE := "square"
const PT_TRIANGLE := "triangle"

# Players
const P1 := 1
const P2 := 2

class Piece:
	var owner_id: int
	var piece_type: String
	var row: int
	var col: int
	var forward_dir: int
	func _init(_owner_id: int, _piece_type: String, _row: int, _col: int, _forward_dir: int):
		owner_id = _owner_id
		piece_type = _piece_type
		row = _row
		col = _col
		forward_dir = _forward_dir

var pieces: Array = []
var board := {} # Dictionary with Vector2i -> Piece
var current_player: int = P1
var captured_by_player := {P1: 0, P2: 0}
var winner: int = 0

# Layout
var margin: int
var cell_size: int
var info_h: int
var grid_w: int

# Interaction
var selected: Piece = null
var legal_moves: Array[Vector2i] = []

# UI buttons
var restart_rect: Rect2
var exit_rect: Rect2

func _ready() -> void:
	set_process(true)
	_setup_random()

func _compute_layout() -> void:
	var size = get_viewport_rect().size
	var min_dim = min(size.x, size.y)
	margin = max(10, int(min_dim * 0.04))
	info_h = max(90, int(min_dim * 0.18))
	var avail_w = max(1, int(size.x) - 2 * margin)
	var avail_h = max(1, int(size.y) - 2 * margin - info_h)
	cell_size = max(48, min(avail_w / BOARD_COLS, avail_h / BOARD_ROWS))
	grid_w = max(2, cell_size / 20)

	var board_pix_h = margin * 2 + cell_size * BOARD_ROWS
	var panel_top = board_pix_h + 12
	var gap = max(8, int(min(size.x, size.y) * 0.02))
	var btn_h = max(44, int(info_h * 0.45))
	var btn_w = (int(size.x) - 2 * margin - gap) / 2
	restart_rect = Rect2(Vector2(margin, panel_top + 8), Vector2(btn_w, btn_h))
	exit_rect = Rect2(Vector2(margin + btn_w + gap, panel_top + 8), Vector2(btn_w, btn_h))

func _setup_random() -> void:
	pieces.clear()
	board.clear()
	current_player = P1
	captured_by_player = {P1: 0, P2: 0}
	winner = 0

	var placements = _generate_non_adjacent_start_positions()
	# P1 forward down
	pieces.append(Piece.new(P1, PT_CIRCLE, placements[0].x, placements[0].y, +1))
	pieces.append(Piece.new(P1, PT_SQUARE, placements[1].x, placements[1].y, +1))
	pieces.append(Piece.new(P1, PT_TRIANGLE, placements[2].x, placements[2].y, +1))
	# P2 forward up
	pieces.append(Piece.new(P2, PT_CIRCLE, placements[3].x, placements[3].y, -1))
	pieces.append(Piece.new(P2, PT_SQUARE, placements[4].x, placements[4].y, -1))
	pieces.append(Piece.new(P2, PT_TRIANGLE, placements[5].x, placements[5].y, -1))
	_rebuild_board()

func _rebuild_board() -> void:
	board.clear()
	for p in pieces:
		board[Vector2i(p.row, p.col)] = p

func _are_adjacent(a: Vector2i, b: Vector2i) -> bool:
	return max(abs(a.x - b.x), abs(a.y - b.y)) <= 1

func _generate_non_adjacent_start_positions() -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for r in BOARD_ROWS:
		for c in BOARD_COLS:
			cells.append(Vector2i(r, c))
	for _i in 2000:
		cells.shuffle()
		var placements = cells.slice(0, 6)
		var ok = true
		for i in 3:
			for j in 3:
				if _are_adjacent(placements[i], placements[3 + j]):
					ok = false
					break
			if not ok:
				break
		if ok:
			return placements
	# Fallback
	var cols := PackedInt32Array()
	for c in BOARD_COLS:
		cols.append(c)
	cols.shuffle()
	var p1_cols = cols.slice(0, 3)
	cols.shuffle()
	var p2_cols = cols.slice(0, 3)
	var p1: Array[Vector2i] = []
	var p2: Array[Vector2i] = []
	for i in 3:
		p1.append(Vector2i(0, p1_cols[i]))
		p2.append(Vector2i(BOARD_ROWS - 1, p2_cols[i]))
	return p1 + p2

func _piece_at(r: int, c: int) -> Piece:
	return board.get(Vector2i(r, c), null)

func _inside(r: int, c: int) -> bool:
	return r >= 0 and r < BOARD_ROWS and c >= 0 and c < BOARD_COLS

func _can_capture(attacker: Piece, defender: Piece) -> bool:
	if attacker.owner_id == defender.owner_id:
		return false
	if attacker.piece_type == PT_TRIANGLE:
		return defender.piece_type == PT_CIRCLE
	if attacker.piece_type == PT_CIRCLE:
		return defender.piece_type == PT_SQUARE
	if attacker.piece_type == PT_SQUARE:
		return defender.piece_type == PT_TRIANGLE
	return false

func _legal_moves_for(p: Piece) -> Array[Vector2i]:
	var dirs: Array[Vector2i] = []
	if p.piece_type == PT_CIRCLE:
		dirs = [Vector2i(-1,-1), Vector2i(-1,1), Vector2i(1,-1), Vector2i(1,1)]
	elif p.piece_type == PT_SQUARE:
		dirs = [Vector2i(-1,0), Vector2i(1,0), Vector2i(0,-1), Vector2i(0,1)]
	elif p.piece_type == PT_TRIANGLE:
		var f = p.forward_dir
		dirs = [Vector2i(f,-1), Vector2i(f,1), Vector2i(-f,0)]
	var result: Array[Vector2i] = []
	for d in dirs:
		var nr = p.row + d.x
		var nc = p.col + d.y
		if not _inside(nr, nc):
			continue
		var occ: Piece = _piece_at(nr, nc)
		if occ == null:
			result.append(Vector2i(nr, nc))
			continue
		if occ.owner_id == p.owner_id:
			continue
		if _can_capture(p, occ):
			result.append(Vector2i(nr, nc))
	return result

func _has_any_legal_move(owner_id: int) -> bool:
	for p in pieces:
		if p.owner_id == owner_id:
			if _legal_moves_for(p).size() > 0:
				return true
	return false

func _apply_move(p: Piece, tr: int, tc: int) -> void:
	if winner != 0:
		return
	var tgt: Piece = _piece_at(tr, tc)
	if tgt != null and tgt.owner_id != p.owner_id:
		if not _can_capture(p, tgt):
			return
		pieces.erase(tgt)
		captured_by_player[p.owner_id] = int(captured_by_player[p.owner_id]) + 1
		board.erase(Vector2i(tgt.row, tgt.col))
	# move piece
	board.erase(Vector2i(p.row, p.col))
	p.row = tr
	p.col = tc
	if p.piece_type == PT_TRIANGLE:
		if p.row == 0:
			p.forward_dir = +1
		elif p.row == BOARD_ROWS - 1:
			p.forward_dir = -1
	board[Vector2i(p.row, p.col)] = p
	# capture win condition
	if captured_by_player[p.owner_id] >= 2:
		winner = p.owner_id
		return
	# switch and trap check
	current_player = P2 if current_player == P1 else P1
	if not _has_any_legal_move(current_player):
		winner = P2 if current_player == P1 else P1

# Input handling
func _unproject(pos: Vector2) -> Vector2i:
	var rel = pos - Vector2(margin, margin)
	var col = int(rel.x / cell_size)
	var row = int(rel.y / cell_size)
	return Vector2i(row, col)

func _handle_pointer(pos: Vector2) -> void:
	if restart_rect.has_point(pos):
		_setup_random()
		selected = null
		legal_moves.clear()
		return
	if exit_rect.has_point(pos):
		get_tree().quit()
		return
	var rc = _unproject(pos)
	if not _inside(rc.x, rc.y):
		selected = null
		legal_moves.clear()
		return
	var clicked: Piece = _piece_at(rc.x, rc.y)
	if winner != 0:
		return
	if selected != null:
		for m in legal_moves:
			if m == rc:
				_apply_move(selected, rc.x, rc.y)
				selected = null
				legal_moves.clear()
				return
		if clicked != null and clicked.owner_id == current_player:
			selected = clicked
			legal_moves = _legal_moves_for(clicked)
		else:
			selected = null
			legal_moves.clear()
	else:
		if clicked != null and clicked.owner_id == current_player:
			selected = clicked
			legal_moves = _legal_moves_for(clicked)
		else:
			selected = null
			legal_moves.clear()

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_handle_pointer(event.position)
	elif event is InputEventScreenTouch and event.pressed:
		_handle_pointer(event.position)

func _process(_dt: float) -> void:
	_update()

func _update() -> void:
	_compute_layout()
	queue_redraw()

func _draw() -> void:
	var size = get_viewport_rect().size
	# background
	if winner == 0:
		draw_rect(Rect2(Vector2.ZERO, size), COLOR_BG)
	else:
		var win_color = COLOR_P1 if winner == P1 else COLOR_P2
		draw_rect(Rect2(Vector2.ZERO, size), win_color)
	# board
	if winner == 0:
		for r in BOARD_ROWS + 1:
			var y = margin + r * cell_size
			draw_line(Vector2(margin, y), Vector2(margin + cell_size * BOARD_COLS, y), COLOR_GRID, grid_w)
		for c in BOARD_COLS + 1:
			var x = margin + c * cell_size
			draw_line(Vector2(x, margin), Vector2(x, margin + cell_size * BOARD_ROWS), COLOR_GRID, grid_w)
		# selection and moves
		if selected != null:
			var sx = margin + selected.col * cell_size
			var sy = margin + selected.row * cell_size
			draw_rect(Rect2(Vector2(sx + 4, sy + 4), Vector2(cell_size - 8, cell_size - 8)), COLOR_HL, false, 5)
			for m in legal_moves:
				var mx = margin + m.y * cell_size
				var my = margin + m.x * cell_size
				draw_rect(Rect2(Vector2(mx + 6, my + 6), Vector2(cell_size - 12, cell_size - 12)), COLOR_MOVE, false, 4)
		# pieces
		for owner in [P2, P1]:
			for p in pieces:
				if p.owner_id != owner:
					continue
				var x = margin + p.col * cell_size
				var y = margin + p.row * cell_size
				var w = cell_size
				var h = cell_size
				var cx = x + w / 2
				var cy = y + h / 2
				var color = COLOR_P1 if p.owner_id == P1 else COLOR_P2
				var dark = COLOR_P1_DARK if p.owner_id == P1 else COLOR_P2_DARK
				if p.piece_type == PT_CIRCLE:
					draw_circle(Vector2(cx, cy), min(w, h) / 3, color)
					draw_arc(Vector2(cx, cy), min(w, h) / 3, 0, TAU, 64, dark, 3)
				elif p.piece_type == PT_SQUARE:
					var m = w / 6
					draw_rect(Rect2(Vector2(x + m, y + m), Vector2(w - 2 * m, h - 2 * m)), color, true)
					draw_rect(Rect2(Vector2(x + m, y + m), Vector2(w - 2 * m, h - 2 * m)), dark, false, 3)
				elif p.piece_type == PT_TRIANGLE:
					var m2 = w / 7
					var p1: Vector2
					var p2: Vector2
					var p3: Vector2
					if p.forward_dir == +1:
						p1 = Vector2(cx, y + h - m2)
						p2 = Vector2(x + m2, y + m2)
						p3 = Vector2(x + w - m2, y + m2)
					else:
						p1 = Vector2(cx, y + m2)
						p2 = Vector2(x + m2, y + h - m2)
						p3 = Vector2(x + w - m2, y + h - m2)
					draw_colored_polygon(PackedVector2Array([p1, p2, p3]), color)
					draw_polyline(PackedVector2Array([p1, p2, p3, p1]), dark, 3)
	# panel text
	var board_pix_h = margin * 2 + cell_size * BOARD_ROWS
	var panel_top = board_pix_h + 12
	var big_font = get_theme_default_font().duplicate()
	big_font.size = max(22, int(info_h * 0.42))
	var small_font = get_theme_default_font().duplicate()
	small_font.size = max(18, int(info_h * 0.28))
	var turn_text := winner == 0 ? "Ход: Игрок %d" % (1 if current_player == P1 else 2) : "Победа! Игрок %d" % (1 if winner == P1 else 2)
	draw_string(big_font, Vector2(margin, panel_top + big_font.size), turn_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 1.0, Color.WHITE)
	if winner == 0:
		var cap_text := "Съедено — Игрок 1: %d | Игрок 2: %d (до 2)" % [captured_by_player[P1], captured_by_player[P2]]
		draw_string(small_font, Vector2(margin, panel_top + big_font.size + small_font.size + 8), cap_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 1.0, Color(0.75,0.75,0.75))
	# buttons
	_draw_button(restart_rect, "Сброс", true)
	_draw_button(exit_rect, "Выход", false)

func _draw_button(rect: Rect2, text: String, primary: bool) -> void:
	var base = COLOR_MOVE if primary else Color(0.35, 0.35, 0.35)
	var border = Color.WHITE if primary else Color(0.63, 0.63, 0.63)
	draw_rect(rect, base, true, 12)
	draw_rect(rect, border, false, 3, 12)
	var f = get_theme_default_font().duplicate()
	f.size = max(18, int(info_h * 0.28))
	var size = f.get_string_size(text)
	var center = rect.position + rect.size / 2.0
	draw_string(f, center - size / 2.0 + Vector2(0, f.size * 0.35), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 1.0, Color.WHITE)