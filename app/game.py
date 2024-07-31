import os
import random
from utils import *
import pygame
from pygame.math import Vector2

# Initialize Pygame
pygame.init()

# Game settings
CELL_SIZE = 40
CELL_NUMBER = 20
SCREEN_SIZE = CELL_NUMBER * CELL_SIZE

# Initialize the screen
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption('Snake Game')
clock = pygame.time.Clock()

# Colors
GREEN = (175, 215, 70)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class Snake:
    def __init__(self):
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(1, 0)
        self.new_block = False

    def draw(self):
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

class Fruit:
    def __init__(self):
        self.randomize()

    def draw(self):
        fruit_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, RED, fruit_rect)

    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class Game:
    def __init__(self):
        self.snake = Snake()
        self.fruit = Fruit()
        self.score = 0

    def update(self):
        self.snake.move()
        self.check_collision()
        self.check_fail()

    def draw(self):
        self.draw_grass()
        self.snake.draw()
        self.fruit.draw()
        self.draw_score()

    def check_collision(self):
        if self.fruit.pos == self.snake.body[0]:
            self.fruit.randomize()
            self.snake.add_block()
            self.score += 1

    def check_fail(self):
        if not 0 <= self.snake.body[0].x < CELL_NUMBER or not 0 <= self.snake.body[0].y < CELL_NUMBER:
            self.game_over()

        for block in self.snake.body[1:]:
            if block == self.snake.body[0]:
                self.game_over()

    def game_over(self):
        pygame.quit()
        quit()

    def draw_grass(self):
        for row in range(CELL_NUMBER):
            if row % 2 == 0:
                for col in range(CELL_NUMBER):
                    if col % 2 == 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(screen, GREEN, grass_rect)
            else:
                for col in range(CELL_NUMBER):
                    if col % 2 != 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(screen, GREEN, grass_rect)

    def draw_score(self):
        score_text = str(self.score)
        score_surface = pygame.font.Font(None, 36).render(score_text, True, (56, 74, 12))
        score_rect = score_surface.get_rect(center=(SCREEN_SIZE - 60, 40))
        screen.blit(score_surface, score_rect)

def main():
    fd = os.open(PATH, os.O_RDWR)
    print('File opened successfully!')

    game = Game()
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == SCREEN_UPDATE:
                game.update()

        button = read_button(fd=fd, show_output_msg=False)
        if BUTTONS_OPTIONS[button] == "UP":
            if game.snake.direction.y != 1:
                game.snake.direction = Vector2(0, -1)
        elif BUTTONS_OPTIONS[button] == "DOWN":
            if game.snake.direction.y != -1:
                game.snake.direction = Vector2(0, 1)
        elif BUTTONS_OPTIONS[button] == "LEFT":
            if game.snake.direction.x != 1:
                game.snake.direction = Vector2(-1, 0)
        elif BUTTONS_OPTIONS[button] == "RIGHT":
            if game.snake.direction.x != -1:
                game.snake.direction = Vector2(1, 0)

        screen.fill((175, 215, 70))
        game.draw()
        pygame.display.update()
        clock.tick(60)

    os.close(fd)
    print('File closed successfully!')

if __name__ == "__main__":
    main()