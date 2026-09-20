"""Gameplay checks that run without opening a window."""

import unittest

from game import Game, HEIGHT, LOCK_DELAY, MAX_LOCK_RESETS, SHAPES, WIDTH, rotate_grid


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=42)

    def piece(self, kind, x=3, y=0):
        self.game.piece = kind
        self.game.shape = SHAPES[kind]
        self.game.x, self.game.y = x, y

    def test_bags_have_each_of_seven_pieces(self):
        game = self.game
        pieces = [game.piece, game.next_piece] + [game.draw_piece() for _ in range(12)]
        self.assertEqual(set(pieces[:7]), set(SHAPES))
        self.assertEqual(set(pieces[7:]), set(SHAPES))

    def test_all_shapes_have_four_cells_and_rotate_back(self):
        for shape in SHAPES.values():
            self.assertEqual(sum(cell != "." for row in shape for cell in row), 4)
            rotated = shape
            for _ in range(4):
                rotated = rotate_grid(rotated)
            self.assertEqual(rotated, shape)
            self.assertEqual(rotate_grid(rotate_grid(shape), False), shape)

    def test_movement_stops_at_both_walls(self):
        self.piece("O", x=0)
        self.assertFalse(self.game.move(-1))
        for _ in range(20):
            self.game.move(1)
        self.assertEqual(self.game.x, WIDTH - 2)
        self.assertFalse(self.game.move(1))

    def test_floor_and_stack_collision(self):
        self.piece("O", y=HEIGHT - 2)
        self.assertFalse(self.game.move(0, 1))
        self.game.y = 5
        self.game.board[7][3] = "T"
        self.assertFalse(self.game.move(0, 1))
        self.assertEqual(self.game.y, 5)

    def test_rotation_kicks_away_from_wall(self):
        self.piece("I", x=-2)
        self.game.shape = rotate_grid(SHAPES["I"])
        self.assertTrue(self.game.fits(self.game.shape, -2, 0))
        self.assertTrue(self.game.rotate())
        self.assertTrue(all(0 <= x < WIDTH for x, _ in self.game.cells()))

    def test_rotation_kicks_above_floor(self):
        self.piece("I", y=HEIGHT - 2)
        self.assertTrue(self.game.rotate())
        self.assertTrue(all(y < HEIGHT for _, y in self.game.cells()))

    def test_fully_blocked_rotation_does_not_change_piece(self):
        self.piece("T", x=3, y=5)
        cells = set(self.game.cells())
        self.game.board = [[None if (x, y) in cells else "J" for x in range(WIDTH)]
                           for y in range(HEIGHT)]
        before = self.game.shape, self.game.x, self.game.y
        self.assertFalse(self.game.rotate())
        self.assertEqual((self.game.shape, self.game.x, self.game.y), before)

    def test_hard_drop_uses_ghost_position_and_spawns_next(self):
        self.piece("O")
        self.assertEqual(self.game.landing_y(), 18)
        expected_next = self.game.next_piece
        self.game.hard_drop()
        self.assertEqual(self.game.score, 36)
        self.assertEqual(self.game.board[19][3:5], ["O", "O"])
        self.assertEqual(self.game.piece, expected_next)

    def test_soft_drop_only_scores_successful_steps(self):
        self.piece("O", y=17)
        self.assertTrue(self.game.soft_drop())
        self.assertFalse(self.game.soft_drop())
        self.assertEqual(self.game.score, 1)

    def test_line_clearing_preserves_rows_and_does_not_alias(self):
        self.game.board[19] = ["I"] * WIDTH
        self.game.board[18][0] = "L"
        self.assertEqual(self.game.clear_lines(), 1)
        self.assertEqual(self.game.board[19][0], "L")
        self.assertEqual(self.game.score, 100)
        self.game.board[0][0] = "O"
        self.assertIsNone(self.game.board[1][0])

    def test_one_to_four_line_scores(self):
        for count, score in enumerate((100, 300, 500, 800), start=1):
            game = Game(seed=1)
            game.board[-count:] = [["J"] * WIDTH for _ in range(count)]
            self.assertEqual(game.clear_lines(), count)
            self.assertEqual(game.score, score)
            self.assertEqual(game.lines, count)
            self.assertTrue(all(cell is None for row in game.board for cell in row))

    def test_lock_completes_four_lines(self):
        self.piece("I", x=1, y=16)
        self.game.shape = rotate_grid(SHAPES["I"])
        for y in range(16, 20):
            self.game.board[y] = [None if x == 3 else "L" for x in range(WIDTH)]
        self.game.hard_drop()
        self.assertEqual(self.game.lines, 4)
        self.assertEqual(self.game.score, 800)

    def test_level_increases_speed_and_multiplies_score(self):
        self.game.lines = 9
        original_speed = self.game.fall_interval
        self.game.board[19] = ["I"] * WIDTH
        self.game.clear_lines()
        self.assertEqual(self.game.level, 2)
        self.assertLess(self.game.fall_interval, original_speed)
        self.assertEqual(self.game.score, 100)
        self.game.board[19] = ["I"] * WIDTH
        self.game.clear_lines()
        self.assertEqual(self.game.score, 300)

    def test_gravity_and_landing_delay(self):
        self.piece("O", y=17)
        for _ in range(9):
            self.game.update(0.1)
        self.assertEqual(self.game.y, 18)
        self.assertIsNone(self.game.board[19][3])
        for _ in range(5):
            self.game.update(0.1)
        self.assertEqual(self.game.board[19][3], "O")

    def test_lock_reset_limit_prevents_infinite_stalling(self):
        self.piece("O", y=18)
        for index in range(MAX_LOCK_RESETS):
            self.game.lock_time = 0.3
            self.game.move(1 if index % 2 == 0 else -1)
            self.assertEqual(self.game.lock_time, 0)
        self.game.lock_time = LOCK_DELAY - 0.01
        self.game.move(1)
        self.game.update(0.02)
        self.assertEqual(self.game.board[19][4], "O")

    def test_pause_freezes_all_gameplay(self):
        self.game.paused = True
        before = (self.game.x, self.game.y, self.game.shape, self.game.score)
        self.assertFalse(self.game.move(1))
        self.assertFalse(self.game.rotate())
        self.game.soft_drop()
        self.game.hard_drop()
        self.game.update(10)
        self.assertEqual((self.game.x, self.game.y, self.game.shape, self.game.score), before)

    def test_blocked_spawn_ends_game(self):
        self.game.next_piece = "O"
        self.game.board[0][4] = "T"
        self.game.spawn()
        self.assertTrue(self.game.over)
        self.assertFalse(self.game.move(1))

    def test_lock_above_top_ends_game_without_negative_index_writes(self):
        self.piece("O", y=-1)
        self.game.lock()
        self.assertTrue(self.game.over)
        self.assertTrue(all(cell is None for row in self.game.board for cell in row))

    def test_restart_clears_every_game_state(self):
        self.game.hard_drop()
        self.game.lines = 28
        self.game.paused = True
        self.game.over = True
        self.game.restart()
        self.assertEqual((self.game.score, self.game.lines, self.game.level), (0, 0, 1))
        self.assertFalse(self.game.paused or self.game.over)
        self.assertEqual((self.game.fall_time, self.game.lock_time, self.game.lock_resets), (0, 0, 0))
        self.assertTrue(all(cell is None for row in self.game.board for cell in row))
        self.assertTrue(self.game.fits(self.game.shape, self.game.x, self.game.y))


if __name__ == "__main__":
    unittest.main()
