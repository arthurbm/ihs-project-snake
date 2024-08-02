import os
import random
import pygame
import json
from pygame.math import Vector2
from abc import ABC, abstractmethod
from enum import Enum, auto
from collections import deque
import math

# Load configuration
with open('config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

# Initialize Pygame
pygame.init()

# Game settings
GAME_SETTINGS = CONFIG['game_settings']
COLORS = CONFIG['colors']
SPACESHIP_CONFIG = CONFIG['spaceship']
BOSS_CONFIG = CONFIG['boss']
SCORING = CONFIG['scoring']

CELL_SIZE = GAME_SETTINGS['cell_size']
CELL_NUMBER = GAME_SETTINGS['cell_number']
SCREEN_SIZE = CELL_NUMBER * CELL_SIZE

SPACE_COLOR = tuple(COLORS['space'])
STAR_COLOR = tuple(COLORS['star'])
SHIP_COLOR = tuple(COLORS['ship'])
ASTEROID_COLOR = tuple(COLORS['asteroid'])
RESOURCE_COLOR = tuple(COLORS['resource'])
BOSS_COLOR = tuple(COLORS['boss'])
BOSS_PROJECTILE_COLOR = tuple(COLORS['boss_projectile'])

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()

class InputHandler(ABC):
    @abstractmethod
    def get_direction(self):
        pass

    @abstractmethod
    def get_action(self):
        pass

    @abstractmethod
    def process_events(self, events):
        pass

class KeyboardInput(InputHandler):
    def __init__(self):
        self.direction_queue = deque()
        self.action_queue = deque()

    def get_direction(self):
        return self.direction_queue.popleft() if self.direction_queue else None

    def get_action(self):
        return self.action_queue.popleft() if self.action_queue else None

    def process_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.direction_queue.append(Vector2(0, -1))
                elif event.key == pygame.K_DOWN:
                    self.direction_queue.append(Vector2(0, 1))
                elif event.key == pygame.K_LEFT:
                    self.direction_queue.append(Vector2(-1, 0))
                elif event.key == pygame.K_RIGHT:
                    self.direction_queue.append(Vector2(1, 0))
                elif event.key == pygame.K_RETURN:
                    self.action_queue.append("START")
                elif event.key == pygame.K_SPACE:
                    self.action_queue.append("BOOST")

class ExternalControlInput(InputHandler):
    def __init__(self, fd):
        self.fd = fd
        self.direction_queue = deque()
        self.action_queue = deque()

    def get_direction(self):
        return self.direction_queue.popleft() if self.direction_queue else None

    def get_action(self):
        return self.action_queue.popleft() if self.action_queue else None

    def process_events(self, events):
        from utils import read_button
        from constants import BUTTONS_OPTIONS
        button = read_button(fd=self.fd, show_output_msg=False)
        if BUTTONS_OPTIONS[button] == "UP":
            self.direction_queue.append(Vector2(0, -1))
        elif BUTTONS_OPTIONS[button] == "DOWN":
            self.direction_queue.append(Vector2(0, 1))
        elif BUTTONS_OPTIONS[button] == "LEFT":
            self.direction_queue.append(Vector2(-1, 0))
        elif BUTTONS_OPTIONS[button] == "RIGHT":
            self.direction_queue.append(Vector2(1, 0))
        elif BUTTONS_OPTIONS[button] == "START":
            self.action_queue.append("START")
        elif BUTTONS_OPTIONS[button] == "BOOST":
            self.action_queue.append("BOOST")


class Spaceship:
    def __init__(self):
        self.body = [Vector2(5, 5) for _ in range(SPACESHIP_CONFIG['initial_length'])]
        self.direction = Vector2(1, 0)
        self.new_block = False
        self.boost = False
        self.boost_cooldown = 0

    def draw(self, screen):
        for i, block in enumerate(self.body):
            block_rect = pygame.Rect(int(block.x * CELL_SIZE), int(block.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
            if i == 0:  # Head of the ship
                pygame.draw.rect(screen, SHIP_COLOR, block_rect)
                # Draw a small triangle to indicate the direction
                direction_indicator = [
                    (block_rect.centerx, block_rect.centery),
                    (block_rect.centerx + self.direction.x * CELL_SIZE // 2, block_rect.centery + self.direction.y * CELL_SIZE // 2),
                    (block_rect.centerx - self.direction.y * CELL_SIZE // 4, block_rect.centery + self.direction.x * CELL_SIZE // 4),
                ]
                pygame.draw.polygon(screen, STAR_COLOR, direction_indicator)
            else:
                pygame.draw.rect(screen, SHIP_COLOR, block_rect, 2)

    def move(self):
        if self.boost and self.boost_cooldown == 0:
            move_steps = SPACESHIP_CONFIG['boost_speed_multiplier']
            self.boost_cooldown = SPACESHIP_CONFIG['boost_cooldown']
        else:
            move_steps = 1

        for _ in range(move_steps):
            if self.new_block:
                body_copy = self.body[:]
                body_copy.insert(0, body_copy[0] + self.direction)
                self.body = body_copy[:]
                self.new_block = False
            else:
                body_copy = self.body[:-1]
                body_copy.insert(0, body_copy[0] + self.direction)
                self.body = body_copy[:]

        # Wrap around the screen
        self.body[0].x %= CELL_NUMBER
        self.body[0].y %= CELL_NUMBER

        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1

    def add_block(self):
        self.new_block = True

    def set_direction(self, direction):
        if direction:
            if direction.x != -self.direction.x or direction.y != -self.direction.y:
                self.direction = direction

    def activate_boost(self):
        if self.boost_cooldown == 0:
            self.boost = True
        else:
            self.boost = False

    def reset(self):
        self.body = [Vector2(5, 5), Vector2(4, 5), Vector2(3, 5)]
        self.direction = Vector2(1, 0)
        self.boost = False
        self.boost_cooldown = 0

class Resource:
    def __init__(self):
        self.randomize()

    def draw(self, screen):
        resource_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, RESOURCE_COLOR, resource_rect)

    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class Asteroid:
    def __init__(self):
        self.randomize()

    def draw(self, screen):
        asteroid_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, ASTEROID_COLOR, asteroid_rect)

    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class Boss:
    def __init__(self):
        self.pos = Vector2(CELL_NUMBER // 2, -3)
        self.base_size = BOSS_CONFIG['base_size']
        self.health = BOSS_CONFIG['health']
        self.movement_timer = 0
        self.movement_interval = BOSS_CONFIG['movement_interval']
        self.attack_timer = 0
        self.attack_interval = BOSS_CONFIG['attack_interval']
        self.projectiles = []
        self.wobble_offset = 0
        self.wobble_speed = BOSS_CONFIG['wobble_speed']

    def draw(self, screen):
        self.wobble_offset += self.wobble_speed
        
        points = []
        for i in range(16):
            angle = i * (2 * math.pi / 16)
            wobble = math.sin(angle * 4 + self.wobble_offset) * BOSS_CONFIG['wobble_amplitude']
            radius = (self.base_size / 2 + wobble) * CELL_SIZE
            x = self.pos.x * CELL_SIZE + self.base_size * CELL_SIZE / 2 + math.cos(angle) * radius
            y = self.pos.y * CELL_SIZE + self.base_size * CELL_SIZE / 2 + math.sin(angle) * radius
            points.append((x, y))

        pygame.draw.polygon(screen, BOSS_COLOR, points)

        # Draw health bar
        health_width = (self.health / 10) * (self.base_size * CELL_SIZE)
        health_rect = pygame.Rect(
            int(self.pos.x * CELL_SIZE),
            int((self.pos.y - 1) * CELL_SIZE),
            health_width,
            CELL_SIZE // 2
        )
        pygame.draw.rect(screen, (0, 255, 0), health_rect)  # Green health bar

    def move(self):
        self.movement_timer += 1
        if self.movement_timer >= self.movement_interval:
            self.pos.x += random.choice([-1, 0, 1])
            self.pos.x = max(0, min(CELL_NUMBER - self.base_size, self.pos.x))
            self.movement_timer = 0

    def attack(self):
        self.attack_timer += 1
        if self.attack_timer >= self.attack_interval:
            projectile_pos = Vector2(
                self.pos.x + self.base_size // 2,
                self.pos.y + self.base_size
            )
            self.projectiles.append(projectile_pos)
            self.attack_timer = 0

    def update_projectiles(self):
        for projectile in self.projectiles[:]:
            projectile.y += BOSS_CONFIG['projectile_speed']
            if projectile.y >= CELL_NUMBER:
                self.projectiles.remove(projectile)

    def draw_projectiles(self, screen):
        for projectile in self.projectiles:
            projectile_rect = pygame.Rect(
                int(projectile.x * CELL_SIZE),
                int(projectile.y * CELL_SIZE),
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, BOSS_PROJECTILE_COLOR, projectile_rect)

class Game:
    def __init__(self, input_handler):
        self.spaceship = Spaceship()
        self.resource = Resource()
        self.asteroids = [Asteroid() for _ in range(GAME_SETTINGS['initial_asteroids'])]
        self.input_handler = input_handler
        self.score = 0
        self.state = GameState.MENU
        self.high_score = self.load_high_score()
        self.stars = self.generate_stars()
        self.fps = GAME_SETTINGS['fps']
        self.boss = None
        self.boss_spawn_score = BOSS_CONFIG['spawn_score']
        self.fps_increase_rate = GAME_SETTINGS['fps_increase_rate']

    def update(self):
        if self.state == GameState.PLAYING:
            self.spaceship.move()
            self.check_collision()
            self.check_fail()
            direction = self.input_handler.get_direction()
            if direction:
                self.spaceship.set_direction(direction)
            action = self.input_handler.get_action()
            if action == "BOOST":
                self.spaceship.activate_boost()
            
            # Boss logic
            if self.score >= self.boss_spawn_score and self.boss is None:
                self.boss = Boss()
            
            if self.boss:
                self.boss.move()
                self.boss.attack()
                self.boss.update_projectiles()
                self.check_boss_collision()

        elif self.state == GameState.MENU or self.state == GameState.GAME_OVER:
            action = self.input_handler.get_action()
            if action == "START":
                self.start_game()

    def draw(self, screen):
        self.draw_space(screen)
        self.spaceship.draw(screen)
        self.resource.draw(screen)
        for asteroid in self.asteroids:
            asteroid.draw(screen)
        if self.boss:
            self.boss.draw(screen)
            self.boss.draw_projectiles(screen)
        self.draw_score(screen)
        
        if self.state == GameState.MENU:
            self.draw_menu(screen)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(screen)

    def check_collision(self):
        if self.resource.pos == self.spaceship.body[0]:
            self.resource.randomize()
            self.spaceship.add_block()
            self.score += SCORING['resource_points']
            self.fps += self.fps_increase_rate
            if self.score % GAME_SETTINGS['asteroids_increase_interval'] == 0:
                self.asteroids.append(Asteroid())

    def check_boss_collision(self):
        if self.boss:
            # Check if spaceship hits boss
            head = self.spaceship.body[0]
            boss_center = self.boss.pos + Vector2(self.boss.base_size / 2, self.boss.base_size / 2)
            distance = (head - boss_center).length()
            if distance < self.boss.base_size / 2 * CELL_SIZE:
                self.game_over()
                return

            # Check if spaceship hits boss projectiles
            for projectile in self.boss.projectiles:
                if projectile.x == self.spaceship.body[0].x and projectile.y == self.spaceship.body[0].y:
                    self.game_over()
                    return

            # Check if spaceship hits boss's weak point (top-center)
            weak_point = self.boss.pos + Vector2(self.boss.base_size / 2, 0)
            if (abs(weak_point.x - self.spaceship.body[0].x) < 1 and
                abs(weak_point.y - self.spaceship.body[0].y) < 1):
                self.boss.health -= 1
                if self.boss.health <= 0:
                    self.score += SCORING['boss_defeat_bonus']
                    self.boss = None
                    self.boss_spawn_score += SCORING['boss_spawn_score_increase']

    def check_fail(self):
        head = self.spaceship.body[0]
        for block in self.spaceship.body[1:]:
            if block == head:
                self.game_over()
        for asteroid in self.asteroids:
            if asteroid.pos == head:
                self.game_over()

    def game_over(self):
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def start_game(self):
        self.spaceship.reset()
        self.score = 0
        self.asteroids = [Asteroid() for _ in range(GAME_SETTINGS['initial_asteroids'])]
        self.state = GameState.PLAYING
        self.fps = GAME_SETTINGS['fps']
        self.boss = None


    def generate_stars(self):
        return [(random.randint(0, SCREEN_SIZE), random.randint(0, SCREEN_SIZE)) for _ in range(100)]

    def draw_space(self, screen):
        screen.fill(SPACE_COLOR)
        for star in self.stars:
            pygame.draw.circle(screen, STAR_COLOR, star, 1)

    def draw_score(self, screen):
        score_text = f"Score: {self.score}"
        score_surface = pygame.font.Font(None, 36).render(score_text, True, STAR_COLOR)
        score_rect = score_surface.get_rect(topleft=(20, 20))
        screen.blit(score_surface, score_rect)

    def draw_menu(self, screen):
        title_surface = pygame.font.Font(None, 72).render("Space Snake", True, STAR_COLOR)
        title_rect = title_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 3))
        screen.blit(title_surface, title_rect)

        start_surface = pygame.font.Font(None, 36).render("Press Enter to Start", True, STAR_COLOR)
        start_rect = start_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE * 2 // 3))
        screen.blit(start_surface, start_rect)

    def draw_game_over(self, screen):
        game_over_surface = pygame.font.Font(None, 72).render("Game Over", True, STAR_COLOR)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 3))
        screen.blit(game_over_surface, game_over_rect)

        score_surface = pygame.font.Font(None, 36).render(f"Score: {self.score}", True, STAR_COLOR)
        score_rect = score_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2))
        screen.blit(score_surface, score_rect)

        high_score_surface = pygame.font.Font(None, 36).render(f"High Score: {self.high_score}", True, STAR_COLOR)
        high_score_rect = high_score_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2 + 40))
        screen.blit(high_score_surface, high_score_rect)

        restart_surface = pygame.font.Font(None, 36).render("Press Enter to Restart", True, STAR_COLOR)
        restart_rect = restart_surface.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE * 2 // 3))
        screen.blit(restart_surface, restart_rect)

    def load_high_score(self):
        try:
            with open('high_score.txt', 'r') as f:
                return int(f.read())
        except FileNotFoundError:
            return 0

    def save_high_score(self):
        with open('high_score.txt', 'w') as f:
            f.write(str(self.high_score))

def main():
    # Change this line to switch between keyboard and external control
    USE_KEYBOARD = True

    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption('Space Snake')
    clock = pygame.time.Clock()

    if USE_KEYBOARD:
        input_handler = KeyboardInput()
    else:
        from constants import PATH
        fd = os.open(PATH, os.O_RDWR)
        input_handler = ExternalControlInput(fd)
        print('File opened successfully!')

    game = Game(input_handler)

    try:
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    return

            input_handler.process_events(events)
            game.update()
            game.draw(screen)
            pygame.display.update()
            clock.tick(game.fps)  # Use the game's current FPS

    finally:
        pygame.quit()
        if not USE_KEYBOARD:
            os.close(fd)
            print('File closed successfully!')

if __name__ == "__main__":
    main()