mport pygame
import sys
 
# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 620        # extra 20px at top for score bar (Phase 3)
GRID_SIZE     = 20         # number of cells per row/column
CELL_SIZE     = WINDOW_WIDTH // GRID_SIZE  # 30px per cell
FPS           = 10         # frames per second (controls snake speed)
 
# Colors (R, G, B)
COLOR_BG        = (15,  15,  35)   # dark navy background
COLOR_GRID      = (25,  25,  55)   # subtle grid lines
COLOR_HEAD      = (78,  204, 163)  # bright teal – snake head
COLOR_BODY      = (45,  160, 120)  # darker teal – snake body
COLOR_PANEL     = (20,  20,  45)   # top info panel
COLOR_TEXT      = (200, 200, 220)  # light text
 
 
# ─────────────────────────────────────────
# SNAKE CLASS
# ─────────────────────────────────────────
class Snake:
    def __init__(self):
        self.reset()
 
    def reset(self):
        # Start with a 3-cell snake in the centre, moving right
        cx = GRID_SIZE // 2
        cy = GRID_SIZE // 2
        self.body = [
            (cx,     cy),   # head
            (cx - 1, cy),   # body
            (cx - 2, cy),   # tail
        ]
        self.direction = (1, 0)   # (dx, dy) → moving right
        self.next_dir  = (1, 0)   # queued direction
 
    def set_direction(self, new_dir):
        """Queue a direction change; prevents 180-degree reversal."""
        dx, dy = new_dir
        # Opposite of current direction would be (-dx, -dy)
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.next_dir = (dx, dy)
 
    def move(self):
        """Advance the snake by one cell. Returns the new head position."""
        self.direction = self.next_dir
 
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
 
        # Phase 1: wrap around walls so you can play freely.
        # Phase 2 will replace this with a wall-collision check.
        new_head = (new_head[0] % GRID_SIZE, new_head[1] % GRID_SIZE)
 
        # Add new head; remove tail.
        # Phase 2: skip pop() when the snake eats food (it grows).
        self.body.insert(0, new_head)
        self.body.pop()
 
        return new_head
 
    def draw(self, surface, offset_y):
        """Draw every segment of the snake."""
        for index, (gx, gy) in enumerate(self.body):
            color = COLOR_HEAD if index == 0 else COLOR_BODY
 
            # Each cell gets a small inner padding so you can see the grid
            padding = 3
            rect = pygame.Rect(
                gx * CELL_SIZE + padding,
                gy * CELL_SIZE + padding + offset_y,
                CELL_SIZE - padding * 2,
                CELL_SIZE - padding * 2,
            )
            pygame.draw.rect(surface, color, rect, border_radius=6)
 
            # Draw eyes on the head
            if index == 0:
                self._draw_eyes(surface, gx, gy, offset_y)
 
    def _draw_eyes(self, surface, gx, gy, offset_y):
        """Draw two small eyes facing the current direction."""
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + offset_y
        eye_radius = 3
        pupil_radius = 1
        offset = 5
 
        dx, dy = self.direction
 
        if   dx ==  1:  e1, e2 = (cx+5, cy-offset), (cx+5, cy+offset)  # right
        elif dx == -1:  e1, e2 = (cx-5, cy-offset), (cx-5, cy+offset)  # left
        elif dy == -1:  e1, e2 = (cx-offset, cy-5), (cx+offset, cy-5)  # up
        else:           e1, e2 = (cx-offset, cy+5), (cx+offset, cy+5)  # down
 
        for pos in (e1, e2):
            pygame.draw.circle(surface, (255, 255, 255), pos, eye_radius)
            pygame.draw.circle(surface, (15,  15,  35),  pos, pupil_radius)
 
 
# ─────────────────────────────────────────
# GAME CLASS
# ─────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Game – Phase 1")
 
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock  = pygame.time.Clock()
        self.font   = pygame.font.SysFont("Segoe UI", 18)
 
        # Panel height at top (reserved for score in Phase 3)
        self.panel_h = 20
 
        self.snake   = Snake()
        self.started = False     # game starts on first arrow key press
 
    def run(self):
        """Main game loop."""
        while True:
            self._handle_events()
 
            if self.started:
                self.snake.move()
 
            self._draw()
            self.clock.tick(FPS)
 
    def _handle_events(self):
        """Process keyboard and window-close events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
 
            if event.type == pygame.KEYDOWN:
                direction_map = {
                    pygame.K_UP:    (0, -1),
                    pygame.K_DOWN:  (0,  1),
                    pygame.K_LEFT:  (-1, 0),
                    pygame.K_RIGHT: (1,  0),
                }
                if event.key in direction_map:
                    self.snake.set_direction(direction_map[event.key])
                    if not self.started:
                        self.started = True   # start moving on first key
 
    def _draw(self):
        """Render everything each frame."""
        self.screen.fill(COLOR_BG)
 
        # ── Top panel (placeholder for score in Phase 3)
        panel_rect = pygame.Rect(0, 0, WINDOW_WIDTH, self.panel_h)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect)
 
        label = "Phase 1 – press an arrow key to start" if not self.started else "Phase 1 – Snake Game"
        text_surf = self.font.render(label, True, COLOR_TEXT)
        self.screen.blit(text_surf, (10, 2))
 
        # ── Grid lines
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID,
                             (x, self.panel_h), (x, WINDOW_HEIGHT))
        for y in range(self.panel_h, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID,
                             (0, y), (WINDOW_WIDTH, y))
 
        # ── Snake
        self.snake.draw(self.screen, self.panel_h)
 
        pygame.display.flip()
 
 
# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
