from __future__ import annotations

import random
from typing import Dict, List, Optional, Set, Tuple

from .engine import BLACK, RED, Game, Move, Piece, Position, opponent


DIFFICULTIES = (
    "初窥门径",
    "小试牛刀",
    "渐通棋理",
    "纵横盘间",
    "弈臻化境",
)

PIECE_VALUES: Dict[str, int] = {
    "general": 10000,
    "rook": 900,
    "cannon": 450,
    "horse": 420,
    "advisor": 220,
    "elephant": 220,
    "pawn": 100,
}

Board = Dict[Position, Piece]
SEARCH_ROOT_LIMIT = 24
SEARCH_NODE_LIMIT = 24


def choose_ai_move(game: Game, color: str, difficulty: str, seed: Optional[int] = None) -> Optional[Move]:
    moves = game.all_legal_moves(color)
    if not moves:
        return None
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"未知 AI 难度：{difficulty}")

    rng = random.Random(seed)
    level = DIFFICULTIES.index(difficulty)
    if level == 0:
        return rng.choice(moves)

    if level == 3:
        return _choose_search_move(game.board, moves, color, depth=2, rng=rng)
    if level == 4:
        return _choose_search_move(game.board, moves, color, depth=3, rng=rng)

    scored = [(score_move(game, move, color, level), rng.random(), move) for move in moves]
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored[0][2]


def score_move(game: Game, move: Move, color: str, level: int) -> int:
    captured = game.piece_at(*move.end)
    moved = game.piece_at(*move.start)
    score = _capture_score(captured)
    if captured and captured.kind == "general":
        return PIECE_VALUES["general"] * 10
    if level >= 2:
        score += _positional_score(move, moved, color)
    if level >= 3:
        score += _check_pressure_score(game, move, color)
    if level >= 4:
        score -= _best_reply_capture(game, move, color)
    return score


def _choose_search_move(board: Board, moves: List[Move], color: str, depth: int, rng: random.Random) -> Move:
    moves = sorted(moves, key=lambda move: _move_order_score(board, move, color), reverse=True)
    if depth >= 3:
        moves = moves[:SEARCH_ROOT_LIMIT]
    scored = []
    for move in moves:
        next_board = _board_after(board, move)
        value = _minimax(
            next_board,
            root_color=color,
            side_to_move=opponent(color),
            depth=depth - 1,
            alpha=-10**9,
            beta=10**9,
        )
        scored.append((value, _move_order_score(board, move, color), rng.random(), move))
    scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return scored[0][3]


def _minimax(
    board: Board,
    root_color: str,
    side_to_move: str,
    depth: int,
    alpha: int,
    beta: int,
) -> int:
    if depth <= 0 or _find_general(board, root_color) is None or _find_general(board, opponent(root_color)) is None:
        return _evaluate_board(board, root_color)

    moves = _legal_moves_from_board(board, side_to_move)
    if not moves:
        return _evaluate_board(board, root_color)

    moves.sort(key=lambda move: _move_order_score(board, move, side_to_move), reverse=True)
    moves = moves[:SEARCH_NODE_LIMIT]
    if side_to_move == root_color:
        value = -10**9
        for move in moves:
            value = max(
                value,
                _minimax(_board_after(board, move), root_color, opponent(side_to_move), depth - 1, alpha, beta),
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = 10**9
    for move in moves:
        value = min(
            value,
            _minimax(_board_after(board, move), root_color, opponent(side_to_move), depth - 1, alpha, beta),
        )
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def _evaluate_board(board: Board, color: str) -> int:
    if _find_general(board, color) is None:
        return -PIECE_VALUES["general"] * 100
    if _find_general(board, opponent(color)) is None:
        return PIECE_VALUES["general"] * 100

    score = 0
    for pos, piece in board.items():
        piece_score = PIECE_VALUES[piece.kind] + _piece_square_bonus(pos, piece)
        score += piece_score if piece.color == color else -piece_score
    if _side_attacks_general(board, color):
        score += 260
    if _side_attacks_general(board, opponent(color)):
        score -= 320
    return score


def _piece_square_bonus(pos: Position, piece: Piece) -> int:
    x, y = pos
    center_distance = abs(x - 4) + abs(y - 4.5)
    bonus = 0
    if piece.kind in {"rook", "horse", "cannon"}:
        bonus += max(0, int(24 - center_distance * 3))
    if piece.kind == "pawn":
        crossed = y <= 4 if piece.color == RED else y >= 5
        bonus += 35 if crossed else 0
        bonus += max(0, int(12 - abs(x - 4) * 2))
    return bonus


def _side_attacks_general(board: Board, color: str) -> bool:
    general = _find_general(board, opponent(color))
    if general is None:
        return True
    for pos, piece in board.items():
        if piece.color == color and general in _attacks_from(board, pos, piece):
            return True
    return False


def _move_order_score(board: Board, move: Move, color: str) -> int:
    piece = board.get(move.start)
    captured = board.get(move.end)
    score = _capture_score(captured)
    if piece is not None:
        score += _piece_square_bonus(move.end, piece)
    next_board = _board_after(board, move)
    if _find_general(next_board, opponent(color)) is None:
        score += PIECE_VALUES["general"] * 20
    elif _side_attacks_general(next_board, color):
        score += 220
    return score


def _legal_moves_from_board(board: Board, color: str) -> List[Move]:
    moves: List[Move] = []
    for start, piece in list(board.items()):
        if piece.color != color:
            continue
        for target in _move_targets_from_board(board, start, piece):
            captured = board.get(target)
            if captured is None or captured.color != color:
                moves.append(Move(start, target))
    return moves


def _move_targets_from_board(board: Board, pos: Position, piece: Piece) -> Set[Position]:
    if piece.kind == "rook":
        return _line_targets(board, pos, cannon=False)
    if piece.kind == "cannon":
        return _cannon_move_targets(board, pos)
    return _attacks_from(board, pos, piece)


def _cannon_move_targets(board: Board, pos: Position) -> Set[Position]:
    x, y = pos
    targets = set()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cx, cy = x + dx, y + dy
        screen_seen = False
        while _inside(cx, cy):
            found = board.get((cx, cy))
            if not screen_seen:
                if found is None:
                    targets.add((cx, cy))
                else:
                    screen_seen = True
            else:
                if found is not None:
                    targets.add((cx, cy))
                    break
            cx += dx
            cy += dy
    return targets


def _capture_score(piece: Optional[Piece]) -> int:
    if piece is None:
        return 0
    return PIECE_VALUES[piece.kind] * 10


def _positional_score(move: Move, piece: Optional[Piece], color: str) -> int:
    if piece is None:
        return 0
    _, end_y = move.end
    score = 0
    if piece.kind == "pawn":
        crossed = end_y <= 4 if color == RED else end_y >= 5
        score += 40 if crossed else 0
    if piece.kind in {"horse", "cannon", "rook"}:
        center_distance = abs(move.end[0] - 4) + abs(move.end[1] - 4.5)
        score += max(0, int(30 - center_distance * 4))
    return score


def _check_pressure_score(game: Game, move: Move, color: str) -> int:
    board = _board_after(game.board, move)
    enemy_general = _find_general(board, opponent(color))
    if enemy_general is None:
        return PIECE_VALUES["general"]
    moved_piece = board.get(move.end)
    if moved_piece is None:
        return 0
    return 180 if enemy_general in _attacks_from(board, move.end, moved_piece) else 0


def _best_reply_capture(game: Game, move: Move, color: str) -> int:
    board = _board_after(game.board, move)
    enemy = opponent(color)
    best = 0
    for start, piece in list(board.items()):
        if piece.color != enemy:
            continue
        for target in _attacks_from(board, start, piece):
            captured = board.get(target)
            if captured is not None and captured.color == color:
                best = max(best, PIECE_VALUES[captured.kind] * 6)
    return best


def _board_after(board: Board, move: Move) -> Board:
    next_board = dict(board)
    piece = next_board.pop(move.start)
    next_board.pop(move.end, None)
    next_board[move.end] = piece
    return next_board


def _find_general(board: Board, color: str) -> Optional[Position]:
    for pos, piece in board.items():
        if piece.color == color and piece.kind == "general":
            return pos
    return None


def _attacks_from(board: Board, pos: Position, piece: Piece) -> Set[Position]:
    if piece.kind == "rook":
        return _line_targets(board, pos, cannon=False)
    if piece.kind == "cannon":
        return _line_targets(board, pos, cannon=True)
    if piece.kind == "horse":
        return _horse_targets(board, *pos)
    if piece.kind == "elephant":
        return _elephant_targets(board, *pos, piece.color)
    if piece.kind == "advisor":
        return _advisor_targets(*pos, piece.color)
    if piece.kind == "general":
        return _general_targets(board, *pos, piece.color)
    if piece.kind == "pawn":
        return _pawn_targets(*pos, piece.color)
    return set()


def _line_targets(board: Board, pos: Position, cannon: bool) -> Set[Position]:
    x, y = pos
    targets = set()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cx, cy = x + dx, y + dy
        screen_seen = False
        while _inside(cx, cy):
            found = board.get((cx, cy))
            if not cannon:
                targets.add((cx, cy))
                if found is not None:
                    break
            elif not screen_seen:
                if found is not None:
                    screen_seen = True
            else:
                if found is not None:
                    targets.add((cx, cy))
                    break
            cx += dx
            cy += dy
    return targets


def _horse_targets(board: Board, x: int, y: int) -> Set[Position]:
    options = [
        ((-2, -1), (-1, 0)),
        ((-2, 1), (-1, 0)),
        ((2, -1), (1, 0)),
        ((2, 1), (1, 0)),
        ((-1, -2), (0, -1)),
        ((1, -2), (0, -1)),
        ((-1, 2), (0, 1)),
        ((1, 2), (0, 1)),
    ]
    targets = set()
    for (dx, dy), (lx, ly) in options:
        target = (x + dx, y + dy)
        if board.get((x + lx, y + ly)) is None and _inside(*target):
            targets.add(target)
    return targets


def _elephant_targets(board: Board, x: int, y: int, color: str) -> Set[Position]:
    targets = set()
    for dx, dy in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
        target = (x + dx, y + dy)
        eye = (x + dx // 2, y + dy // 2)
        if not _inside(*target) or board.get(eye) is not None:
            continue
        if color == RED and target[1] < 5:
            continue
        if color == BLACK and target[1] > 4:
            continue
        targets.add(target)
    return targets


def _advisor_targets(x: int, y: int, color: str) -> Set[Position]:
    return {
        (tx, ty)
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1))
        for tx, ty in [(x + dx, y + dy)]
        if _in_palace(tx, ty, color)
    }


def _general_targets(board: Board, x: int, y: int, color: str) -> Set[Position]:
    targets = {
        (tx, ty)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        for tx, ty in [(x + dx, y + dy)]
        if _in_palace(tx, ty, color)
    }
    enemy_general = _find_general(board, opponent(color))
    if enemy_general is not None and enemy_general[0] == x:
        step = -1 if enemy_general[1] < y else 1
        clear = True
        for cy in range(y + step, enemy_general[1], step):
            if board.get((x, cy)) is not None:
                clear = False
                break
        if clear:
            targets.add(enemy_general)
    return targets


def _pawn_targets(x: int, y: int, color: str) -> Set[Position]:
    direction = -1 if color == RED else 1
    targets = set()
    forward = (x, y + direction)
    if _inside(*forward):
        targets.add(forward)
    crossed = y <= 4 if color == RED else y >= 5
    if crossed:
        for tx in (x - 1, x + 1):
            if _inside(tx, y):
                targets.add((tx, y))
    return targets


def _inside(x: int, y: int) -> bool:
    return 0 <= x <= 8 and 0 <= y <= 9


def _in_palace(x: int, y: int, color: str) -> bool:
    if not 3 <= x <= 5:
        return False
    return 7 <= y <= 9 if color == RED else 0 <= y <= 2
