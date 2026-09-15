"""
Modern Python Snake Game with Pygame.
Features:
- Satisfying & eye-friendly aesthetics: soft twilight palette, subtle dot grid,
  smooth flowing tapered snake body, rounded capsule connections, and glossy expressive eyes.
- Fixed Game Modes: Choose Manual Human Mode or Smart AI Autopilot at start.
- Interactive Cheats:
  - [Q] Key: Spawn extra food on the board (multi-food support with smart AI targeting).
  - [E] Key: Bomb snake tail (reduce snake length with explosion burst and sound effect).
- Procedural 8-bit sound effects (built-in, zero external assets).
- Dual food mechanics: Standard ruby apples + Timed golden bonus stars.
- Floating text popups (+10, BOMB! -3, +FOOD).
- Persistent high score tracking.
"""

import json
import math
import os
import random
import sys
import pygame
from sound_effects import SoundManager
from snake_ai import SnakeAI

# ---------------------------------------------------------
# GAME MODES
# ---------------------------------------------------------
MODE_HUMAN = "HUMAN"
MODE_AI = "AI"

# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------
CELL_SIZE = 25
GRID_WIDTH = 30
GRID_HEIGHT = 24
HEADER_HEIGHT = 70

WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH                    # 750 px
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT + HEADER_HEIGHT  # 670 px
FPS = 60

# Palette (Curated soft twilight & modern neon arcade)
COLOR_BG = (13, 19, 29)
COLOR_HEADER = (18, 25, 38)
COLOR_HEADER_BORDER = (35, 48, 68)
COLOR_GRID_DOT = (30, 42, 60)

COLOR_SNAKE_HEAD = (0, 245, 155)
COLOR_SNAKE_BODY_START = (0, 230, 140)
COLOR_SNAKE_BODY_MID = (0, 180, 220)
COLOR_SNAKE_BODY_END = (85, 115, 235)
COLOR_SNAKE_EYE = (255, 255, 255)
COLOR_SNAKE_PUPIL = (12, 18, 28)

COLOR_FOOD = (255, 65, 105)
COLOR_FOOD_GLOW = (255, 65, 105, 55)
COLOR_LEAF = (70, 225, 120)

COLOR_BONUS = (255, 205, 30)
COLOR_BONUS_GLOW = (255, 215, 0, 75)

COLOR_TEXT_PRIMARY = (240, 245, 255)
COLOR_TEXT_SECONDARY = (135, 155, 180)
COLOR_ACCENT_GOLD = (255, 210, 50)
COLOR_ACCENT_CYAN = (0, 215, 255)

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")

# Directions (dx, dy)
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

OPPOSITES = {
    DIR_UP: DIR_DOWN,
    DIR_DOWN: DIR_UP,
    DIR_LEFT: DIR_RIGHT,
    DIR_RIGHT: DIR_LEFT,
}


# ---------------------------------------------------------
# FLOATING TEXT POPUP SYSTEM
# ---------------------------------------------------------
class FloatingText:
    def __init__(self, text: str, x: float, y: float, color: tuple[int, int, int]):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.alpha = 255
        self.life = 0.9  # duration in seconds
        self.total_life = 0.9
        self.vy = -1.5

    def update(self, dt: float) -> bool:
        self.y += self.vy
        self.life -= dt
        self.alpha = max(0, int(255 * (self.life / self.total_life)))
        return self.life > 0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        if self.alpha <= 0:
            return
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(self.alpha)
        surface.blit(surf, (self.x - surf.get_width() // 2, self.y))


# ---------------------------------------------------------
# PARTICLE SYSTEM
# ---------------------------------------------------------
class Particle:
    def __init__(self, x: float, y: float, color: tuple[int, ...], speed_mult: float = 1.0):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.5) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(2.0, 4.5)
        self.alpha = 255
        self.fade_speed = random.uniform(6.0, 11.0)

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.93
        self.vy *= 0.93
        self.alpha -= self.fade_speed
        self.radius = max(0.5, self.radius - 0.04)
        return self.alpha > 0

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        draw_color = (*self.color[:3], int(self.alpha))
        p_surf = pygame.Surface((int(self.radius * 2) + 2, int(self.radius * 2) + 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, draw_color, (int(self.radius) + 1, int(self.radius) + 1), int(self.radius))
        surface.blit(p_surf, (self.x - self.radius, self.y - self.radius))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def emit(self, x: float, y: float, color: tuple[int, ...], count: int = 15, speed_mult: float = 1.0):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed_mult))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)


# ---------------------------------------------------------
# FOOD CLASS (MULTI-FOOD & GOLDEN STAR SUPPORT)
# ---------------------------------------------------------
class Food:
    def __init__(self):
        self.positions: list[tuple[int, int]] = []
        # Bonus Food (glowing star with timer)
        self.bonus_active = False
        self.bonus_pos = (0, 0)
        self.bonus_timer = 0.0
        self.bonus_max_timer = 8.0  # seconds
        self.eaten_counter = 0

    def respawn(self, occupied_positions: list[tuple[int, int]]):
        """Resets food to exactly 1 regular food item."""
        self.positions.clear()
        self.add_food(occupied_positions)

    def add_food(self, occupied_positions: list[tuple[int, int]]) -> tuple[int, int] | None:
        """Spawns an extra food on an unoccupied tile (for Q key or initial spawn)."""
        blocked = set(occupied_positions).union(self.positions)
        if self.bonus_active:
            blocked.add(self.bonus_pos)

        available = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
        ]
        if available:
            new_pos = random.choice(available)
            self.positions.append(new_pos)
            return new_pos
        return None

    def remove_food(self, pos: tuple[int, int], occupied_positions: list[tuple[int, int]]):
        """Removes the eaten food. If no food remains, auto-spawns 1 to ensure at least 1 apple exists."""
        if pos in self.positions:
            self.positions.remove(pos)
        self.eaten_counter += 1

        # Every 5 foods eaten, spawn a bonus star
        if self.eaten_counter % 5 == 0 and not self.bonus_active:
            self.spawn_bonus(occupied_positions)

        # Ensure at least 1 food is always available
        if not self.positions:
            self.add_food(occupied_positions)

    def spawn_bonus(self, occupied_positions: list[tuple[int, int]]):
        blocked = set(occupied_positions).union(self.positions)
        available = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in blocked
        ]
        if available:
            self.bonus_pos = random.choice(available)
            self.bonus_active = True
            self.bonus_timer = self.bonus_max_timer

    def update_bonus(self, dt: float):
        if self.bonus_active:
            self.bonus_timer -= dt
            if self.bonus_timer <= 0:
                self.bonus_active = False

    def draw(self, surface: pygame.Surface, time_pulse: float):
        # Draw all active regular apples
        for pos in self.positions:
            fx = pos[0] * CELL_SIZE + CELL_SIZE // 2
            fy = HEADER_HEIGHT + pos[1] * CELL_SIZE + CELL_SIZE // 2
            pulse = math.sin(time_pulse * 4.0) * 1.2
            radius = int(CELL_SIZE * 0.38 + pulse)

            # Soft radial outer glow
            glow_radius = radius + 6
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, COLOR_FOOD_GLOW, (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (fx - glow_radius, fy - glow_radius))

            # Plump apple body
            pygame.draw.circle(surface, COLOR_FOOD, (fx, fy), radius)
            # Apple glossy specular shine
            pygame.draw.circle(surface, (255, 175, 195), (fx - radius // 3, fy - radius // 3), max(2, radius // 4))
            # Little green leaf
            leaf_rect = pygame.Rect(fx - 1, fy - radius - 4, 6, 5)
            pygame.draw.ellipse(surface, COLOR_LEAF, leaf_rect)

        # Draw Golden Bonus Star if active
        if self.bonus_active:
            bx = self.bonus_pos[0] * CELL_SIZE + CELL_SIZE // 2
            by = HEADER_HEIGHT + self.bonus_pos[1] * CELL_SIZE + CELL_SIZE // 2
            b_pulse = math.sin(time_pulse * 8.0) * 1.8
            b_radius = int(CELL_SIZE * 0.44 + b_pulse)

            # Golden halo
            b_glow = pygame.Surface(((b_radius + 9) * 2, (b_radius + 9) * 2), pygame.SRCALPHA)
            pygame.draw.circle(b_glow, COLOR_BONUS_GLOW, (b_radius + 9, b_radius + 9), b_radius + 9)
            surface.blit(b_glow, (bx - b_radius - 9, by - b_radius - 9))

            # Sparkling 4-point Diamond Star
            pts = [
                (bx, by - b_radius),
                (bx + b_radius, by),
                (bx, by + b_radius),
                (bx - b_radius, by),
            ]
            pygame.draw.polygon(surface, COLOR_BONUS, pts)
            inner_pts = [
                (bx, by - b_radius // 2),
                (bx + b_radius // 2, by),
                (bx, by + b_radius // 2),
                (bx - b_radius // 2, by),
            ]
            pygame.draw.polygon(surface, (255, 255, 220), inner_pts)

            # Circular countdown timer ring
            timer_fraction = max(0.0, self.bonus_timer / self.bonus_max_timer)
            ring_rect = pygame.Rect(bx - CELL_SIZE // 2 + 1, by - CELL_SIZE // 2 + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            if timer_fraction > 0.05:
                angle_span = 2 * math.pi * timer_fraction
                pygame.draw.arc(surface, COLOR_BONUS, ring_rect, 0, angle_span, 2)


# ---------------------------------------------------------
# SNAKE CLASS (SATISFYING TAPERED BODY & EXPRESSIVE EYES)
# ---------------------------------------------------------
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        mid_x = GRID_WIDTH // 2
        mid_y = GRID_HEIGHT // 2
        self.body: list[tuple[int, int]] = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y),
        ]
        self.direction = DIR_RIGHT
        self.dir_queue: list[tuple[int, int]] = []
        self.grow_pending = 0

    def queue_direction(self, new_dir: tuple[int, int]):
        last_dir = self.dir_queue[-1] if self.dir_queue else self.direction
        if new_dir != last_dir and new_dir != OPPOSITES.get(last_dir):
            if len(self.dir_queue) < 2:
                self.dir_queue.append(new_dir)

    def move(self) -> tuple[int, int]:
        if self.dir_queue:
            self.direction = self.dir_queue.pop(0)

        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

        return new_head

    def grow(self, amount: int = 1):
        self.grow_pending += amount

    def check_wall_collision(self) -> bool:
        hx, hy = self.body[0]
        return hx < 0 or hx >= GRID_WIDTH or hy < 0 or hy >= GRID_HEIGHT

    def check_self_collision(self) -> bool:
        head = self.body[0]
        return head in self.body[1:]

    def _get_segment_radius(self, idx: int, total: int) -> int:
        """Computes smooth tapering radius from full head to sleek tail."""
        base_r = CELL_SIZE // 2 - 1
        if idx == 0:
            return base_r  # Head is full size
        taper_ratio = idx / max(1, total - 1)
        if taper_ratio > 0.35:
            # Taper last 65% of tail gradually
            tail_prog = (taper_ratio - 0.35) / 0.65
            scale = 1.0 - tail_prog * 0.45  # scales from 1.0 down to 0.55
        else:
            scale = 1.0
        return max(4, int(base_r * scale))

    def _get_segment_color(self, idx: int, total: int) -> tuple[int, int, int]:
        """Smooth multi-stop gradient: Emerald -> Turquoise -> Electric Cyan -> Soft Indigo."""
        ratio = idx / max(1, total - 1)
        if ratio < 0.5:
            sub = ratio / 0.5
            r = int(COLOR_SNAKE_BODY_START[0] * (1 - sub) + COLOR_SNAKE_BODY_MID[0] * sub)
            g = int(COLOR_SNAKE_BODY_START[1] * (1 - sub) + COLOR_SNAKE_BODY_MID[1] * sub)
            b = int(COLOR_SNAKE_BODY_START[2] * (1 - sub) + COLOR_SNAKE_BODY_MID[2] * sub)
        else:
            sub = (ratio - 0.5) / 0.5
            r = int(COLOR_SNAKE_BODY_MID[0] * (1 - sub) + COLOR_SNAKE_BODY_END[0] * sub)
            g = int(COLOR_SNAKE_BODY_MID[1] * (1 - sub) + COLOR_SNAKE_BODY_END[1] * sub)
            b = int(COLOR_SNAKE_BODY_MID[2] * (1 - sub) + COLOR_SNAKE_BODY_END[2] * sub)
        return (r, g, b)

    def draw(self, surface: pygame.Surface):
        total_segs = len(self.body)

        # 1. Draw smooth continuous capsule connections between segments (from tail to head)
        for i in reversed(range(total_segs - 1)):
            c1_x = self.body[i][0] * CELL_SIZE + CELL_SIZE // 2
            c1_y = HEADER_HEIGHT + self.body[i][1] * CELL_SIZE + CELL_SIZE // 2
            c2_x = self.body[i + 1][0] * CELL_SIZE + CELL_SIZE // 2
            c2_y = HEADER_HEIGHT + self.body[i + 1][1] * CELL_SIZE + CELL_SIZE // 2

            r1 = self._get_segment_radius(i, total_segs)
            r2 = self._get_segment_radius(i + 1, total_segs)
            avg_r = (r1 + r2) // 2
            seg_color = self._get_segment_color(i, total_segs)

            # Capsule thick bridge
            pygame.draw.line(surface, seg_color, (c1_x, c1_y), (c2_x, c2_y), width=avg_r * 2)

        # 2. Draw rounded joints for each segment
        for i in reversed(range(total_segs)):
            cx = self.body[i][0] * CELL_SIZE + CELL_SIZE // 2
            cy = HEADER_HEIGHT + self.body[i][1] * CELL_SIZE + CELL_SIZE // 2
            r = self._get_segment_radius(i, total_segs)
            seg_color = COLOR_SNAKE_HEAD if i == 0 else self._get_segment_color(i, total_segs)

            # Head soft ambient aura
            if i == 0:
                glow_r = r + 5
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (0, 255, 160, 60), (glow_r, glow_r), glow_r)
                surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

            pygame.draw.circle(surface, seg_color, (cx, cy), r)

            # 3. Draw Expressive Animated Eyes on Head
            if i == 0:
                self._draw_glossy_eyes(surface, cx, cy)

    def _draw_glossy_eyes(self, surface: pygame.Surface, cx: int, cy: int):
        dx, dy = self.direction

        # Eye positioning perpendicular to movement vector
        eye_dist = 5
        forward_dist = 4
        eye_r = 4
        pupil_r = 2
        shine_r = 1

        if dx != 0:
            e1 = (cx + dx * forward_dist, cy - eye_dist)
            e2 = (cx + dx * forward_dist, cy + eye_dist)
            p1 = (e1[0] + dx * 1, e1[1])
            p2 = (e2[0] + dx * 1, e2[1])
            s1 = (p1[0] - dx * 1, p1[1] - 1)
            s2 = (p2[0] - dx * 1, p2[1] - 1)
        else:
            e1 = (cx - eye_dist, cy + dy * forward_dist)
            e2 = (cx + eye_dist, cy + dy * forward_dist)
            p1 = (e1[0], e1[1] + dy * 1)
            p2 = (e2[0], e2[1] + dy * 1)
            s1 = (p1[0] - 1, p1[1] - dy * 1)
            s2 = (p2[0] - 1, p2[1] - dy * 1)

        # Draw whites
        pygame.draw.circle(surface, COLOR_SNAKE_EYE, e1, eye_r)
        pygame.draw.circle(surface, COLOR_SNAKE_EYE, e2, eye_r)
        # Draw dark pupils
        pygame.draw.circle(surface, COLOR_SNAKE_PUPIL, p1, pupil_r)
        pygame.draw.circle(surface, COLOR_SNAKE_PUPIL, p2, pupil_r)
        # Glossy specular shine dots
        pygame.draw.circle(surface, (255, 255, 255), s1, shine_r)
        pygame.draw.circle(surface, (255, 255, 255), s2, shine_r)


# ---------------------------------------------------------
# GAME MANAGER
# ---------------------------------------------------------
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAMEOVER = 3

class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Neon Snake 🐍 Arcade")

        # Display setup with responsive scaling for desktop and mobile
        self.is_android = hasattr(sys, "getandroidapilevel") or "ANDROID_ARGUMENT" in os.environ
        if self.is_android:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)

        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Trebuchet MS", 46, bold=True)
        self.font_header = pygame.font.SysFont("Trebuchet MS", 22, bold=True)
        self.font_body = pygame.font.SysFont("Verdana", 15)
        self.font_small = pygame.font.SysFont("Verdana", 12)
        self.font_popup = pygame.font.SysFont("Trebuchet MS", 16, bold=True)

        # Sounds
        self.sound = SoundManager(enabled=True)

        # Entities
        self.snake = Snake()
        self.food = Food()
        self.particles = ParticleSystem()
        self.floating_texts: list[FloatingText] = []

        # AI & Fixed Mode
        self.mode = MODE_HUMAN
        self.ai = SnakeAI(GRID_WIDTH, GRID_HEIGHT)

        # State & Stats
        self.state = STATE_MENU
        self.score = 0
        self.fruits_eaten = 0
        self.bonus_eaten = 0
        self.high_score = 0
        self.wins = 0
        self.losses = 0
        self.total_games = 0
        self.human_wins = 0
        self.human_losses = 0
        self.ai_wins = 0
        self.ai_losses = 0
        self.win_target = 500
        self.is_new_high_score = False
        self.is_round_win = False
        self.load_stats()

        # Mobile & Touch Controls (Swipe & On-Screen Buttons)
        self.touch_start_pos: tuple[int, int] | None = None
        self.dpad_cx = 85
        self.dpad_cy = WINDOW_HEIGHT - 85
        self.btn_up_rect = pygame.Rect(self.dpad_cx - 24, self.dpad_cy - 70, 48, 48)
        self.btn_down_rect = pygame.Rect(self.dpad_cx - 24, self.dpad_cy + 22, 48, 48)
        self.btn_left_rect = pygame.Rect(self.dpad_cx - 70, self.dpad_cy - 24, 48, 48)
        self.btn_right_rect = pygame.Rect(self.dpad_cx + 22, self.dpad_cy - 24, 48, 48)
        self.btn_food_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 75, 60, 60)
        self.btn_bomb_rect = pygame.Rect(WINDOW_WIDTH - 75, WINDOW_HEIGHT - 75, 60, 60)
        self.btn_pause_rect = pygame.Rect(WINDOW_WIDTH - 140, 32, 130, 32)
        self.btn_mute_rect = pygame.Rect(WINDOW_WIDTH - 140, 8, 130, 24)
        self.menu_card1_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 205, 235, 145)
        self.menu_card2_rect = pygame.Rect(WINDOW_WIDTH // 2 + 15, 205, 235, 145)

        # Speed & Timing Control
        self.base_speed = 20.0
        self.speed = 20.0
        self.move_timer = 0.0
        self.time_alive = 0.0
        self.game_over_timer = 0.0

        self.running = True

    def load_stats(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.high_score = int(data.get("high_score", 0))
                    self.wins = int(data.get("wins", 0))
                    self.losses = int(data.get("losses", 0))
                    self.total_games = int(data.get("total_games", self.wins + self.losses))
                    self.human_wins = int(data.get("human_wins", 0))
                    self.human_losses = int(data.get("human_losses", 0))
                    self.ai_wins = int(data.get("ai_wins", 0))
                    self.ai_losses = int(data.get("ai_losses", 0))
                    self.win_target = int(data.get("win_target", 500))
                    return
            except Exception as err:
                print(f"Error loading stats: {err}")
        self.high_score = 0
        self.wins = 0
        self.losses = 0
        self.total_games = 0
        self.human_wins = 0
        self.human_losses = 0
        self.ai_wins = 0
        self.ai_losses = 0
        self.win_target = 500

    def save_stats(self):
        try:
            data = {
                "high_score": self.high_score,
                "wins": self.wins,
                "losses": self.losses,
                "total_games": self.total_games,
                "human_wins": self.human_wins,
                "human_losses": self.human_losses,
                "ai_wins": self.ai_wins,
                "ai_losses": self.ai_losses,
                "win_target": self.win_target,
            }
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as err:
            print(f"Could not save stats: {err}")

    def start_new_game(self, mode: str = None):
        """Starts a new fixed-mode game."""
        if mode:
            self.mode = mode
        self.snake.reset()
        self.food = Food()
        self.food.respawn(self.snake.body)
        self.particles = ParticleSystem()
        self.floating_texts.clear()
        self.score = 0
        self.fruits_eaten = 0
        self.bonus_eaten = 0
        self.speed = 20.0
        self.move_timer = 0.0
        self.time_alive = 0.0
        self.game_over_timer = 0.0
        self.is_new_high_score = False
        self.is_round_win = False
        self.state = STATE_PLAYING
        self.sound.play_click()

    def spawn_extra_food_action(self):
        """Action for [Q] key: Spawns extra food on board with sound and visual feedback."""
        new_pos = self.food.add_food(self.snake.body)
        if new_pos:
            self.sound.play_spawn()
            px = new_pos[0] * CELL_SIZE + CELL_SIZE // 2
            py = HEADER_HEIGHT + new_pos[1] * CELL_SIZE + CELL_SIZE // 2
            self.particles.emit(px, py, COLOR_FOOD, count=10, speed_mult=1.0)
            self.floating_texts.append(FloatingText("+1 🍎 FOOD", px, py - 18, COLOR_FOOD))

    def bomb_snake_action(self):
        """Action for [E] key: Bombs the snake, trimming segments down to minimum length of 3."""
        if len(self.snake.body) > 3:
            cut_amount = min(3, len(self.snake.body) - 3)
            removed_segs = self.snake.body[-cut_amount:]
            self.snake.body = self.snake.body[:-cut_amount]

            # Emit fiery explosion particles at the removed segments
            for seg in removed_segs:
                sx = seg[0] * CELL_SIZE + CELL_SIZE // 2
                sy = HEADER_HEIGHT + seg[1] * CELL_SIZE + CELL_SIZE // 2
                self.particles.emit(sx, sy, (255, 140, 20), count=14, speed_mult=1.6)
                self.particles.emit(sx, sy, (255, 60, 20), count=8, speed_mult=1.2)

            self.sound.play_bomb()
            hx = self.snake.body[0][0] * CELL_SIZE + CELL_SIZE // 2
            hy = HEADER_HEIGHT + self.snake.body[0][1] * CELL_SIZE + CELL_SIZE // 2
            self.floating_texts.append(FloatingText(f"💥 BOMB! -{cut_amount}", hx, hy - 20, COLOR_BONUS))
        else:
            # Snake is already at minimum size
            self.sound.play_click()
            hx = self.snake.body[0][0] * CELL_SIZE + CELL_SIZE // 2
            hy = HEADER_HEIGHT + self.snake.body[0][1] * CELL_SIZE + CELL_SIZE // 2
            self.floating_texts.append(FloatingText("MIN SIZE (3)!", hx, hy - 20, COLOR_TEXT_SECONDARY))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Touch / Mobile Tap & Click Handling
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                if event.type == pygame.FINGERDOWN:
                    win_w, win_h = self.window.get_size()
                    raw_x = int(event.x * win_w)
                    raw_y = int(event.y * win_h)
                else:
                    if event.button != 1:
                        continue
                    raw_x, raw_y = event.pos

                # Transform raw window coordinates to virtual 750x670 coordinates
                vx = int((raw_x - self.offset_x) / max(0.001, self.scale))
                vy = int((raw_y - self.offset_y) / max(0.001, self.scale))
                mpos = (max(0, min(WINDOW_WIDTH - 1, vx)), max(0, min(WINDOW_HEIGHT - 1, vy)))
                self.touch_start_pos = mpos

                # Menu card selection via touch/tap
                if self.state == STATE_MENU:
                    if self.menu_card1_rect.collidepoint(mpos):
                        self.start_new_game(mode=MODE_HUMAN)
                    elif self.menu_card2_rect.collidepoint(mpos):
                        self.start_new_game(mode=MODE_AI)

                elif self.state == STATE_PLAYING:
                    # Header touch buttons: Pause & Mute
                    if self.btn_pause_rect.collidepoint(mpos):
                        self.state = STATE_PAUSED
                        self.sound.play_click()
                        continue
                    if self.btn_mute_rect.collidepoint(mpos):
                        self.sound.enabled = not self.sound.enabled
                        continue

                    # On-screen action buttons: +Food and Bomb
                    if self.btn_food_rect.collidepoint(mpos):
                        self.spawn_extra_food_action()
                        continue
                    if self.btn_bomb_rect.collidepoint(mpos):
                        self.bomb_snake_action()
                        continue

                    # On-screen virtual D-Pad buttons
                    if self.mode == MODE_HUMAN:
                        if self.btn_up_rect.collidepoint(mpos):
                            self.snake.queue_direction(DIR_UP)
                        elif self.btn_down_rect.collidepoint(mpos):
                            self.snake.queue_direction(DIR_DOWN)
                        elif self.btn_left_rect.collidepoint(mpos):
                            self.snake.queue_direction(DIR_LEFT)
                        elif self.btn_right_rect.collidepoint(mpos):
                            self.snake.queue_direction(DIR_RIGHT)

                elif self.state == STATE_PAUSED:
                    # Tap anywhere to resume
                    self.state = STATE_PLAYING
                    self.sound.play_click()

                elif self.state == STATE_GAMEOVER:
                    # Tap anywhere to restart immediately
                    self.start_new_game(mode=self.mode)

            # Touch / Mobile Swipe Gesture Handling
            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                if self.touch_start_pos is not None:
                    if event.type == pygame.FINGERUP:
                        win_w, win_h = self.window.get_size()
                        raw_x = int(event.x * win_w)
                        raw_y = int(event.y * win_h)
                    else:
                        raw_x, raw_y = event.pos

                    vx = int((raw_x - self.offset_x) / max(0.001, self.scale))
                    vy = int((raw_y - self.offset_y) / max(0.001, self.scale))
                    end_pos = (max(0, min(WINDOW_WIDTH - 1, vx)), max(0, min(WINDOW_HEIGHT - 1, vy)))

                    dx = end_pos[0] - self.touch_start_pos[0]
                    dy = end_pos[1] - self.touch_start_pos[1]
                    dist_sq = dx * dx + dy * dy

                    # Swipe gesture detection (min drag distance 25px)
                    if dist_sq >= 625 and self.state == STATE_PLAYING and self.mode == MODE_HUMAN:
                        if abs(dx) > abs(dy):
                            if dx > 0:
                                self.snake.queue_direction(DIR_RIGHT)
                            else:
                                self.snake.queue_direction(DIR_LEFT)
                        else:
                            if dy > 0:
                                self.snake.queue_direction(DIR_DOWN)
                            else:
                                self.snake.queue_direction(DIR_UP)

                    self.touch_start_pos = None

            # Physical Keyboard Controls (Desktop & Bluetooth Keyboards)
            elif event.type == pygame.KEYDOWN:
                # Global sound toggle (M)
                if event.key == pygame.K_m:
                    self.sound.enabled = not self.sound.enabled
                    continue

                # State handling
                if self.state == STATE_MENU:
                    if event.key in (pygame.K_1, pygame.K_SPACE, pygame.K_RETURN):
                        self.start_new_game(mode=MODE_HUMAN)
                    elif event.key in (pygame.K_2, pygame.K_a):
                        self.start_new_game(mode=MODE_AI)
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == STATE_PLAYING:
                    # [Q] Spawn extra food
                    if event.key == pygame.K_q:
                        self.spawn_extra_food_action()
                        continue

                    # [E] Bomb snake tail
                    if event.key == pygame.K_e:
                        self.bomb_snake_action()
                        continue

                    # Direction controls (Only active in Manual Human Mode)
                    if self.mode == MODE_HUMAN:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.snake.queue_direction(DIR_UP)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.snake.queue_direction(DIR_DOWN)
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.snake.queue_direction(DIR_LEFT)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.snake.queue_direction(DIR_RIGHT)

                    # Pause & Menu
                    if event.key in (pygame.K_SPACE, pygame.K_p):
                        self.state = STATE_PAUSED
                        self.sound.play_click()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

                elif self.state == STATE_PAUSED:
                    if event.key in (pygame.K_SPACE, pygame.K_p):
                        self.state = STATE_PLAYING
                        self.sound.play_click()
                    elif event.key == pygame.K_r:
                        self.start_new_game(mode=self.mode)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

                elif self.state == STATE_GAMEOVER:
                    if event.key in (pygame.K_1, pygame.K_SPACE, pygame.K_RETURN):
                        self.start_new_game(mode=MODE_HUMAN)
                    elif event.key in (pygame.K_2, pygame.K_a):
                        self.start_new_game(mode=MODE_AI)
                    elif event.key == pygame.K_r:
                        self.start_new_game(mode=self.mode)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

    def trigger_game_over(self):
        self.state = STATE_GAMEOVER
        self.game_over_timer = 5.0

        # Check for High Score Record
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

        # Determine Win vs Lose (Milestone Target reached OR New High Score Record)
        self.is_round_win = (self.score >= self.win_target) or self.is_new_high_score

        # Record Win / Loss
        self.total_games += 1
        if self.is_round_win:
            self.wins += 1
            if self.mode == MODE_HUMAN:
                self.human_wins += 1
            else:
                self.ai_wins += 1
            self.sound.play_victory()
        else:
            self.losses += 1
            if self.mode == MODE_HUMAN:
                self.human_losses += 1
            else:
                self.ai_losses += 1
            self.sound.play_game_over()

        # Save stats to disk
        self.save_stats()

        # Emit death dispersion particles around snake head
        hx, hy = self.snake.body[0]
        px = hx * CELL_SIZE + CELL_SIZE // 2
        py = HEADER_HEIGHT + hy * CELL_SIZE + CELL_SIZE // 2
        particle_col = COLOR_SNAKE_HEAD if self.is_round_win else (255, 70, 80)
        self.particles.emit(px, py, particle_col, count=35, speed_mult=1.8)
        self.particles.emit(px, py, COLOR_FOOD, count=15, speed_mult=1.5)

    def update(self, dt: float):
        self.time_alive += dt
        self.particles.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

        # Auto-restart countdown after game over (5 seconds)
        if self.state == STATE_GAMEOVER:
            self.game_over_timer -= dt
            if self.game_over_timer <= 0:
                self.start_new_game(mode=self.mode)
            return

        if self.state != STATE_PLAYING:
            return

        self.food.update_bonus(dt)

        # Speed remains fixed at 20.0 steps/second throughout the run
        self.speed = 20.0

        self.move_timer += dt
        tick_interval = 1.0 / self.speed

        if self.move_timer >= tick_interval:
            self.move_timer -= tick_interval

            # Autonomous Smart AI decision (if in AI mode)
            if self.mode == MODE_AI:
                ai_dir, _ = self.ai.get_next_move(
                    snake_body=self.snake.body,
                    food_pos=self.food.positions,
                    bonus_pos=self.food.bonus_pos if self.food.bonus_active else None,
                    bonus_active=self.food.bonus_active,
                    bonus_timer=self.food.bonus_timer,
                    current_speed=self.speed,
                    grow_pending=self.snake.grow_pending,
                    fruits_eaten=self.fruits_eaten,
                )
                self.snake.dir_queue.clear()
                self.snake.direction = ai_dir

            new_head = self.snake.move()

            # Check Collisions
            if self.snake.check_wall_collision() or self.snake.check_self_collision():
                self.trigger_game_over()
                return

            # Check any Regular Food eaten
            if new_head in self.food.positions:
                self.score += 10
                self.fruits_eaten += 1
                self.snake.grow(1)
                self.sound.play_eat()

                fx = new_head[0] * CELL_SIZE + CELL_SIZE // 2
                fy = HEADER_HEIGHT + new_head[1] * CELL_SIZE + CELL_SIZE // 2
                self.particles.emit(fx, fy, COLOR_FOOD, count=16)
                self.floating_texts.append(FloatingText("+10", fx, fy - 18, COLOR_FOOD))

                self.food.remove_food(new_head, self.snake.body)

            # Check Golden Bonus Food eaten
            elif self.food.bonus_active and new_head == self.food.bonus_pos:
                bonus_points = 50 + int(self.food.bonus_timer * 5)
                self.score += bonus_points
                self.bonus_eaten += 1
                self.snake.grow(2)
                self.food.bonus_active = False
                self.sound.play_bonus()

                bx = self.food.bonus_pos[0] * CELL_SIZE + CELL_SIZE // 2
                by = HEADER_HEIGHT + self.food.bonus_pos[1] * CELL_SIZE + CELL_SIZE // 2
                self.particles.emit(bx, by, COLOR_BONUS, count=28, speed_mult=1.5)
                self.floating_texts.append(FloatingText(f"+{bonus_points} STAR!", bx, by - 20, COLOR_BONUS))

    def draw_grid_dots(self):
        """Draws subtle, soft intersection dots (easy on eyes, eliminates harsh grid fatigue)."""
        # Outer boundary
        border_rect = pygame.Rect(0, HEADER_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - HEADER_HEIGHT)
        pygame.draw.rect(self.screen, (22, 32, 46), border_rect, width=1)

        # Subtle dots at cell centers
        for col in range(GRID_WIDTH):
            for row in range(GRID_HEIGHT):
                cx = col * CELL_SIZE + CELL_SIZE // 2
                cy = HEADER_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2
                self.screen.set_at((cx, cy), COLOR_GRID_DOT)

    def draw_header(self):
        # Header background & boundary line
        pygame.draw.rect(self.screen, COLOR_HEADER, (0, 0, WINDOW_WIDTH, HEADER_HEIGHT))
        pygame.draw.line(self.screen, COLOR_HEADER_BORDER, (0, HEADER_HEIGHT - 1), (WINDOW_WIDTH, HEADER_HEIGHT - 1), 2)

        # Current Score
        score_lbl = self.font_small.render("SCORE", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(score_lbl, (20, 12))
        score_val = self.font_header.render(str(self.score), True, COLOR_ACCENT_CYAN)
        self.screen.blit(score_val, (20, 32))

        # High Score
        hs_lbl = self.font_small.render("BEST RECORD", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(hs_lbl, (115, 12))
        hs_val = self.font_header.render(str(max(self.score, self.high_score)), True, COLOR_ACCENT_GOLD)
        self.screen.blit(hs_val, (115, 32))

        # Speed indicator (Fixed at 20 steps/sec)
        lvl_lbl = self.font_small.render("FIXED SPEED", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(lvl_lbl, (230, 12))
        lvl_val = self.font_header.render("20 / sec", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(lvl_val, (230, 32))

        # Wins & Losses Record
        rec_lbl = self.font_small.render("RECORD (W/L)", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(rec_lbl, (335, 12))
        w_surf = self.font_header.render(f"{self.wins}W", True, COLOR_SNAKE_HEAD)
        dash_surf = self.font_header.render(" - ", True, COLOR_TEXT_SECONDARY)
        l_surf = self.font_header.render(f"{self.losses}L", True, (255, 80, 90))
        self.screen.blit(w_surf, (335, 32))
        self.screen.blit(dash_surf, (335 + w_surf.get_width(), 32))
        self.screen.blit(l_surf, (335 + w_surf.get_width() + dash_surf.get_width(), 32))

        # In-game interactive hotkey hints ([Q] Food, [E] Bomb)
        q_hint = self.font_small.render("[Q] +Food", True, COLOR_FOOD)
        e_hint = self.font_small.render("[E] Bomb", True, COLOR_BONUS)
        self.screen.blit(q_hint, (460, 18))
        self.screen.blit(e_hint, (460, 38))

        # Bonus Fruit Active Bar (if active)
        if self.food.bonus_active:
            bar_w = 75
            bar_h = 8
            bar_x = 545
            bar_y = 38
            pct = max(0.0, self.food.bonus_timer / self.food.bonus_max_timer)
            b_lbl = self.font_small.render(f"STAR ({self.food.bonus_timer:.1f}s)", True, COLOR_BONUS)
            self.screen.blit(b_lbl, (bar_x, 16))
            pygame.draw.rect(self.screen, (40, 45, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(self.screen, COLOR_BONUS, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)

        # Controls & Audio Mute hint
        snd_txt = "SFX: ON [M]" if self.sound.enabled else "SFX: OFF [M]"
        snd_surf = self.font_small.render(snd_txt, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(snd_surf, (WINDOW_WIDTH - snd_surf.get_width() - 20, 16))

        pause_surf = self.font_small.render("Pause: [SPACE]", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(pause_surf, (WINDOW_WIDTH - pause_surf.get_width() - 20, 38))

    def draw_menu_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 235))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font_title.render("NEON SNAKE", True, COLOR_SNAKE_HEAD)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 70))

        subtitle = self.font_body.render("ARCADE RETRO EDITION", True, COLOR_ACCENT_CYAN)
        self.screen.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, 125))

        # High score & Lifetime Record callout
        win_rate = (self.wins / max(1, self.total_games)) * 100 if self.total_games > 0 else 0
        rec_str = f"★ Best: {self.high_score} pts   |   Wins: {self.wins}   Losses: {self.losses} ({win_rate:.0f}% Win Rate) ★"
        hs_text = self.font_body.render(rec_str, True, COLOR_ACCENT_GOLD)
        self.screen.blit(hs_text, (WINDOW_WIDTH // 2 - hs_text.get_width() // 2, 162))

        # Mode Selection Cards
        # Option 1: Human Player Card
        card1_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 205, 235, 145)
        pygame.draw.rect(self.screen, (18, 28, 42), card1_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 180, 255), card1_rect, width=2, border_radius=12)

        p1_title = self.font_header.render("[1] MANUAL", True, COLOR_ACCENT_CYAN)
        self.screen.blit(p1_title, (card1_rect.centerx - p1_title.get_width() // 2, 220))
        p1_desc1 = self.font_small.render("Play with Arrow / WASD", True, COLOR_TEXT_PRIMARY)
        p1_desc2 = self.font_small.render("Test your reflexes!", True, COLOR_TEXT_SECONDARY)
        p1_btn = self.font_small.render("Press 1 or SPACE", True, COLOR_ACCENT_CYAN)
        self.screen.blit(p1_desc1, (card1_rect.centerx - p1_desc1.get_width() // 2, 255))
        self.screen.blit(p1_desc2, (card1_rect.centerx - p1_desc2.get_width() // 2, 277))
        self.screen.blit(p1_btn, (card1_rect.centerx - p1_btn.get_width() // 2, 310))

        # Option 2: AI Autoplay Card
        card2_rect = pygame.Rect(WINDOW_WIDTH // 2 + 15, 205, 235, 145)
        pygame.draw.rect(self.screen, (16, 38, 30), card2_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_SNAKE_HEAD, card2_rect, width=2, border_radius=12)

        p2_title = self.font_header.render("[2] SMART AI", True, COLOR_SNAKE_HEAD)
        self.screen.blit(p2_title, (card2_rect.centerx - p2_title.get_width() // 2, 220))
        p2_desc1 = self.font_small.render("Autonomous smart agent", True, COLOR_TEXT_PRIMARY)
        p2_desc2 = self.font_small.render("BFS + Tail survival!", True, COLOR_TEXT_SECONDARY)
        p2_btn = self.font_small.render("Press 2 or A to Watch", True, COLOR_SNAKE_HEAD)
        self.screen.blit(p2_desc1, (card2_rect.centerx - p2_desc1.get_width() // 2, 255))
        self.screen.blit(p2_desc2, (card2_rect.centerx - p2_desc2.get_width() // 2, 277))
        self.screen.blit(p2_btn, (card2_rect.centerx - p2_btn.get_width() // 2, 310))

        # Control Guide Box
        box_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, 375, 500, 215)
        pygame.draw.rect(self.screen, (20, 26, 38), box_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_HEADER_BORDER, box_rect, width=2, border_radius=12)

        guide_lines = [
            ("Mobile Touch (CP)", "Swipe to steer, on-screen D-Pad & buttons"),
            ("Keyboard Move", "Arrow Keys or W / A / S / D"),
            ("Interactive Food", "[Q] or tap [+Food] button"),
            ("Interactive Bomb", "[E] or tap [Bomb] button"),
            ("Pause Game", "Spacebar / P or tap Pause"),
            ("Sound Toggle", "M (Mute / Unmute)"),
        ]
        y_off = 390
        for action, key in guide_lines:
            a_surf = self.font_small.render(action, True, COLOR_ACCENT_CYAN)
            k_surf = self.font_small.render(key, True, COLOR_TEXT_PRIMARY)
            self.screen.blit(a_surf, (WINDOW_WIDTH // 2 - 220, y_off))
            self.screen.blit(k_surf, (WINDOW_WIDTH // 2 - 20, y_off))
            y_off += 28

    def draw_paused_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 18, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("PAUSED", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 210))

        sub1 = self.font_body.render("Press SPACE or P to Resume", True, COLOR_ACCENT_CYAN)
        self.screen.blit(sub1, (WINDOW_WIDTH // 2 - sub1.get_width() // 2, 280))

        mode_desc = "Current Mode: MANUAL" if self.mode == MODE_HUMAN else "Current Mode: SMART AI"
        sub_mode = self.font_body.render(f"{mode_desc} (Fixed)", True, COLOR_ACCENT_GOLD)
        self.screen.blit(sub_mode, (WINDOW_WIDTH // 2 - sub_mode.get_width() // 2, 320))

        sub2 = self.font_body.render("Press R to Restart   |   ESC for Menu", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(sub2, (WINDOW_WIDTH // 2 - sub2.get_width() // 2, 360))

    def draw_gameover_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((16, 12, 20, 225))
        self.screen.blit(overlay, (0, 0))

        # Title: VICTORY or GAME OVER (DEFEAT)
        if self.is_round_win:
            title_text = "★ VICTORY! ★"
            title_col = COLOR_SNAKE_HEAD
        else:
            title_text = "GAME OVER"
            title_col = (255, 70, 80)

        title = self.font_title.render(title_text, True, title_col)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 85))

        # Subtitle banner
        if self.is_new_high_score:
            pulse = int(180 + 75 * math.sin(self.time_alive * 6))
            rec_surf = self.font_header.render("★ NEW RECORD HIGH SCORE! ★", True, COLOR_ACCENT_GOLD)
            rec_surf.set_alpha(pulse)
            self.screen.blit(rec_surf, (WINDOW_WIDTH // 2 - rec_surf.get_width() // 2, 145))
        elif self.is_round_win:
            vic_sub = self.font_header.render(f"Target Reached: >= {self.win_target} pts (+1 WIN!)", True, COLOR_SNAKE_HEAD)
            self.screen.blit(vic_sub, (WINDOW_WIDTH // 2 - vic_sub.get_width() // 2, 145))
        else:
            def_sub = self.font_body.render(f"Win Target was {self.win_target} pts (+1 LOSS)", True, COLOR_TEXT_SECONDARY)
            self.screen.blit(def_sub, (WINDOW_WIDTH // 2 - def_sub.get_width() // 2, 145))

        # Stats Card
        card_rect = pygame.Rect(WINDOW_WIDTH // 2 - 205, 185, 410, 235)
        pygame.draw.rect(self.screen, (22, 26, 38), card_rect, border_radius=12)
        border_col = COLOR_SNAKE_HEAD if self.is_round_win else (50, 40, 60)
        pygame.draw.rect(self.screen, border_col, card_rect, width=2, border_radius=12)

        win_rate = (self.wins / max(1, self.total_games)) * 100 if self.total_games > 0 else 0
        outcome_txt = "VICTORY (+1 WIN)" if self.is_round_win else "DEFEAT (+1 LOSS)"
        outcome_col = COLOR_SNAKE_HEAD if self.is_round_win else (255, 80, 90)

        stats = [
            ("Match Result", outcome_txt, outcome_col),
            ("Final Score", f"{self.score} pts", COLOR_ACCENT_CYAN),
            ("Best Record", f"{self.high_score} pts", COLOR_ACCENT_GOLD),
            ("Lifetime Wins", f"{self.wins} ({win_rate:.0f}% Win Rate)", COLOR_SNAKE_HEAD),
            ("Lifetime Losses", f"{self.losses}", (255, 120, 130)),
            ("Apples Eaten", f"{self.fruits_eaten}", COLOR_FOOD),
        ]
        sy = 197
        for label, val, col in stats:
            l_surf = self.font_body.render(label, True, COLOR_TEXT_SECONDARY)
            v_surf = self.font_body.render(val, True, col)
            self.screen.blit(l_surf, (WINDOW_WIDTH // 2 - 175, sy))
            self.screen.blit(v_surf, (WINDOW_WIDTH // 2 + 10, sy))
            sy += 30

        # 5-second Auto-restart Countdown Notice
        secs_left = max(1, int(math.ceil(self.game_over_timer)))
        cd_surf = self.font_header.render(f"Auto-restarting in {secs_left}s... [R to Skip]", True, COLOR_ACCENT_GOLD)
        self.screen.blit(cd_surf, (WINDOW_WIDTH // 2 - cd_surf.get_width() // 2, 440))

        esc_prompt = self.font_small.render("Press R to Restart Now  |  ESC: Main Menu", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(esc_prompt, (WINDOW_WIDTH // 2 - esc_prompt.get_width() // 2, 485))

    def draw_touch_controls(self):
        """Renders subtle, glowing on-screen mobile touch controls for cellphones / touchscreens."""
        # 1. Action Buttons (bottom right): [+Food] and [Bomb]
        # Food Button
        f_surf = pygame.Surface((self.btn_food_rect.width, self.btn_food_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(f_surf, (40, 18, 28, 150), (0, 0, self.btn_food_rect.width, self.btn_food_rect.height), border_radius=16)
        pygame.draw.rect(f_surf, (255, 65, 105, 190), (0, 0, self.btn_food_rect.width, self.btn_food_rect.height), width=2, border_radius=16)
        f_icon = self.font_popup.render("+🍎", True, COLOR_FOOD)
        f_lbl = self.font_small.render("FOOD", True, COLOR_TEXT_PRIMARY)
        f_surf.blit(f_icon, (self.btn_food_rect.width // 2 - f_icon.get_width() // 2, 8))
        f_surf.blit(f_lbl, (self.btn_food_rect.width // 2 - f_lbl.get_width() // 2, 34))
        self.screen.blit(f_surf, self.btn_food_rect.topleft)

        # Bomb Button
        b_surf = pygame.Surface((self.btn_bomb_rect.width, self.btn_bomb_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(b_surf, (45, 30, 15, 150), (0, 0, self.btn_bomb_rect.width, self.btn_bomb_rect.height), border_radius=16)
        pygame.draw.rect(b_surf, (255, 205, 30, 190), (0, 0, self.btn_bomb_rect.width, self.btn_bomb_rect.height), width=2, border_radius=16)
        b_icon = self.font_popup.render("💥", True, COLOR_BONUS)
        b_lbl = self.font_small.render("BOMB", True, COLOR_TEXT_PRIMARY)
        b_surf.blit(b_icon, (self.btn_bomb_rect.width // 2 - b_icon.get_width() // 2, 8))
        b_surf.blit(b_lbl, (self.btn_bomb_rect.width // 2 - b_lbl.get_width() // 2, 34))
        self.screen.blit(b_surf, self.btn_bomb_rect.topleft)

        # 2. Virtual D-Pad (bottom left, active in Manual mode)
        if self.mode == MODE_HUMAN:
            # Base subtle backdrop disc
            base_surf = pygame.Surface((150, 150), pygame.SRCALPHA)
            pygame.draw.circle(base_surf, (16, 24, 38, 110), (75, 75), 68)
            pygame.draw.circle(base_surf, (30, 48, 72, 140), (75, 75), 68, width=1)
            self.screen.blit(base_surf, (self.dpad_cx - 75, self.dpad_cy - 75))

            dpad_buttons = [
                (self.btn_up_rect, "▲"),
                (self.btn_down_rect, "▼"),
                (self.btn_left_rect, "◀"),
                (self.btn_right_rect, "▶"),
            ]
            for rect, arrow in dpad_buttons:
                d_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(d_surf, (22, 34, 52, 160), (0, 0, rect.width, rect.height), border_radius=12)
                pygame.draw.rect(d_surf, (0, 215, 255, 150), (0, 0, rect.width, rect.height), width=2, border_radius=12)
                txt = self.font_header.render(arrow, True, COLOR_ACCENT_CYAN)
                d_surf.blit(txt, (rect.width // 2 - txt.get_width() // 2, rect.height // 2 - txt.get_height() // 2 - 1))
                self.screen.blit(d_surf, rect.topleft)

    def render(self):
        self.screen.fill(COLOR_BG)
        self.draw_grid_dots()

        # In-game entities
        self.food.draw(self.screen, self.time_alive)
        self.snake.draw(self.screen)
        self.particles.draw(self.screen)

        # Floating text popups (+10, BOMB! -3, +FOOD)
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font_popup)

        # On-screen Mobile Touch Controls (D-Pad & Action Buttons)
        if self.state == STATE_PLAYING:
            self.draw_touch_controls()

        # Persistent HUD
        self.draw_header()

        # State Overlays
        if self.state == STATE_MENU:
            self.draw_menu_overlay()
        elif self.state == STATE_PAUSED:
            self.draw_paused_overlay()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover_overlay()

        # Scale virtual surface to actual window / mobile screen
        win_w, win_h = self.window.get_size()
        scale = min(win_w / WINDOW_WIDTH, win_h / WINDOW_HEIGHT)
        sw = int(WINDOW_WIDTH * scale)
        sh = int(WINDOW_HEIGHT * scale)
        ox = (win_w - sw) // 2
        oy = (win_h - sh) // 2

        self.scale = scale
        self.offset_x = ox
        self.offset_y = oy

        self.window.fill((6, 9, 14))
        if sw == WINDOW_WIDTH and sh == WINDOW_HEIGHT:
            self.window.blit(self.screen, (0, 0))
        else:
            scaled = pygame.transform.smoothscale(self.screen, (sw, sh))
            self.window.blit(scaled, (ox, oy))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            self.handle_input()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame()
    game.run()
