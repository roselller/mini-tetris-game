"""Mini Tetris: the window, drawing, and keyboard/mouse controls.

All of the rules live in game.py. This file only shows the game on screen and
turns key presses and clicks into calls on the Game object.
"""

import pygame

from game import HEIGHT, SHAPES, WIDTH, Game

# --- Layout -----------------------------------------------------------------
CELL = 30
MARGIN = 20
BOARD_W, BOARD_H = WIDTH * CELL, HEIGHT * CELL
BOARD_X, BOARD_Y = MARGIN, MARGIN
SIDE_X = BOARD_X + BOARD_W + MARGIN
SIDE_W = 210
WINDOW_W = SIDE_X + SIDE_W + MARGIN
WINDOW_H = BOARD_H + 2 * MARGIN
FPS = 60

# The button on the start, pause, and game-over screens.
BUTTON_RECT = pygame.Rect(0, 0, 200, 52)
BUTTON_RECT.center = (BOARD_X + BOARD_W // 2, BOARD_Y + 360)

# Holding left or right waits a moment, then repeats quickly.
REPEAT_DELAY = 0.16
REPEAT_RATE = 0.045

# --- Colors -----------------------------------------------------------------
BACKGROUND = (17, 20, 30)
PANEL = (26, 30, 43)
GRID_LINE = (36, 41, 58)
TEXT = (233, 236, 244)
MUTED = (132, 141, 166)
BUTTON = (233, 236, 244)
BUTTON_HOVER = (255, 255, 255)
BUTTON_TEXT = (17, 20, 30)

PIECE_COLORS = {
    "I": (74, 201, 232),
    "O": (245, 200, 66),
    "T": (176, 108, 224),
    "S": (98, 204, 118),
    "Z": (236, 88, 98),
    "J": (86, 128, 236),
    "L": (243, 154, 64),
}

CONTROLS = (
    ("Left / Right", "Move"),
    ("Up or X", "Rotate"),
    ("Z", "Rotate back"),
    ("Down", "Soft drop"),
    ("Space", "Hard drop"),
    ("P or Esc", "Pause"),
    ("R", "Restart"),
)


def shade(color, amount):
    """Make a color lighter (positive) or darker (negative)."""
    return tuple(max(0, min(255, channel + amount)) for channel in color)


def draw_cell(surface, x, y, size, color):
    """Draw one solid block with a soft highlight along its top edge."""
    block = pygame.Rect(x + 1, y + 1, size - 2, size - 2)
    pygame.draw.rect(surface, shade(color, -45), block, border_radius=5)
    face = pygame.Rect(block.x, block.y, block.w, block.h - 3)
    pygame.draw.rect(surface, color, face, border_radius=5)
    shine = pygame.Rect(block.x + 4, block.y + 3, block.w - 8, 2)
    pygame.draw.rect(surface, shade(color, 60), shine, border_radius=1)


def draw_ghost(surface, x, y, size, color):
    """Draw the outline that shows where the piece will land."""
    outline = pygame.Rect(x + 3, y + 3, size - 6, size - 6)
    pygame.draw.rect(surface, shade(color, -30), outline, width=2, border_radius=4)


def make_font(size, bold=True):
    return pygame.font.SysFont("avenirnext,helveticaneue,arial,dejavusans", size, bold=bold)


class App:
    """Owns the window and connects input to a Game."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Mini Tetris")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": make_font(38),
            "value": make_font(30),
            "button": make_font(22),
            "body": make_font(18, bold=False),
            "label": make_font(16, bold=False),
            "small": make_font(15, bold=False),
        }
        self.game = Game()
        self.started = False
        self.held = []          # left/right keys currently down, newest last
        self.repeat_timer = 0.0
        self.soft_held = False  # is the down arrow being held?

    # --- State ---------------------------------------------------------------

    @property
    def mode(self):
        """Which full-board screen is showing, or None while playing."""
        if not self.started:
            return "menu"
        if self.game.over:
            return "over"
        if self.game.paused:
            return "paused"
        return None

    def clear_held(self):
        self.held.clear()
        self.soft_held = False
        self.repeat_timer = 0.0

    def new_game(self):
        self.game.restart()
        self.started = True
        self.clear_held()

    def toggle_pause(self):
        if self.started and not self.game.over:
            self.game.paused = not self.game.paused
            self.clear_held()

    def activate(self):
        """What the button and (on menus) the Space key do."""
        mode = self.mode
        if mode == "paused":
            self.game.paused = False
        elif mode in ("menu", "over"):
            self.new_game()

    # --- Input ---------------------------------------------------------------

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            self.key_down(event.key)
        elif event.type == pygame.KEYUP:
            self.key_up(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode and BUTTON_RECT.collidepoint(event.pos):
                self.activate()
        elif event.type == pygame.WINDOWFOCUSLOST:
            # Pause so nothing falls while the player is in another window.
            if self.mode is None:
                self.game.paused = True
                self.clear_held()

    def key_down(self, key):
        mode = self.mode
        if key == pygame.K_r:
            if mode in ("paused", "over", None):
                self.new_game()
        elif key == pygame.K_SPACE:
            if mode is None:
                self.game.hard_drop()
            elif mode in ("menu", "paused"):
                self.activate()
            # On the game-over screen Space does nothing, so a quick hard-drop
            # tap can't skip past the final score. Use R or the button instead.
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            self.toggle_pause()
        elif mode is None:
            if key == pygame.K_LEFT:
                self.press_direction(-1)
            elif key == pygame.K_RIGHT:
                self.press_direction(1)
            elif key in (pygame.K_UP, pygame.K_x):
                self.game.rotate(clockwise=True)
            elif key == pygame.K_z:
                self.game.rotate(clockwise=False)
            elif key == pygame.K_DOWN:
                self.soft_held = True
                self.game.soft_drop()

    def key_up(self, key):
        if key == pygame.K_LEFT:
            self.release_direction(-1)
        elif key == pygame.K_RIGHT:
            self.release_direction(1)
        elif key == pygame.K_DOWN:
            self.soft_held = False

    def press_direction(self, direction):
        if direction in self.held:
            self.held.remove(direction)
        self.held.append(direction)
        self.game.move(direction)
        self.repeat_timer = REPEAT_DELAY

    def release_direction(self, direction):
        if direction in self.held:
            self.held.remove(direction)
            self.repeat_timer = REPEAT_DELAY

    # --- Update --------------------------------------------------------------

    def update(self, dt):
        if self.mode is not None:
            return
        if self.held:
            self.repeat_timer -= dt
            while self.repeat_timer <= 0:
                self.game.move(self.held[-1])
                self.repeat_timer += REPEAT_RATE
        self.game.update(dt, soft_drop=self.soft_held)

    # --- Drawing -------------------------------------------------------------

    def text(self, string, font, color, **anchor):
        image = self.fonts[font].render(string, True, color)
        rect = image.get_rect(**anchor)
        self.screen.blit(image, rect)
        return rect

    def draw(self):
        self.screen.fill(BACKGROUND)
        self.draw_board()
        self.draw_sidebar()
        if self.mode:
            self.draw_overlay(self.mode)

    def draw_board(self):
        game = self.game
        frame = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)
        pygame.draw.rect(self.screen, PANEL, frame.inflate(8, 8), border_radius=8)

        for col in range(1, WIDTH):
            x = BOARD_X + col * CELL
            pygame.draw.line(self.screen, GRID_LINE, (x, BOARD_Y), (x, BOARD_Y + BOARD_H))
        for row in range(1, HEIGHT):
            y = BOARD_Y + row * CELL
            pygame.draw.line(self.screen, GRID_LINE, (BOARD_X, y), (BOARD_X + BOARD_W, y))

        for row, line in enumerate(game.board):
            for col, kind in enumerate(line):
                if kind is not None:
                    draw_cell(self.screen, BOARD_X + col * CELL, BOARD_Y + row * CELL,
                              CELL, PIECE_COLORS[kind])

        if self.started and not game.over:
            color = PIECE_COLORS[game.piece]
            for col, row in game.cells(game.shape, game.x, game.landing_y()):
                if row >= 0:
                    draw_ghost(self.screen, BOARD_X + col * CELL, BOARD_Y + row * CELL,
                               CELL, color)
            for col, row in game.cells():
                if row >= 0:
                    draw_cell(self.screen, BOARD_X + col * CELL, BOARD_Y + row * CELL,
                              CELL, color)

    def draw_sidebar(self):
        game = self.game
        left = SIDE_X + 18

        # Next piece
        preview = pygame.Rect(SIDE_X, MARGIN, SIDE_W, 130)
        pygame.draw.rect(self.screen, PANEL, preview, border_radius=8)
        self.text("Next piece", "label", MUTED, topleft=(left, preview.y + 14))
        self.draw_preview(game.next_piece, (preview.centerx, preview.y + 80))

        # Score, lines, level
        stats = pygame.Rect(SIDE_X, preview.bottom + 16, SIDE_W, 196)
        pygame.draw.rect(self.screen, PANEL, stats, border_radius=8)
        for index, (label, value) in enumerate((("Score", game.score),
                                                ("Lines", game.lines),
                                                ("Level", game.level))):
            top = stats.y + 12 + index * 62
            self.text(label, "label", MUTED, topleft=(left, top))
            self.text(f"{value:,}", "value", TEXT, topleft=(left, top + 20))

        # Controls
        controls = pygame.Rect(SIDE_X, stats.bottom + 16, SIDE_W,
                               BOARD_Y + BOARD_H - stats.bottom - 16)
        pygame.draw.rect(self.screen, PANEL, controls, border_radius=8)
        self.text("Controls", "label", MUTED, topleft=(left, controls.y + 14))
        for index, (keys, action) in enumerate(CONTROLS):
            top = controls.y + 44 + index * 22
            self.text(keys, "small", TEXT, topleft=(left, top))
            self.text(action, "small", MUTED, topright=(controls.right - 18, top))

    def draw_preview(self, kind, center, size=24):
        cells = [(col, row)
                 for row, line in enumerate(SHAPES[kind])
                 for col, cell in enumerate(line) if cell != "."]
        first_col = min(col for col, _ in cells)
        first_row = min(row for _, row in cells)
        width = max(col for col, _ in cells) - first_col + 1
        height = max(row for _, row in cells) - first_row + 1
        left = center[0] - width * size // 2
        top = center[1] - height * size // 2
        for col, row in cells:
            draw_cell(self.screen, left + (col - first_col) * size,
                      top + (row - first_row) * size, size, PIECE_COLORS[kind])

    def draw_overlay(self, mode):
        game = self.game
        cover = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        cover.fill((12, 14, 22, 242))
        self.screen.blit(cover, (BOARD_X, BOARD_Y))

        center_x = BOARD_X + BOARD_W // 2
        if mode == "menu":
            title, button = "Mini Tetris", "Let's play"
            lines = ("Stack the pieces.", "Clear the lines.")
            hint = "or press Space"
        elif mode == "paused":
            title, button = "Paused", "Resume"
            lines = ("Your game is on hold.",)
            hint = "or press Space. R restarts."
        else:
            title, button = "Game over", "Play again"
            lines = (f"Score {game.score:,}",
                     f"{game.lines} lines, level {game.level}")
            hint = "or press R"

        self.text(title, "title", TEXT, center=(center_x, BOARD_Y + 200))
        for index, line in enumerate(lines):
            self.text(line, "body", MUTED, center=(center_x, BOARD_Y + 250 + index * 28))

        hovered = BUTTON_RECT.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, BUTTON_HOVER if hovered else BUTTON,
                         BUTTON_RECT, border_radius=10)
        self.text(button, "button", BUTTON_TEXT, center=BUTTON_RECT.center)
        self.text(hint, "label", MUTED, center=(center_x, BUTTON_RECT.bottom + 26))

    # --- Main loop -----------------------------------------------------------

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()