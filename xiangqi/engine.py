from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


RED = "red"
BLACK = "black"
COLORS = (RED, BLACK)
Position = Tuple[int, int]


@dataclass(frozen=True)
class Piece:
    color: str
    kind: str


@dataclass(frozen=True)
class Move:
    start: Position
    end: Position


@dataclass(frozen=True)
class GameStatus:
    turn: str
    in_check: bool
    winner: Optional[str] = None
    reason: str = "playing"


@dataclass(frozen=True)
class HistoryEntry:
    move: Move
    moved: Piece
    captured: Optional[Piece]
    previous_turn: str
    notation: str


def opponent(color: str) -> str:
    return BLACK if color == RED else RED


def chinese_number(value: int) -> str:
    digits = "零一二三四五六七八九"
    if 0 <= value <= 9:
        return digits[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        prefix = "" if tens == 1 else digits[tens]
        suffix = "" if ones == 0 else digits[ones]
        return f"{prefix}十{suffix}"
    return str(value)


class Game:
    def __init__(self) -> None:
        self.board: Dict[Position, Piece] = {}
        self.history: List[HistoryEntry] = []
        self.move_log: List[str] = []
        self.turn = RED
        self.reset()

    def reset(self) -> None:
        self.board.clear()
        self.history.clear()
        self.move_log.clear()
        self.turn = RED
        self._setup_side(RED)
        self._setup_side(BLACK)

    def _setup_side(self, color: str) -> None:
        back_y = 9 if color == RED else 0
        pawn_y = 6 if color == RED else 3
        cannon_y = 7 if color == RED else 2
        back_rank = [
            "rook",
            "horse",
            "elephant",
            "advisor",
            "general",
            "advisor",
            "elephant",
            "horse",
            "rook",
        ]
        for x, kind in enumerate(back_rank):
            self.set_piece(x, back_y, Piece(color, kind))
        for x in (0, 2, 4, 6, 8):
            self.set_piece(x, pawn_y, Piece(color, "pawn"))
        for x in (1, 7):
            self.set_piece(x, cannon_y, Piece(color, "cannon"))

    def piece_at(self, x: int, y: int) -> Optional[Piece]:
        return self.board.get((x, y))

    def set_piece(self, x: int, y: int, piece: Optional[Piece]) -> None:
        if piece is None:
            self.board.pop((x, y), None)
        else:
            self.board[(x, y)] = piece

    def legal_targets(self, x: int, y: int) -> Set[Position]:
        piece = self.piece_at(x, y)
        if piece is None:
            return set()
        targets = set()
        for target in self._raw_targets((x, y), piece):
            captured = self.board.get(target)
            if captured is not None and captured.color == piece.color:
                continue
            targets.add(target)
        return targets

    def all_legal_moves(self, color: str) -> List[Move]:
        moves: List[Move] = []
        for (x, y), piece in list(self.board.items()):
            if piece.color == color:
                for target in self.legal_targets(x, y):
                    moves.append(Move((x, y), target))
        return moves

    def move(self, move: Move) -> bool:
        if self.status().winner:
            return False
        piece = self.board.get(move.start)
        if piece is None or piece.color != self.turn:
            return False
        if move.end not in self.legal_targets(*move.start):
            return False
        captured = self.board.get(move.end)
        notation = self.format_move(move, piece)
        self._apply_unrecorded(move)
        self.history.append(HistoryEntry(move, piece, captured, self.turn, notation))
        self.move_log.append(notation)
        self.turn = opponent(self.turn)
        return True

    def undo(self) -> bool:
        if not self.history:
            return False
        entry = self.history.pop()
        self.set_piece(*entry.move.start, entry.moved)
        self.set_piece(*entry.move.end, entry.captured)
        self.turn = entry.previous_turn
        self.move_log.pop()
        return True

    def status(self) -> GameStatus:
        if self._find_general(RED) is None:
            return GameStatus(turn=self.turn, in_check=False, winner=BLACK, reason="general_captured")
        if self._find_general(BLACK) is None:
            return GameStatus(turn=self.turn, in_check=False, winner=RED, reason="general_captured")
        in_check = self.is_in_check(self.turn)
        return GameStatus(self.turn, in_check)

    def is_in_check(self, color: str) -> bool:
        general_pos = self._find_general(color)
        if general_pos is None:
            return True
        enemy = opponent(color)
        for pos, piece in list(self.board.items()):
            if piece.color == enemy and general_pos in self._raw_targets(pos, piece, attacks_only=True):
                return True
        return False

    def format_move(self, move: Move, piece: Piece) -> str:
        names = {
            "general": "帥" if piece.color == RED else "將",
            "advisor": "仕" if piece.color == RED else "士",
            "elephant": "相" if piece.color == RED else "象",
            "horse": "馬",
            "rook": "車",
            "cannon": "炮",
            "pawn": "兵" if piece.color == RED else "卒",
        }
        files_red = "九八七六五四三二一"
        files_black = "一二三四五六七八九"
        sx, sy = move.start
        ex, ey = move.end
        file_name = files_red[sx] if piece.color == RED else files_black[sx]
        if sx == ex:
            forward = ey < sy if piece.color == RED else ey > sy
            action = "进" if forward else "退"
            amount = abs(ey - sy)
            number = chinese_number(amount)
            return f"{names[piece.kind]}{file_name}{action}{number}"
        action = "平"
        dest_file = files_red[ex] if piece.color == RED else files_black[ex]
        return f"{names[piece.kind]}{file_name}{action}{dest_file}"

    def _raw_targets(self, pos: Position, piece: Piece, attacks_only: bool = False) -> Set[Position]:
        x, y = pos
        if piece.kind == "rook":
            return set(self._line_targets(pos, piece.color, cannon=False))
        if piece.kind == "cannon":
            return set(self._line_targets(pos, piece.color, cannon=True, attacks_only=attacks_only))
        if piece.kind == "horse":
            return self._horse_targets(x, y)
        if piece.kind == "elephant":
            return self._elephant_targets(x, y, piece.color)
        if piece.kind == "advisor":
            return self._advisor_targets(x, y, piece.color)
        if piece.kind == "general":
            return self._general_targets(x, y, piece.color)
        if piece.kind == "pawn":
            return self._pawn_targets(x, y, piece.color)
        return set()

    def _line_targets(
        self,
        pos: Position,
        color: str,
        cannon: bool,
        attacks_only: bool = False,
    ) -> Iterable[Position]:
        x, y = pos
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cx, cy = x + dx, y + dy
            screen_seen = False
            while self._inside(cx, cy):
                piece = self.piece_at(cx, cy)
                if not cannon:
                    yield (cx, cy)
                    if piece is not None:
                        break
                elif not screen_seen:
                    if piece is None and not attacks_only:
                        yield (cx, cy)
                    elif piece is not None:
                        screen_seen = True
                else:
                    if piece is not None:
                        yield (cx, cy)
                        break
                cx += dx
                cy += dy

    def _horse_targets(self, x: int, y: int) -> Set[Position]:
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
            if self.piece_at(x + lx, y + ly) is None and self._inside(x + dx, y + dy):
                targets.add((x + dx, y + dy))
        return targets

    def _elephant_targets(self, x: int, y: int, color: str) -> Set[Position]:
        targets = set()
        for dx, dy in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
            tx, ty = x + dx, y + dy
            eye = (x + dx // 2, y + dy // 2)
            if not self._inside(tx, ty) or self.piece_at(*eye) is not None:
                continue
            if color == RED and ty < 5:
                continue
            if color == BLACK and ty > 4:
                continue
            targets.add((tx, ty))
        return targets

    def _advisor_targets(self, x: int, y: int, color: str) -> Set[Position]:
        return {
            (tx, ty)
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1))
            for tx, ty in [(x + dx, y + dy)]
            if self._in_palace(tx, ty, color)
        }

    def _general_targets(self, x: int, y: int, color: str) -> Set[Position]:
        targets = {
            (tx, ty)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            for tx, ty in [(x + dx, y + dy)]
            if self._in_palace(tx, ty, color)
        }
        enemy_general = self._find_general(opponent(color))
        if enemy_general is not None and enemy_general[0] == x:
            step = -1 if enemy_general[1] < y else 1
            clear = True
            for cy in range(y + step, enemy_general[1], step):
                if self.piece_at(x, cy) is not None:
                    clear = False
                    break
            if clear:
                targets.add(enemy_general)
        return targets

    def _pawn_targets(self, x: int, y: int, color: str) -> Set[Position]:
        direction = -1 if color == RED else 1
        targets = set()
        forward = (x, y + direction)
        if self._inside(*forward):
            targets.add(forward)
        crossed = y <= 4 if color == RED else y >= 5
        if crossed:
            for tx in (x - 1, x + 1):
                if self._inside(tx, y):
                    targets.add((tx, y))
        return targets

    def _inside(self, x: int, y: int) -> bool:
        return 0 <= x <= 8 and 0 <= y <= 9

    def _in_palace(self, x: int, y: int, color: str) -> bool:
        if not 3 <= x <= 5:
            return False
        return 7 <= y <= 9 if color == RED else 0 <= y <= 2

    def _find_general(self, color: str) -> Optional[Position]:
        for pos, piece in self.board.items():
            if piece.color == color and piece.kind == "general":
                return pos
        return None

    def _apply_unrecorded(self, move: Move) -> None:
        piece = self.board.pop(move.start)
        self.board.pop(move.end, None)
        self.board[move.end] = piece

    def _revert_unrecorded(self, move: Move, moved: Piece, captured: Optional[Piece]) -> None:
        self.board.pop(move.end, None)
        self.board[move.start] = moved
        if captured is not None:
            self.board[move.end] = captured
