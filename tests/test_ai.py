from xiangqi.ai import DIFFICULTIES, choose_ai_move
from xiangqi.engine import BLACK, RED, Game, Move, Piece


def empty_game(turn=RED):
    game = Game()
    game.board.clear()
    game.history.clear()
    game.move_log.clear()
    game.turn = turn
    return game


def test_all_five_difficulties_are_available():
    assert list(DIFFICULTIES) == [
        "初窥门径",
        "小试牛刀",
        "渐通棋理",
        "纵横盘间",
        "弈臻化境",
    ]


def test_ai_returns_a_legal_move_without_changing_board():
    game = Game()
    before = dict(game.board)

    move = choose_ai_move(game, RED, "初窥门径", seed=7)

    assert isinstance(move, Move)
    assert move.end in game.legal_targets(*move.start)
    assert game.board == before
    assert game.turn == RED


def test_second_level_prefers_higher_value_capture():
    game = empty_game(RED)
    game.set_piece(4, 9, Piece(RED, "general"))
    game.set_piece(4, 0, Piece(BLACK, "general"))
    game.set_piece(4, 6, Piece(RED, "pawn"))
    game.set_piece(0, 5, Piece(RED, "rook"))
    game.set_piece(0, 4, Piece(BLACK, "pawn"))
    game.set_piece(3, 5, Piece(BLACK, "rook"))

    move = choose_ai_move(game, RED, "小试牛刀", seed=1)

    assert move == Move((0, 5), (3, 5))


def test_highest_level_takes_immediate_general_capture():
    game = empty_game(BLACK)
    game.set_piece(4, 9, Piece(RED, "general"))
    game.set_piece(4, 0, Piece(BLACK, "general"))
    game.set_piece(4, 8, Piece(BLACK, "rook"))
    game.set_piece(0, 0, Piece(RED, "rook"))

    move = choose_ai_move(game, BLACK, "弈臻化境", seed=1)

    assert move == Move((4, 8), (4, 9))


def test_highest_level_uses_search_to_create_a_forced_general_threat():
    game = empty_game(RED)
    game.set_piece(4, 9, Piece(RED, "general"))
    game.set_piece(4, 0, Piece(BLACK, "general"))
    game.set_piece(6, 2, Piece(RED, "rook"))
    game.set_piece(5, 3, Piece(RED, "horse"))
    game.set_piece(2, 6, Piece(RED, "horse"))
    game.set_piece(2, 5, Piece(RED, "advisor"))
    game.set_piece(4, 5, Piece(BLACK, "cannon"))
    game.set_piece(4, 4, Piece(BLACK, "horse"))
    game.set_piece(2, 7, Piece(BLACK, "elephant"))

    move = choose_ai_move(game, RED, "弈臻化境", seed=1)

    assert move == Move((6, 2), (6, 0))


def test_ai_returns_none_when_no_legal_moves_are_available():
    game = empty_game(BLACK)

    move = choose_ai_move(game, BLACK, "初窥门径", seed=1)

    assert move is None
