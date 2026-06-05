import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from xiangqi.ai import DIFFICULTIES
from xiangqi.engine import BLACK, RED, Move
from xiangqi.ui import MODE_AI, MODE_TWO_PLAYER, RESULT_MAIN_MENU, ResultDialog, XiangqiWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_ai_mode_undo_reverts_full_round(app):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = "ai"
    window.ai_difficulty = "初窥门径"

    assert window.game.move(Move((0, 6), (0, 5)))
    assert window.game.move(Move((0, 3), (0, 4)))

    window.undo()

    assert len(window.game.history) == 0
    assert window.game.turn == RED


def test_ai_mode_undo_reverts_single_move_when_only_one_exists(app):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = "ai"
    window.ai_difficulty = "初窥门径"

    assert window.game.move(Move((0, 6), (0, 5)))

    window.undo()

    assert len(window.game.history) == 0
    assert window.game.turn == RED


def test_reset_preserves_ai_mode_and_difficulty(app):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = "ai"
    window.ai_difficulty = "弈臻化境"
    window.review_locked = True
    assert window.game.move(Move((0, 6), (0, 5)))

    window.reset()

    assert window.mode == "ai"
    assert window.ai_difficulty == "弈臻化境"
    assert window.review_locked is False
    assert len(window.game.history) == 0
    assert window.game.turn == RED


def test_result_dialog_can_choose_main_menu(app):
    dialog = ResultDialog("红方", RED)

    dialog.choose_result(RESULT_MAIN_MENU)

    assert dialog.result_action == RESULT_MAIN_MENU
    assert dialog.result() == QDialog.Accepted


def test_return_to_main_menu_resets_game_and_reselects_mode(app):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = MODE_AI
    window.ai_difficulty = "弈臻化境"
    window.review_locked = True
    window.result_prompt_shown = True
    assert window.game.move(Move((0, 6), (0, 5)))
    calls = []

    def choose_two_player():
        calls.append("called")
        window.mode = MODE_TWO_PLAYER
        window.ai_difficulty = None

    window.choose_startup_mode = choose_two_player

    window.return_to_main_menu()

    assert calls == ["called"]
    assert window.mode == MODE_TWO_PLAYER
    assert window.ai_difficulty is None
    assert window.review_locked is False
    assert window.result_prompt_shown is False
    assert len(window.game.history) == 0
    assert window.game.turn == RED


def test_show_result_dialog_main_menu_action_returns_to_mode_selection(app, monkeypatch):
    window = XiangqiWindow(show_startup_dialog=False)
    window.game.set_piece(4, 0, None)
    calls = []

    class FakeResultDialog:
        def __init__(self, winner, winner_color, parent=None):
            self.result_action = RESULT_MAIN_MENU

        def exec(self):
            return QDialog.Accepted

    monkeypatch.setattr("xiangqi.ui.ResultDialog", FakeResultDialog)

    def return_to_main_menu():
        calls.append("called")

    window.return_to_main_menu = return_to_main_menu

    window.show_result_dialog()

    assert calls == ["called"]


def test_closing_startup_mode_dialog_marks_window_cancelled(app, monkeypatch):
    class FakeModeDialog:
        selected = None

        def __init__(self, parent=None):
            pass

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr("xiangqi.ui.ModeDialog", FakeModeDialog)

    window = XiangqiWindow(show_startup_dialog=True)

    assert window.startup_cancelled is True
    assert window.choose_startup_mode() is False


def test_move_list_uses_chinese_numbering_and_side_colors(app):
    window = XiangqiWindow(show_startup_dialog=False)

    assert window.game.move(Move((0, 6), (0, 5)))
    assert window.game.move(Move((0, 3), (0, 4)))
    window.refresh()

    first_item = window.move_list.item(0)
    first_label = window.move_list.itemWidget(first_item)
    second_item = window.move_list.item(1)
    second_label = window.move_list.itemWidget(second_item)

    assert first_item.text() == "1. 兵九进一"
    assert 'color="#2f7d4a">1.</font>' in first_label.text()
    assert 'color="#b21b14">兵九进一</font>' in first_label.text()
    assert first_item.sizeHint().height() >= 30
    assert first_label.minimumHeight() >= 30
    assert second_item.text() == "2. 卒一进一"
    assert 'color="#2f7d4a">2.</font>' in second_label.text()
    assert 'color="#1e1e1e">卒一进一</font>' in second_label.text()
    assert second_item.sizeHint().height() >= 30
    assert second_label.minimumHeight() >= 30


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_ai_move_calculation_returns_without_blocking_ui(app, monkeypatch, difficulty):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = MODE_AI
    window.ai_difficulty = difficulty
    assert window.game.move(Move((0, 6), (0, 5)))
    assert window.game.turn == BLACK

    def slow_choose_ai_move(game, color, difficulty):
        time.sleep(0.2)
        return None

    monkeypatch.setattr("xiangqi.ui.choose_ai_move", slow_choose_ai_move)

    start = time.perf_counter()
    window.maybe_make_ai_move()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.05
    assert window.ai_thinking is True

    window.ai_worker.wait(1000)


def test_reset_during_ai_calculation_does_not_block_ui(app, monkeypatch):
    window = XiangqiWindow(show_startup_dialog=False)
    window.mode = MODE_AI
    window.ai_difficulty = "弈臻化境"
    assert window.game.move(Move((0, 6), (0, 5)))

    def slow_choose_ai_move(game, color, difficulty):
        time.sleep(0.2)
        return None

    monkeypatch.setattr("xiangqi.ui.choose_ai_move", slow_choose_ai_move)
    window.maybe_make_ai_move()

    start = time.perf_counter()
    window.reset()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.05
    assert window.ai_thinking is False

    for worker in list(window.ai_workers):
        worker.wait(1000)
