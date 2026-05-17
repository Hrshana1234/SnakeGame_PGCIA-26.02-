import pygame
import sys
import random

# ─────────────────────────────────────────
# WINDOW / GRID
# ─────────────────────────────────────────
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 640
GRID_SIZE     = 20
CELL_SIZE     = WINDOW_WIDTH // GRID_SIZE   # 30 px
PANEL_H       = 40

# ─────────────────────────────────────────
# DIFFICULTY SETTINGS
# ─────────────────────────────────────────
DIFFICULTIES = {
    "EASY": {
        "fps_start":   6,
        "fps_max":    14,
        "speed_step":  3,   # foods eaten per +1 FPS
        "barriers":    0,
        "label_color": (80, 200, 120),
    },
    "MEDIUM": {
        "fps_start":   9,
        "fps_max":    18,
        "speed_step":  3,
        "barriers":   15,
        "label_color": (220, 180, 50),
    },
    "HARD": {
        "fps_start":  14,
        "fps_max":    22,
        "speed_step":  2,
        "barriers":   30,
        "label_color": (220, 70, 70),
    },
}
DIFFICULTY_ORDER = ["EASY", "MEDIUM", "HARD"]

# ─────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────
COLOR_BG        = (15,  15,  35)
COLOR_GRID      = (25,  25,  55)
COLOR_HEAD      = (78,  204, 163)
COLOR_BODY      = (45,  160, 120)
COLOR_FOOD      = (220,  80,  80)
COLOR_FOOD_GLOW = (255, 120, 120)
COLOR_BARRIER   = (160,  90,  30)   # dark orange-brown brick
COLOR_BARRIER_H = (200, 120,  50)   # lighter highlight edge
COLOR_PANEL     = (12,  12,  30)
COLOR_TEXT      = (200, 200, 220)
COLOR_TEAL      = (78,  204, 163)
COLOR_GOLD      = (255, 200,  60)
COLOR_DIM       = (100, 100, 130)

# ─────────────────────────────────────────
# GAME STATES
# ─────────────────────────────────────────
STATE_MENU     = "menu"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"


# ─────────────────────────────────────────
# SNAKE
# ─────────────────────────────────────────
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        cx = GRID_SIZE // 2
        cy = GRID_SIZE // 2
        self.body = [
            (cx,     cy),
            (cx - 1, cy),
            (cx - 2, cy),
        ]
        self.direction = (1, 0)
        self.next_dir  = (1, 0)

    def set_direction(self, new_dir):
        if new_dir != (-self.direction[0], -self.direction[1]):
            self.next_dir = new_dir

    def move(self, grow=False):
        self.direction = self.next_dir
        hx, hy = self.body[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)
        if not grow:
            self.body.pop()
        return new_head

    def head(self):
        return self.body[0]

    def check_wall_collision(self):
        hx, hy = self.head()
        return hx < 0 or hx >= GRID_SIZE or hy < 0 or hy >= GRID_SIZE

    def check_self_collision(self):
        return self.head() in self.body[1:]

    def draw(self, surface):
        total = len(self.body)
        for index, (gx, gy) in enumerate(self.body):
            if index == 0:
                color = COLOR_HEAD
            else:
                t = index / max(total - 1, 1)
                color = (
                    int(COLOR_BODY[0] * (1 - t * 0.45)),
                    int(COLOR_BODY[1] * (1 - t * 0.45)),
                    int(COLOR_BODY[2] * (1 - t * 0.45)),
                )
            pad  = 3
            rect = pygame.Rect(
                gx * CELL_SIZE + pad,
                gy * CELL_SIZE + pad + PANEL_H,
                CELL_SIZE - pad * 2,
                CELL_SIZE - pad * 2,
            )
            pygame.draw.rect(surface, color, rect, border_radius=6)
            if index == 0:
                self._draw_eyes(surface, gx, gy)

    def _draw_eyes(self, surface, gx, gy):
        cx     = gx * CELL_SIZE + CELL_SIZE // 2
        cy     = gy * CELL_SIZE + CELL_SIZE // 2 + PANEL_H
        offset = 5
        dx, dy = self.direction
        if   dx ==  1: e1, e2 = (cx+5, cy-offset), (cx+5, cy+offset)
        elif dx == -1: e1, e2 = (cx-5, cy-offset), (cx-5, cy+offset)
        elif dy == -1: e1, e2 = (cx-offset, cy-5), (cx+offset, cy-5)
        else:          e1, e2 = (cx-offset, cy+5), (cx+offset, cy+5)
        for pos in (e1, e2):
            pygame.draw.circle(surface, (255, 255, 255), pos, 3)
            pygame.draw.circle(surface, COLOR_BG,         pos, 1)


# ─────────────────────────────────────────
# FOOD
# ─────────────────────────────────────────
class Food:
    def __init__(self):
        self.position = (0, 0)

    def spawn(self, occupied):
        """Place food on a cell not in `occupied` (snake body + barriers)."""
        all_cells   = {(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
        empty_cells = list(all_cells - set(occupied))
        self.position = random.choice(empty_cells)

    def draw(self, surface):
        gx, gy = self.position
        cx = gx * CELL_SIZE + CELL_SIZE // 2
        cy = gy * CELL_SIZE + CELL_SIZE // 2 + PANEL_H
        r  = CELL_SIZE // 2 - 4
        pygame.draw.circle(surface, COLOR_FOOD, (cx, cy), r)
        pygame.draw.circle(surface, COLOR_FOOD_GLOW,
                           (cx - r // 3, cy - r // 3), r // 4)


# ─────────────────────────────────────────
# BARRIERS
# ─────────────────────────────────────────
class Barriers:
    def __init__(self, count, snake_body):
        self.cells = self._generate(count, snake_body)

    def _generate(self, count, snake_body):
        """
        Place `count` barrier cells randomly, avoiding:
          - The snake's starting body
          - A safe 5-cell clear zone around the snake head
        Barriers are placed in small 2–3 cell clusters for a natural look.
        """
        if count == 0:
            return set()

        hx, hy = snake_body[0]
        # Safe zone: 5-cell radius around the starting head
        safe = {
            (hx + dx, hy + dy)
            for dx in range(-5, 6)
            for dy in range(-5, 6)
        } | set(snake_body)

        available = [
            (x, y)
            for x in range(GRID_SIZE)
            for y in range(GRID_SIZE)
            if (x, y) not in safe
        ]
        random.shuffle(available)

        barriers = set()
        placed   = 0
        for (bx, by) in available:
            if placed >= count:
                break
            if (bx, by) in barriers:
                continue
            # Place a small horizontal cluster (1–3 cells)
            cluster_len = random.randint(1, 3)
            for i in range(cluster_len):
                cell = (bx + i, by)
                if (
                    0 <= cell[0] < GRID_SIZE
                    and cell not in safe
                    and placed < count
                ):
                    barriers.add(cell)
                    placed += 1

        return barriers

    def check_collision(self, pos):
        return pos in self.cells

    def draw(self, surface):
        for (gx, gy) in self.cells:
            pad  = 2
            rect = pygame.Rect(
                gx * CELL_SIZE + pad,
                gy * CELL_SIZE + pad + PANEL_H,
                CELL_SIZE - pad * 2,
                CELL_SIZE - pad * 2,
            )
            pygame.draw.rect(surface, COLOR_BARRIER, rect, border_radius=4)
            # Thin highlight on top edge for a brick effect
            pygame.draw.line(
                surface, COLOR_BARRIER_H,
                (rect.left + 3,  rect.top + 2),
                (rect.right - 3, rect.top + 2),
                1,
            )


# ─────────────────────────────────────────
# GAME
# ─────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Game")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock  = pygame.time.Clock()

        self.font_sm = pygame.font.SysFont("Segoe UI", 16)
        self.font_md = pygame.font.SysFont("Segoe UI", 22)
        self.font_lg = pygame.font.SysFont("Segoe UI", 42, bold=True)
        self.font_xl = pygame.font.SysFont("Segoe UI", 64, bold=True)

        # High scores per difficulty
        self.high_scores = {d: 0 for d in DIFFICULTY_ORDER}

        # Menu cursor
        self.selected = 0   # index into DIFFICULTY_ORDER

        self.state = STATE_MENU
        self._start_game()  # pre-init objects (won't show until state changes)

    # ─────────────────────────────────────────
    def _start_game(self):
        """Initialise a new round with the currently selected difficulty."""
        cfg = DIFFICULTIES[DIFFICULTY_ORDER[self.selected]]
        self.snake       = Snake()
        self.food        = Food()
        self.barriers    = Barriers(cfg["barriers"], self.snake.body)
        self.score       = 0
        self.foods_eaten = 0
        self.fps          = cfg["fps_start"]
        self.barrier_flash = 0   # frames remaining for red flash effect
        occupied = set(self.snake.body) | self.barriers.cells
        self.food.spawn(occupied)

    def _current_cfg(self):
        return DIFFICULTIES[DIFFICULTY_ORDER[self.selected]]

    def _recalc_speed(self):
        cfg = self._current_cfg()
        self.fps = min(cfg["fps_start"] + self.foods_eaten // cfg["speed_step"],
                       cfg["fps_max"])

    def _trigger_gameover(self):
        diff = DIFFICULTY_ORDER[self.selected]
        if self.score > self.high_scores[diff]:
            self.high_scores[diff] = self.score
        self.state = STATE_GAMEOVER

    def _level(self):
        return (self.fps - self._current_cfg()["fps_start"]) + 1

    # ─────────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────────
    def run(self):
        while True:
            self._handle_events()
            if self.state == STATE_PLAYING:
                self._update()
            self._draw()
            self.clock.tick(self.fps)

    # ─────────────────────────────────────────
    # INPUT
    # ─────────────────────────────────────────
    def _handle_events(self):
        direction_map = {
            pygame.K_UP:    (0, -1),
            pygame.K_DOWN:  (0,  1),
            pygame.K_LEFT:  (-1, 0),
            pygame.K_RIGHT: (1,  0),
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # ── MENU ──────────────────────────────
                if self.state == STATE_MENU:
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        self.selected = (self.selected - 1) % len(DIFFICULTY_ORDER)
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.selected = (self.selected + 1) % len(DIFFICULTY_ORDER)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._start_game()
                        self.state = STATE_PLAYING

                # ── PLAYING ───────────────────────────
                elif self.state == STATE_PLAYING:
                    if event.key in direction_map:
                        self.snake.set_direction(direction_map[event.key])

                # ── GAME OVER ─────────────────────────
                elif self.state == STATE_GAMEOVER:
                    if event.key == pygame.K_r:
                        self._start_game()
                        self.state = STATE_PLAYING
                    elif event.key == pygame.K_m:
                        self.state = STATE_MENU

    # ─────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────
    def _update(self):
        hx, hy   = self.snake.head()
        dx, dy   = self.snake.next_dir
        next_pos = (hx + dx, hy + dy)
        eating   = (next_pos == self.food.position)

        self.snake.move(grow=eating)

        # Wall and self collision → instant death
        if self.snake.check_wall_collision() or self.snake.check_self_collision():
            self._trigger_gameover()
            return

        # Barrier collision → speed penalty (death if already at minimum)
        if self.barriers.check_collision(self.snake.head()):
            cfg = self._current_cfg()
            if self.fps <= cfg["fps_start"]:
                # Already at minimum speed — can't slow down further, so die
                self._trigger_gameover()
                return
            else:
                # Slow down by 1 FPS as a penalty
                self.fps -= 1
                self.foods_eaten = max(
                    0,
                    (self.fps - cfg["fps_start"]) * cfg["speed_step"]
                )
                self.barrier_flash = 6   # show red flash for 6 frames

        if eating:
            self.score       += 10
            self.foods_eaten += 1
            self._recalc_speed()
            occupied = set(self.snake.body) | self.barriers.cells
            self.food.spawn(occupied)

    # ─────────────────────────────────────────
    # DRAW
    # ─────────────────────────────────────────
    def _draw(self):
        self.screen.fill(COLOR_BG)
        self._draw_grid()

        if self.state == STATE_MENU:
            self._draw_menu()
        else:
            self.barriers.draw(self.screen)
            self.food.draw(self.screen)
            self.snake.draw(self.screen)
            if self.state == STATE_GAMEOVER:
                self._draw_gameover_overlay()

        self._draw_panel()
        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID,
                             (x, PANEL_H), (x, WINDOW_HEIGHT))
        for y in range(PANEL_H, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID,
                             (0, y), (WINDOW_WIDTH, y))

    def _draw_panel(self):
        pygame.draw.rect(self.screen, COLOR_PANEL,
                         pygame.Rect(0, 0, WINDOW_WIDTH, PANEL_H))

        # Red flash when barrier hit
        if self.barrier_flash > 0:
            flash_surf = pygame.Surface((WINDOW_WIDTH, PANEL_H), pygame.SRCALPHA)
            alpha = int(120 * self.barrier_flash / 6)
            flash_surf.fill((220, 50, 50, alpha))
            self.screen.blit(flash_surf, (0, 0))
            self.barrier_flash -= 1

        pygame.draw.line(self.screen, (40, 40, 80),
                         (0, PANEL_H - 1), (WINDOW_WIDTH, PANEL_H - 1))

        diff     = DIFFICULTY_ORDER[self.selected]
        cfg      = DIFFICULTIES[diff]
        d_color  = cfg["label_color"]

        # Difficulty badge (left)
        d_surf = self.font_sm.render(diff, True, d_color)
        self.screen.blit(d_surf, (14, PANEL_H // 2 - d_surf.get_height() // 2))

        # Score (centre-left)
        sc = self.font_md.render(f"Score  {self.score}", True, COLOR_TEAL)
        self.screen.blit(sc, (60, PANEL_H // 2 - sc.get_height() // 2))

        # Level (centre)
        if self.state == STATE_PLAYING:
            lv = self.font_sm.render(f"Lv {self._level()}", True, COLOR_DIM)
            self.screen.blit(lv, (WINDOW_WIDTH // 2 - lv.get_width() // 2,
                                   PANEL_H // 2 - lv.get_height() // 2))

        # High score (right)
        hs_val   = self.high_scores[diff]
        hs_color = COLOR_GOLD if (self.score >= hs_val and self.score > 0) else COLOR_DIM
        hs = self.font_md.render(f"Best  {hs_val}", True, hs_color)
        self.screen.blit(hs, (WINDOW_WIDTH - hs.get_width() - 14,
                               PANEL_H // 2 - hs.get_height() // 2))

    # ── MENU SCREEN ───────────────────────────────────────────────────────────
    def _draw_menu(self):
        cx = WINDOW_WIDTH  // 2
        cy = WINDOW_HEIGHT // 2

        # Title
        title = self.font_xl.render("SNAKE", True, COLOR_TEAL)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 130)))

        # Difficulty cards
        card_w, card_h = 140, 110
        gap            = 20
        total_w        = 3 * card_w + 2 * gap
        start_x        = cx - total_w // 2

        for i, diff in enumerate(DIFFICULTY_ORDER):
            cfg    = DIFFICULTIES[diff]
            col    = cfg["label_color"]
            x      = start_x + i * (card_w + gap)
            y      = cy - 40
            is_sel = (i == self.selected)

            # Card background
            bg_color = (30, 30, 60) if is_sel else (20, 20, 45)
            border   = col if is_sel else (50, 50, 80)
            rect     = pygame.Rect(x, y, card_w, card_h)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(self.screen, border,   rect, 2, border_radius=10)

            # Difficulty name
            name_s = self.font_md.render(diff, True, col)
            self.screen.blit(name_s, name_s.get_rect(center=(x + card_w // 2,
                                                               y + 24)))

            # Speed info
            spd = self.font_sm.render(
                f"Speed  {cfg['fps_start']}→{cfg['fps_max']}", True, COLOR_DIM)
            self.screen.blit(spd, spd.get_rect(center=(x + card_w // 2, y + 52)))

            # Barriers info
            bar_text = "No barriers" if cfg["barriers"] == 0 else f"{cfg['barriers']} barriers"
            bar_s    = self.font_sm.render(bar_text, True, COLOR_DIM)
            self.screen.blit(bar_s, bar_s.get_rect(center=(x + card_w // 2, y + 72)))

            # Best score for this difficulty
            hs     = self.high_scores[diff]
            hs_str = f"Best: {hs}" if hs > 0 else "Best: –"
            hs_s   = self.font_sm.render(hs_str, True, COLOR_GOLD if hs > 0 else COLOR_DIM)
            self.screen.blit(hs_s, hs_s.get_rect(center=(x + card_w // 2, y + 92)))

        # Navigation hint
        nav = self.font_sm.render(
            "← → to choose     Enter or Space to start", True, COLOR_DIM)
        self.screen.blit(nav, nav.get_rect(center=(cx, cy + 100)))

    # ── GAME OVER OVERLAY ─────────────────────────────────────────────────────
    def _draw_gameover_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH  // 2
        cy = WINDOW_HEIGHT // 2

        go = self.font_lg.render("GAME OVER", True, (220, 80, 80))
        self.screen.blit(go, go.get_rect(center=(cx, cy - 80)))

        diff   = DIFFICULTY_ORDER[self.selected]
        hs_val = self.high_scores[diff]

        sc = self.font_md.render(f"Score:  {self.score}", True, COLOR_TEXT)
        self.screen.blit(sc, sc.get_rect(center=(cx, cy - 20)))

        if self.score == hs_val and self.score > 0:
            badge = self.font_md.render("★  New High Score!", True, COLOR_GOLD)
            self.screen.blit(badge, badge.get_rect(center=(cx, cy + 18)))
        elif hs_val > 0:
            hs = self.font_sm.render(f"Best:  {hs_val}", True, COLOR_DIM)
            self.screen.blit(hs, hs.get_rect(center=(cx, cy + 18)))

        r_surf = self.font_md.render("R  – play again", True, COLOR_TEAL)
        m_surf = self.font_md.render("M  – main menu", True, COLOR_DIM)
        self.screen.blit(r_surf, r_surf.get_rect(center=(cx, cy + 65)))
        self.screen.blit(m_surf, m_surf.get_rect(center=(cx, cy + 95)))


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
