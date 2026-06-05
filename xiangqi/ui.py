from html import escape

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .ai import DIFFICULTIES, choose_ai_move
from .engine import BLACK, RED, Game, Move, Piece


PIECE_TEXT = {
    (RED, "general"): "帥",
    (RED, "advisor"): "仕",
    (RED, "elephant"): "相",
    (RED, "horse"): "馬",
    (RED, "rook"): "車",
    (RED, "cannon"): "炮",
    (RED, "pawn"): "兵",
    (BLACK, "general"): "將",
    (BLACK, "advisor"): "士",
    (BLACK, "elephant"): "象",
    (BLACK, "horse"): "馬",
    (BLACK, "rook"): "車",
    (BLACK, "cannon"): "炮",
    (BLACK, "pawn"): "卒",
}

MODE_AI = "ai"
MODE_TWO_PLAYER = "two_player"
RESULT_REVIEW = "review"
RESULT_RESTART = "restart"
RESULT_MAIN_MENU = "main_menu"
MOVE_INDEX_COLOR = "#2f7d4a"
RED_MOVE_COLOR = "#b21b14"
BLACK_MOVE_COLOR = "#1e1e1e"
MOVE_LOG_ROW_HEIGHT = 34


class AiMoveWorker(QThread):
    moveReady = Signal(int, object)

    def __init__(self, request_id: int, board, turn: str, color: str, difficulty: str, parent=None) -> None:
        super().__init__(parent)
        self.request_id = request_id
        self.board = dict(board)
        self.turn = turn
        self.color = color
        self.difficulty = difficulty

    def run(self) -> None:
        game = Game()
        game.board = dict(self.board)
        game.history.clear()
        game.move_log.clear()
        game.turn = self.turn
        move = choose_ai_move(game, self.color, self.difficulty)
        self.moveReady.emit(self.request_id, move)


class BoardWidget(QWidget):
    moveRequested = Signal(tuple, tuple)
    selectionChanged = Signal(tuple)

    def __init__(self, game: Game, parent=None) -> None:
        super().__init__(parent)
        self.game = game
        self.selected = None
        self.targets = set()
        self.input_enabled = True
        self.margin = 44
        self.cell = 64
        self.setMinimumSize(660, 760)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_input_enabled(self, enabled: bool) -> None:
        self.input_enabled = enabled
        if not enabled:
            self.clear_selection()

    def set_selection(self, pos):
        self.selected = pos
        self.targets = self.game.legal_targets(*pos) if pos else set()
        self.update()

    def clear_selection(self):
        self.selected = None
        self.targets = set()
        self.update()

    def mousePressEvent(self, event) -> None:
        if not self.input_enabled:
            self.clear_selection()
            return
        if self.game.status().winner:
            self.clear_selection()
            return
        pos = self._point_to_board(event.position())
        if pos is None:
            self.clear_selection()
            return
        piece = self.game.piece_at(*pos)
        if self.selected and pos in self.targets:
            self.moveRequested.emit(self.selected, pos)
            return
        if piece and piece.color == self.game.turn:
            self.set_selection(pos)
            self.selectionChanged.emit(pos)
        else:
            self.clear_selection()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._configure_geometry()
        self._draw_background(painter)
        self._draw_board(painter)
        self._draw_highlights(painter)
        self._draw_pieces(painter)

    def _configure_geometry(self):
        usable_w = max(1, self.width() - 2 * self.margin)
        usable_h = max(1, self.height() - 2 * self.margin)
        self.cell = min(usable_w / 8, usable_h / 9)
        board_w = self.cell * 8
        board_h = self.cell * 9
        self.origin_x = (self.width() - board_w) / 2
        self.origin_y = (self.height() - board_h) / 2

    def _draw_background(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor("#b98243"))
        inset = QRectF(18, 18, self.width() - 36, self.height() - 36)
        painter.fillRect(inset, QColor("#f0c878"))
        painter.setPen(QPen(QColor("#7a4b1e"), 4))
        painter.drawRoundedRect(inset, 8, 8)

    def _draw_board(self, painter: QPainter) -> None:
        line_color = QColor("#684016")
        painter.setPen(QPen(line_color, 2))
        for y in range(10):
            self._draw_line(painter, (0, y), (8, y))
        for x in range(9):
            self._draw_line(painter, (x, 0), (x, 4))
            self._draw_line(painter, (x, 5), (x, 9))

        self._draw_line(painter, (3, 0), (5, 2))
        self._draw_line(painter, (5, 0), (3, 2))
        self._draw_line(painter, (3, 7), (5, 9))
        self._draw_line(painter, (5, 7), (3, 9))

        river_rect = QRectF(
            self.origin_x,
            self.origin_y + self.cell * 4,
            self.cell * 8,
            self.cell,
        )
        painter.fillRect(river_rect.adjusted(2, 2, -2, -2), QColor("#f4d58b"))
        painter.setPen(QColor("#7a411b"))
        painter.setFont(QFont("Microsoft YaHei", max(18, int(self.cell * 0.28)), QFont.Bold))
        painter.drawText(river_rect, Qt.AlignCenter, "楚河        汉界")

    def _draw_highlights(self, painter: QPainter) -> None:
        if self.selected:
            painter.setBrush(QColor(255, 235, 135, 150))
            painter.setPen(QPen(QColor("#b13c2e"), 3))
            painter.drawEllipse(self._piece_rect(*self.selected).adjusted(-4, -4, 4, 4))
        painter.setBrush(QColor(42, 125, 83, 170))
        painter.setPen(Qt.NoPen)
        for x, y in self.targets:
            center = self._board_to_point(x, y)
            painter.drawEllipse(center, self.cell * 0.11, self.cell * 0.11)

    def _draw_pieces(self, painter: QPainter) -> None:
        for (x, y), piece in self.game.board.items():
            rect = self._piece_rect(x, y)
            painter.setBrush(QColor("#f8ead1"))
            painter.setPen(QPen(QColor("#8a5521"), 2))
            painter.drawEllipse(rect)
            painter.setPen(QPen(QColor("#b21b14" if piece.color == RED else "#1e1e1e"), 2))
            painter.drawEllipse(rect.adjusted(5, 5, -5, -5))
            painter.setFont(QFont("SimSun", max(18, int(self.cell * 0.42)), QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, PIECE_TEXT[(piece.color, piece.kind)])

    def _draw_line(self, painter: QPainter, start, end) -> None:
        painter.drawLine(self._board_to_point(*start), self._board_to_point(*end))

    def _board_to_point(self, x: int, y: int) -> QPointF:
        return QPointF(self.origin_x + x * self.cell, self.origin_y + y * self.cell)

    def _piece_rect(self, x: int, y: int) -> QRectF:
        center = self._board_to_point(x, y)
        r = self.cell * 0.38
        return QRectF(center.x() - r, center.y() - r, r * 2, r * 2)

    def _point_to_board(self, point: QPointF):
        x = round((point.x() - self.origin_x) / self.cell)
        y = round((point.y() - self.origin_y) / self.cell)
        if not (0 <= x <= 8 and 0 <= y <= 9):
            return None
        center = self._board_to_point(x, y)
        distance = ((point.x() - center.x()) ** 2 + (point.y() - center.y()) ** 2) ** 0.5
        if distance <= self.cell * 0.45:
            return (x, y)
        return None


class ResultDialog(QDialog):
    def __init__(self, winner: str, winner_color: str, parent=None) -> None:
        super().__init__(parent)
        self.result_action = None
        self.setWindowTitle("本局结束")
        self.setModal(True)
        self.setFixedSize(500, 330)
        accent = "#b21b14" if winner_color == RED else "#1f1f1f"

        self.setStyleSheet(
            f"""
            QDialog {{
                background: #f2cf87;
                border: 3px solid #6b3f17;
                border-radius: 10px;
            }}
            QLabel#seal {{
                background: #fff3d3;
                color: {accent};
                border: 3px solid {accent};
                border-radius: 42px;
                font-size: 34px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }}
            QLabel#title {{
                color: #3b210d;
                font-size: 30px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }}
            QLabel#subtitle {{
                color: #694018;
                font-size: 15px;
                line-height: 1.4;
                font-family: "Microsoft YaHei";
            }}
            QPushButton {{
                border: 0;
                border-radius: 7px;
                padding: 11px 22px;
                font-size: 16px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }}
            QPushButton#reviewButton {{
                background: #fff6dc;
                color: #5b3513;
                border: 1px solid #9a6a2f;
            }}
            QPushButton#reviewButton:hover {{
                background: #fff0c5;
            }}
            QPushButton#resetButton {{
                background: #8f3d25;
                color: white;
            }}
            QPushButton#resetButton:hover {{
                background: #a8482d;
            }}
            QPushButton#mainMenuButton {{
                background: #fff6dc;
                color: #5b3513;
                border: 1px solid #9a6a2f;
            }}
            QPushButton#mainMenuButton:hover {{
                background: #fff0c5;
            }}
            """
        )

        seal = QLabel("胜")
        seal.setObjectName("seal")
        seal.setFixedSize(84, 84)
        seal.setAlignment(Qt.AlignCenter)

        title = QLabel(f"{winner}获胜")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("帅/将已被吃掉，本局到此结束。\n复盘会锁定当前局面，重开会沿用当前模式，主界面可重新选择模式。")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        review_button = QPushButton("复盘")
        review_button.setObjectName("reviewButton")
        reset_button = QPushButton("重开")
        reset_button.setObjectName("resetButton")
        main_menu_button = QPushButton("主界面")
        main_menu_button.setObjectName("mainMenuButton")
        review_button.clicked.connect(lambda: self.choose_result(RESULT_REVIEW))
        reset_button.clicked.connect(lambda: self.choose_result(RESULT_RESTART))
        main_menu_button.clicked.connect(lambda: self.choose_result(RESULT_MAIN_MENU))

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(review_button)
        button_row.addWidget(reset_button)
        button_row.addWidget(main_menu_button)
        button_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 26, 34, 26)
        layout.setSpacing(16)
        layout.addWidget(seal, 0, Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(1)
        layout.addLayout(button_row)

    def choose_result(self, action: str) -> None:
        self.result_action = action
        self.accept()


class ChoiceDialog(QDialog):
    def __init__(self, title: str, subtitle: str, seal_text: str, choices, parent=None) -> None:
        super().__init__(parent)
        self.selected = None
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(460, 350)
        self.setStyleSheet(
            """
            QDialog {
                background: #f2cf87;
                border: 3px solid #6b3f17;
                border-radius: 10px;
            }
            QLabel#seal {
                background: #fff3d3;
                color: #8f3d25;
                border: 3px solid #8f3d25;
                border-radius: 42px;
                font-size: 28px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLabel#title {
                color: #3b210d;
                font-size: 28px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLabel#subtitle {
                color: #694018;
                font-size: 15px;
                line-height: 1.4;
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                border: 0;
                border-radius: 7px;
                padding: 11px 18px;
                font-size: 16px;
                font-weight: bold;
                font-family: "Microsoft YaHei";
                background: #8f3d25;
                color: white;
            }
            QPushButton:hover {
                background: #a8482d;
            }
            """
        )

        seal = QLabel(seal_text)
        seal.setObjectName("seal")
        seal.setFixedSize(84, 84)
        seal.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)

        button_layout = QVBoxLayout()
        button_layout.setSpacing(9)
        for text, value in choices:
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, choice=value: self._choose(choice))
            button_layout.addWidget(button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 24, 34, 24)
        layout.setSpacing(14)
        layout.addWidget(seal, 0, Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)
        layout.addLayout(button_layout)

    def _choose(self, choice) -> None:
        self.selected = choice
        self.accept()


class ModeDialog(ChoiceDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "选择对弈模式",
            "请选择本局的对弈方式。AI 对弈中玩家执红先手，AI 执黑后手。",
            "弈",
            [("AI 对弈", MODE_AI), ("双人对弈", MODE_TWO_PLAYER)],
            parent,
        )


class DifficultyDialog(ChoiceDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(
            "选择 AI 难度",
            "难度由浅入深，当前版本为离线本地 AI。",
            "AI",
            [(name, name) for name in DIFFICULTIES],
            parent,
        )


class XiangqiWindow(QMainWindow):
    def __init__(self, show_startup_dialog: bool = True) -> None:
        super().__init__()
        self.game = Game()
        self.mode = MODE_TWO_PLAYER
        self.ai_difficulty = None
        self.ai_thinking = False
        self.ai_worker = None
        self.ai_workers = []
        self.ai_request_id = 0
        self.review_locked = False
        self.result_prompt_shown = False
        self.startup_cancelled = False
        self.setWindowTitle("中国象棋")
        self.resize(980, 780)
        self.board = BoardWidget(self.game)
        self.board.moveRequested.connect(self.handle_move)
        self.board.selectionChanged.connect(self.handle_selection)

        self.turn_label = QLabel()
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.move_list = QListWidget()

        undo_button = QPushButton("悔棋")
        reset_button = QPushButton("重开")
        undo_button.clicked.connect(self.undo)
        reset_button.clicked.connect(self.reset)

        side = QVBoxLayout()
        title = QLabel("中国象棋")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        side.addWidget(title)
        side.addWidget(self.turn_label)
        side.addWidget(self.status_label)
        side.addWidget(QLabel("走法记录"))
        side.addWidget(self.move_list, 1)
        side.addWidget(undo_button)
        side.addWidget(reset_button)

        panel = QWidget()
        panel.setLayout(side)
        panel.setFixedWidth(250)
        panel.setStyleSheet(
            """
            QWidget { background: #fff8e7; color: #3d2a16; }
            QLabel { font-size: 16px; }
            QListWidget { background: #fffdf5; border: 1px solid #c9a66a; font-size: 14px; }
            QPushButton {
                background: #8f3d25; color: white; border: 0; border-radius: 6px;
                padding: 10px; font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background: #a8482d; }
            """
        )

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.board, 1)
        layout.addWidget(panel)
        self.setCentralWidget(root)
        self.refresh()
        if show_startup_dialog:
            self.choose_startup_mode()

    def handle_selection(self, pos) -> None:
        if self.review_locked:
            return
        if self.ai_thinking or self.is_ai_turn():
            self.status_label.setText("AI 正在行棋。")
            self.board.clear_selection()
            return
        piece = self.game.piece_at(*pos)
        if piece:
            color = "红方" if piece.color == RED else "黑方"
            self.status_label.setText(f"已选中：{color} {PIECE_TEXT[(piece.color, piece.kind)]}")

    def handle_move(self, start, end) -> None:
        if self.review_locked:
            self.board.clear_selection()
            return
        if self.ai_thinking or self.is_ai_turn():
            self.status_label.setText("AI 正在行棋。")
            self.board.clear_selection()
            return
        if not self.game.move(Move(start, end)):
            self.status_label.setText("这步不合法。")
            self.board.clear_selection()
            return
        self.board.clear_selection()
        self.refresh()
        if self.game.status().winner:
            self.show_result_dialog()
        else:
            self.maybe_make_ai_move()

    def undo(self) -> None:
        if self.review_locked:
            self.status_label.setText("复盘中不能悔棋，请选择重开。")
            return
        if self.ai_thinking:
            self.status_label.setText("AI 正在行棋，请稍候。")
            return
        if self.mode == MODE_AI:
            undone = False
            if self.game.history:
                undone = self.game.undo() or undone
            if self.game.history:
                undone = self.game.undo() or undone
            if undone:
                self.result_prompt_shown = False
                self.board.clear_selection()
                self.refresh()
            else:
                self.status_label.setText("当前没有可悔的棋。")
            return
        if self.game.undo():
            self.board.clear_selection()
            self.refresh()
        else:
            self.status_label.setText("当前没有可悔的棋。")

    def reset(self) -> None:
        self._cancel_ai_worker()
        self.game.reset()
        self.review_locked = False
        self.result_prompt_shown = False
        self.board.clear_selection()
        self.refresh()

    def return_to_main_menu(self) -> None:
        self._cancel_ai_worker()
        self.game.reset()
        self.review_locked = False
        self.result_prompt_shown = False
        self.board.clear_selection()
        self.choose_startup_mode()

    def choose_startup_mode(self) -> bool:
        mode_dialog = ModeDialog(self)
        if mode_dialog.exec() != QDialog.Accepted or not mode_dialog.selected:
            self.startup_cancelled = True
            self.close()
            return False
        self.startup_cancelled = False
        self.mode = mode_dialog.selected
        if self.mode == MODE_TWO_PLAYER:
            self.ai_difficulty = None
        if self.mode == MODE_AI:
            difficulty_dialog = DifficultyDialog(self)
            if difficulty_dialog.exec() == QDialog.Accepted and difficulty_dialog.selected:
                self.ai_difficulty = difficulty_dialog.selected
            else:
                self.ai_difficulty = DIFFICULTIES[0]
        self.refresh()
        return True

    def is_ai_turn(self) -> bool:
        return self.mode == MODE_AI and self.game.turn == BLACK and not self.game.status().winner

    def maybe_make_ai_move(self) -> None:
        if not self.is_ai_turn() or self.ai_thinking:
            return
        self.ai_thinking = True
        self.refresh()
        self.ai_request_id += 1
        worker = AiMoveWorker(
            self.ai_request_id,
            self.game.board,
            self.game.turn,
            BLACK,
            self.ai_difficulty or DIFFICULTIES[0],
            self,
        )
        self.ai_worker = worker
        self.ai_workers.append(worker)
        worker.moveReady.connect(self.apply_ai_move)
        worker.finished.connect(lambda worker=worker: self._release_ai_worker(worker))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def apply_ai_move(self, request_id: int, move) -> None:
        if request_id != self.ai_request_id:
            return
        self.ai_thinking = False
        self.ai_worker = None
        if move is not None and self.is_ai_turn():
            self.game.move(move)
        self.board.clear_selection()
        self.refresh()
        if self.game.status().winner:
            self.show_result_dialog()

    def _cancel_ai_worker(self) -> None:
        self.ai_request_id += 1
        self.ai_thinking = False
        self.ai_worker = None

    def _release_ai_worker(self, worker: AiMoveWorker) -> None:
        if worker in self.ai_workers:
            self.ai_workers.remove(worker)

    def show_result_dialog(self) -> None:
        if self.result_prompt_shown:
            return
        self.result_prompt_shown = True
        status = self.game.status()
        winner = "红方" if status.winner == RED else "黑方"
        dialog = ResultDialog(winner, status.winner, self)
        dialog.exec()
        if dialog.result_action == RESULT_REVIEW:
            self.review_locked = True
            self.board.clear_selection()
            self.refresh()
        elif dialog.result_action == RESULT_MAIN_MENU:
            self.return_to_main_menu()
        else:
            self.reset()

    def refresh(self) -> None:
        status = self.game.status()
        turn_name = "红方" if self.game.turn == RED else "黑方"
        mode_name = "AI 对弈" if self.mode == MODE_AI else "双人对弈"
        difficulty = f" / {self.ai_difficulty}" if self.mode == MODE_AI and self.ai_difficulty else ""
        self.turn_label.setText(f"当前回合：{turn_name}\n模式：{mode_name}{difficulty}")
        self.board.set_input_enabled(not self.ai_thinking and not self.is_ai_turn())
        if status.winner:
            winner = "红方" if status.winner == RED else "黑方"
            reason = "吃掉帅/将" if status.reason == "general_captured" else "胜利"
            suffix = "复盘中，棋子位置已锁定。" if self.review_locked else "本局结束。"
            self.status_label.setText(f"{winner}获胜：{reason}。{suffix}")
        elif self.ai_thinking or self.is_ai_turn():
            self.status_label.setText("AI 正在行棋。")
        elif status.in_check:
            self.status_label.setText(f"{turn_name}被将军。")
        else:
            self.status_label.setText("请选择当前方棋子行棋。")

        self.move_list.clear()
        for index, entry in enumerate(self.game.history, start=1):
            side_color = RED_MOVE_COLOR if entry.moved.color == RED else BLACK_MOVE_COLOR
            text = f"{index}. {entry.notation}"
            item = QListWidgetItem(text)
            label = QLabel(
                f'<font color="{MOVE_INDEX_COLOR}">{index}.</font> '
                f'<font color="{side_color}">{escape(entry.notation)}</font>'
            )
            label.setTextFormat(Qt.RichText)
            label.setMinimumHeight(MOVE_LOG_ROW_HEIGHT)
            label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            label.setStyleSheet("background: transparent; padding: 5px 4px;")
            item.setSizeHint(QSize(0, MOVE_LOG_ROW_HEIGHT))
            self.move_list.addItem(item)
            self.move_list.setItemWidget(item, label)
        self.move_list.scrollToBottom()
        self.board.update()
