"""Tetris rules, kept separate from drawing so they are easy to test."""

import random

WIDTH, HEIGHT = 10, 20
LOCK_DELAY = 0.45
MAX_LOCK_RESETS = 12

# Square grids give each piece a fixed center for rotation.
SHAPES = {
    "I": ("....", "IIII", "....", "...."),
    "O": ("OO", "OO"),
    "T": (".T.", "TTT", "..."),
    "S": (".SS", "SS.", "..."),
    "Z": ("ZZ.", ".ZZ", "..."),
    "J": ("J..", "JJJ", "..."),
    "L": ("..L", "LLL", "..."),
}


def rotate_grid(shape, clockwise=True):
    """Return a quarter-turn of a square grid."""
    if clockwise:
        return tuple("".join(row) for row in zip(*shape[::-1]))
    return tuple("".join(row) for row in zip(*shape))[::-1]


class Game:
    def __init__(self, seed=None):
        self.random = random.Random(seed)
        self.restart()

    def restart(self):
        self.board = [[None] * WIDTH for _ in range(HEIGHT)]
        self.score = 0
        self.lines = 0
        self.paused = False
        self.over = False
        self.bag = []
        self.next_piece = self.draw_piece()
        self.spawn()

    @property
    def level(self):
        return self.lines // 10 + 1

    @property
    def fall_interval(self):
        return max(0.075, 0.8 * 0.82 ** (self.level - 1))

    def draw_piece(self):
        # A shuffled bag gives all seven pieces before any repeats.
        if not self.bag:
            self.bag = list(SHAPES)
            self.random.shuffle(self.bag)
        return self.bag.pop()

    def spawn(self):
        self.piece = self.next_piece
        self.next_piece = self.draw_piece()
        self.shape = SHAPES[self.piece]
        self.x = (WIDTH - len(self.shape)) // 2
        self.y = 0
        self.fall_time = 0.0
        self.lock_time = 0.0
        self.lock_resets = 0
        if not self.fits(self.shape, self.x, self.y):
            self.over = True

    def cells(self, shape=None, x=None, y=None):
        shape = self.shape if shape is None else shape
        x = self.x if x is None else x
        y = self.y if y is None else y
        return [(x + col, y + row)
                for row, line in enumerate(shape)
                for col, cell in enumerate(line) if cell != "."]

    def fits(self, shape, x, y):
        for col, row in self.cells(shape, x, y):
            if col < 0 or col >= WIDTH or row >= HEIGHT:
                return False
            if row >= 0 and self.board[row][col] is not None:
                return False
        return True

    def grounded(self):
        return not self.fits(self.shape, self.x, self.y + 1)

    def reset_lock(self, was_grounded):
        if was_grounded and self.lock_resets < MAX_LOCK_RESETS:
            self.lock_time = 0.0
            self.lock_resets += 1

    def move(self, dx, dy=0):
        if self.over or self.paused:
            return False
        if not self.fits(self.shape, self.x + dx, self.y + dy):
            return False
        was_grounded = self.grounded()
        self.x += dx
        self.y += dy
        if dx:
            self.reset_lock(was_grounded)
        return True

    def rotate(self, clockwise=True):
        if self.over or self.paused or self.piece == "O":
            return False
        rotated = rotate_grid(self.shape, clockwise)
        # Small wall/floor nudges let pieces turn beside an obstacle.
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0),
                       (0, -1), (-1, -1), (1, -1), (0, -2)):
            if self.fits(rotated, self.x + dx, self.y + dy):
                was_grounded = self.grounded()
                self.shape = rotated
                self.x += dx
                self.y += dy
                self.reset_lock(was_grounded)
                return True
        return False

    def landing_y(self):
        y = self.y
        while self.fits(self.shape, self.x, y + 1):
            y += 1
        return y

    def soft_drop(self):
        if self.move(0, 1):
            self.score += 1
            return True
        return False

    def hard_drop(self):
        if self.over or self.paused:
            return
        destination = self.landing_y()
        self.score += 2 * (destination - self.y)
        self.y = destination
        self.lock()

    def clear_lines(self):
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = HEIGHT - len(remaining)
        self.board = [[None] * WIDTH for _ in range(cleared)] + remaining
        self.score += (0, 100, 300, 500, 800)[cleared] * self.level
        self.lines += cleared
        return cleared

    def lock(self):
        cells = self.cells()
        if any(row < 0 for _, row in cells):
            self.over = True
            return
        for col, row in cells:
            self.board[row][col] = self.piece
        self.clear_lines()
        self.spawn()

    def update(self, dt, soft_drop=False):
        if self.paused or self.over:
            return
        # Clamp long gaps (for example, a dragged window) to avoid sudden drops.
        dt = min(dt, 0.1)
        self.fall_time += dt
        interval = min(0.045, self.fall_interval) if soft_drop else self.fall_interval
        while self.fall_time >= interval:
            self.fall_time -= interval
            if not self.move(0, 1):
                self.fall_time = 0.0
                break
            if soft_drop:
                self.score += 1
        if self.grounded():
            self.lock_time += dt
            if self.lock_time >= LOCK_DELAY:
                self.lock()
        elif self.lock_resets < MAX_LOCK_RESETS:
            self.lock_time = 0.0
