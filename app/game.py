import os
import random
import pygame
from pygame.math import Vector2
from abc import ABC, abstractmethod

# Initialize Pygame
pygame.init()

# Game settings
CELL_SIZE = 60
CELL_NUMBER = 15
SCREEN_SIZE = CELL_NUMBER * CELL_SIZE

# Colors
GREEN = (175, 215, 70)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class InputHandler(ABC):
    @abstractmethod
    def get_direction(self):
        pass

class KeyboardInput(InputHandler):
    def get_direction(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            return Vector2(0, -1)
        if keys[pygame.K_DOWN]:
            return Vector2(0, 1)
        if keys[pygame.K_LEFT]:
            return Vector2(-1, 0)
        if keys[pygame.K_RIGHT]:
            return Vector2(1, 0)
        return None

class ExternalControlInput(InputHandler):
    def __init__(self, fd):
        self.fd = fd

    def get_direction(self):
        from utils import read_button
        from constants import BUTTONS_OPTIONS
        button = read_button(fd=self.fd, show_output_msg=False)
        if BUTTONS_OPTIONS[button] == "UP":
            return Vector2(0, -1)
        elif BUTTONS_OPTIONS[button] == "DOWN":
            return Vector2(0, 1)
        elif BUTTONS_OPTIONS[button] == "LEFT":
            return Vector2(-1, 0)
        elif BUTTONS_OPTIONS[button] == "RIGHT":
            return Vector2(1, 0)
        return None

class Snake:
    def __init__(self):
        self.body = [Vector2(5, 5), Vector2(4, 5), Vector2(3, 5)]
        self.direction = Vector2(1, 0)
        self.new_block = False

    def draw(self, screen):
        for block in self.body:
            block_rect = pygame.Rect(int(block.x * CELL_SIZE), int(block.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, BLUE, block_rect)

    def move(self):
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]
            self.new_block = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]

    def add_block(self):
        self.new_block = True

    def set_direction(self, direction):
        if direction:
            if direction.x != -self.direction.x or direction.y != -self.direction.y:
                self.direction = direction

class Fruit:
    def __init__(self):
        self.randomize()

    def draw(self, screen):
        fruit_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, RED, fruit_rect)

    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class Game:
    def __init__(self, input_handler):
        self.snake = Snake()
        self.fruit = Fruit()
        self.input_handler = input_handler
        self.score = 0
        self.is_running = True

    def update(self):
        self.snake.move()
        self.check_collision()
        self.check_fail()
        direction = self.input_handler.get_direction()
        self.snake.set_direction(direction)

    def draw(self, screen):
        self.draw_grass(screen)
        self.snake.draw(screen)
        self.fruit.draw(screen)
        self.draw_score(screen)

    def check_collision(self):
        if self.fruit.pos == self.snake.body[0]:
            self.fruit.randomize()
            self.snake.add_block()
            self.score += 1

    def check_fail(self):
        head = self.snake.body[0]
        if not 0 <= head.x < CELL_NUMBER or not 0 <= head.y < CELL_NUMBER:
            self.game_over()
        for block in self.snake.body[1:]:
            if block == head:
                self.game_over()

    def game_over(self):
        self.is_running = False

    def draw_grass(self, screen):
        for row in range(CELL_NUMBER):
            for col in range(CELL_NUMBER):
                if (row + col) % 2 == 0:
                    grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(screen, GREEN, grass_rect)

    def draw_score(self, screen):
        score_text = str(self.score)
        score_surface = pygame.font.Font(None, 36).render(score_text, True, (56, 74, 12))
        score_rect = score_surface.get_rect(center=(SCREEN_SIZE - 60, 40))
        screen.blit(score_surface, score_rect)

def main():
    # Change this line to switch between keyboard and external control
    USE_KEYBOARD = True

    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption('Snake Game')
    clock = pygame.time.Clock()

    if USE_KEYBOARD:
        input_handler = KeyboardInput()
    else:
        from constants import PATH
        fd = os.open(PATH, os.O_RDWR)
        input_handler = ExternalControlInput(fd)
        print('File opened successfully!')

    game = Game(input_handler)
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)

    try:
        while game.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.is_running = False
                if event.type == SCREEN_UPDATE:
                    game.update()

            screen.fill((175, 215, 70))
            game.draw(screen)
            pygame.display.update()
            clock.tick(60)

    finally:
        pygame.quit()
        if not USE_KEYBOARD:
            os.close(fd)
            print('File closed successfully!')

if __name__ == "__main__":
    main()