# Mini Tetris

A small, playable desktop game with seven pieces, a landing guide, a next-piece
preview, line clearing, score, levels, pause, and restart.

## Play

Click **Let's play** or press **Space**. The game pauses automatically when its
window loses focus. Click the window and press Space to resume.

| Key | Action |
| --- | --- |
| Left / Right arrows | Move (hold to repeat) |
| Up arrow or X | Rotate clockwise |
| Z | Rotate counterclockwise |
| Down arrow | Soft drop (hold to fall faster) |
| Space | Hard drop / start / resume |
| P or Esc | Pause / resume |
| R | Restart |

Close the window to quit. Restart also works during pause and game over.

Clear 1 / 2 / 3 / 4 lines at once for 100 / 300 / 500 / 800 points times the
current level. Soft drops earn 1 point per cell; hard drops earn 2. Every 10
cleared lines raises the level and falling speed. Pieces have a short landing
delay so you can adjust them, plus simple wall and floor nudges when rotating.
This is a compact learning project, not an exact tournament rules implementation.

The only dependency is [pygame-ce](https://pypi.org/project/pygame-ce/).
No image or sound downloads are needed.

## Explore the code

- `game.py`: board, pieces, movement, rotation, scoring, and timing.
- `main.py`: window, drawing, and keyboard/mouse controls.
- `test_game.py`: automated checks for the gameplay rules.

Run the checks with `.venv/bin/python -m unittest -v`.
