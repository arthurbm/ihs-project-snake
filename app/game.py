import os
import random
import pygame
import json
from pygame.math import Vector2
from abc import ABC, abstractmethod
from enum import Enum, auto
from collections import deque

# Load configuration
with open('config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

# Initialize Pygame
pygame.init()

# Game settings
CELL_SIZE = CONFIG['cell_size']
CELL_NUMBER = CONFIG['cell_number']
SCREEN_SIZE = CELL_NUMBER * CELL_SIZE

# Colors
SPACE_COLOR = tuple(CONFIG['colors']['space'])
STAR_COLOR = tuple(CONFIG['colors']['star'])
SHIP_COLOR = tuple(CONFIG['colors']['ship'])
ASTEROID_COLOR = tuple(CONFIG['colors']['asteroid'])
RESOURCE_COLOR = tuple(CONFIG['colors']['resource'])

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
        self.body = [Vector2(5, 5), Vector2(4, 5), Vector2(3, 5)]
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
            move_steps = 2
            self.boost_cooldown = 30  # Set cooldown to 30 frames (0.5 seconds at 60 FPS)
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

class Game:
    def __init__(self, input_handler):
        self.spaceship = Spaceship()
        self.resource = Resource()
        self.asteroids = [Asteroid() for _ in range(5)]  # Start with 5 asteroids
        self.input_handler = input_handler
        self.score = 0
        self.state = GameState.MENU
        self.high_score = self.load_high_score()
        self.stars = self.generate_stars()
        self.fps = CONFIG['fps']

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
        self.draw_score(screen)
        
        if self.state == GameState.MENU:
            self.draw_menu(screen)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(screen)

    def check_collision(self):
        if self.resource.pos == self.spaceship.body[0]:
            self.resource.randomize()
            self.spaceship.add_block()
            self.score += 1
            self.fps += 1  # Increase FPS by 1
            if self.score % 5 == 0:  # Add a new asteroid every 5 points
                self.asteroids.append(Asteroid())

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
        self.asteroids = [Asteroid() for _ in range(5)]
        self.state = GameState.PLAYING
        self.fps = CONFIG['fps']  # Reset FPS to initial value

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