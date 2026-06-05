import unittest

from xiangqi.engine import BLACK, RED, Game, Move, Piece


def empty_game():
    game = Game()
    game.board.clear()
    game.history.clear()
    game.turn = RED
    return game


class EngineTests(unittest.TestCase):
    def test_initial_board_has_standard_piece_positions(self):
        game = Game()

        self.assertEqual(game.piece_at(4, 9), Piece(RED, "general"))
        self.assertEqual(game.piece_at(4, 0), Piece(BLACK, "general"))
        self.assertEqual(game.piece_at(0, 9), Piece(RED, "rook"))
        self.assertEqual(game.piece_at(1, 0), Piece(BLACK, "horse"))
        self.assertEqual(game.turn, RED)

    def test_rook_moves_in_straight_lines_until_blocked(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 6, Piece(RED, "pawn"))
        game.set_piece(0, 5, Piece(RED, "rook"))
        game.set_piece(0, 3, Piece(RED, "pawn"))
        game.set_piece(3, 5, Piece(BLACK, "pawn"))

        targets = game.legal_targets(0, 5)

        self.assertIn((0, 4), targets)
        self.assertNotIn((0, 3), targets)
        self.assertIn((3, 5), targets)
        self.assertNotIn((4, 5), targets)

    def test_horse_leg_blocks_knight_like_move(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 6, Piece(RED, "pawn"))
        game.set_piece(4, 5, Piece(RED, "horse"))
        game.set_piece(4, 4, Piece(RED, "pawn"))

        targets = game.legal_targets(4, 5)

        self.assertNotIn((3, 3), targets)
        self.assertNotIn((5, 3), targets)
        self.assertIn((2, 4), targets)
        self.assertIn((6, 4), targets)

    def test_cannon_needs_one_screen_to_capture(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 6, Piece(RED, "pawn"))
        game.set_piece(1, 5, Piece(RED, "cannon"))
        game.set_piece(3, 5, Piece(RED, "pawn"))
        game.set_piece(5, 5, Piece(BLACK, "pawn"))
        game.set_piece(6, 5, Piece(BLACK, "rook"))

        targets = game.legal_targets(1, 5)

        self.assertIn((2, 5), targets)
        self.assertIn((5, 5), targets)
        self.assertNotIn((6, 5), targets)

    def test_pawn_changes_movement_after_crossing_river(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 5, Piece(RED, "pawn"))
        game.set_piece(2, 6, Piece(RED, "pawn"))
        game.set_piece(6, 3, Piece(BLACK, "pawn"))

        self.assertEqual(game.legal_targets(2, 6), {(2, 5)})

        game.set_piece(2, 6, None)
        game.set_piece(2, 4, Piece(RED, "pawn"))
        game.set_piece(6, 3, None)
        game.set_piece(6, 5, Piece(BLACK, "pawn"))

        self.assertLessEqual({(2, 3), (1, 4), (3, 4)}, game.legal_targets(2, 4))
        self.assertNotIn((2, 5), game.legal_targets(2, 4))
        self.assertLessEqual({(6, 6), (5, 5), (7, 5)}, game.legal_targets(6, 5))
        self.assertNotIn((6, 4), game.legal_targets(6, 5))

    def test_palace_elephant_and_advisor_restrictions(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 5, Piece(RED, "rook"))
        game.set_piece(4, 8, Piece(RED, "advisor"))
        game.set_piece(2, 9, Piece(RED, "elephant"))
        game.set_piece(3, 8, Piece(RED, "pawn"))

        advisor_targets = game.legal_targets(4, 8)
        elephant_targets = game.legal_targets(2, 9)

        self.assertEqual(advisor_targets, {(3, 7), (5, 7), (3, 9), (5, 9)})
        self.assertIn((0, 7), elephant_targets)
        self.assertNotIn((4, 7), elephant_targets)
        self.assertTrue(all(y >= 5 for _, y in elephant_targets))

    def test_player_can_move_even_if_that_leaves_own_general_in_check(self):
        game = empty_game()
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 5, Piece(RED, "rook"))

        self.assertIn((3, 5), game.legal_targets(4, 5))
        self.assertTrue(game.move(Move((4, 5), (3, 5))))
        self.assertEqual(game.piece_at(3, 5), Piece(RED, "rook"))
        self.assertTrue(game.is_in_check(RED))

    def test_capturing_general_wins_the_game(self):
        game = empty_game()
        game.turn = RED
        game.set_piece(4, 9, Piece(RED, "general"))
        game.set_piece(4, 0, Piece(BLACK, "general"))
        game.set_piece(4, 1, Piece(RED, "rook"))
        game.set_piece(0, 0, Piece(BLACK, "rook"))

        self.assertTrue(game.move(Move((4, 1), (4, 0))))
        self.assertEqual(game.piece_at(4, 0), Piece(RED, "rook"))
        self.assertEqual(game.status().winner, RED)
        self.assertEqual(game.status().reason, "general_captured")
        self.assertFalse(game.move(Move((0, 0), (0, 1))))
        self.assertEqual(game.piece_at(0, 0), Piece(BLACK, "rook"))
        self.assertIsNone(game.piece_at(0, 1))

    def test_move_log_undo_and_reset(self):
        game = Game()

        self.assertTrue(game.move(Move((0, 6), (0, 5))))
        self.assertEqual(game.turn, BLACK)
        self.assertEqual(game.move_log[-1], "兵九进一")

        self.assertTrue(game.undo())
        self.assertEqual(game.turn, RED)
        self.assertEqual(game.piece_at(0, 6), Piece(RED, "pawn"))
        self.assertIsNone(game.piece_at(0, 5))

        game.move(Move((0, 6), (0, 5)))
        game.reset()

        self.assertEqual(game.turn, RED)
        self.assertEqual(game.history, [])
        self.assertEqual(game.move_log, [])

    def test_black_move_log_uses_chinese_digits_and_preserves_piece_name(self):
        game = Game()

        self.assertTrue(game.move(Move((0, 6), (0, 5))))
        self.assertTrue(game.move(Move((0, 3), (0, 4))))

        self.assertEqual(game.move_log[-1], "卒一进一")


if __name__ == "__main__":
    unittest.main()
