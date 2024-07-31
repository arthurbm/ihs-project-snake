import os
import pygame
import random
from utils import read_button, BUTTONS_OPTIONS, PATH, WR_L_DISPLAY, seven_segment

# Inicializar Pygame
pygame.init()

# Definição de cores
white = (255, 255, 255)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)

# Dimensões da tela
display_width = 600
display_height = 400
display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Snake Game')

clock = pygame.time.Clock()
snake_block = 10
snake_speed = 15

# Fontes
font_style = pygame.font.SysFont(None, 35)
score_font = pygame.font.SysFont(None, 35)

# Arquivo da placa
fd = os.open(PATH, os.O_RDWR)

def score_display(score):
    value = score_font.render(f"Your Score: {score}", True, black)
    display.blit(value, [0, 0])
    seven_segment(fd, score, WR_L_DISPLAY, show_output_msg=False)

def our_snake(snake_block, snake_list):
    for x in snake_list:
        pygame.draw.rect(display, black, [x[0], x[1], snake_block, snake_block])

def message(msg, color):
    mesg = font_style.render(msg, True, color)
    display.blit(mesg, [display_width / 6, display_height / 3])

def game_loop():
    game_over = False
    game_close = False

    x1 = display_width / 2
    y1 = display_height / 2

    x1_change = 0
    y1_change = 0

    snake_List = []
    Length_of_snake = 1

    foodx = round(random.randrange(0, display_width - snake_block) / 10.0) * 10.0
    foody = round(random.randrange(0, display_height - snake_block) / 10.0) * 10.0

    while not game_over:

        while game_close:
            display.fill(blue)
            message("You Lost! Press START to Play Again", red)
            score_display(Length_of_snake - 1)
            pygame.display.update()

            button = read_button(fd, show_output_msg=False)
            if BUTTONS_OPTIONS[button] == "START":
                game_loop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True

        button = read_button(fd, show_output_msg=False)
        if BUTTONS_OPTIONS[button] == "LEFT":
            x1_change = -snake_block
            y1_change = 0
        elif BUTTONS_OPTIONS[button] == "RIGHT":
            x1_change = snake_block
            y1_change = 0
        elif BUTTONS_OPTIONS[button] == "UP":
            y1_change = -snake_block
            x1_change = 0
        elif BUTTONS_OPTIONS[button] == "DOWN":
            y1_change = snake_block
            x1_change = 0

        if x1 >= display_width or x1 < 0 or y1 >= display_height or y1 < 0:
            game_close = True
        x1 += x1_change
        y1 += y1_change
        display.fill(blue)
        pygame.draw.rect(display, green, [foodx, foody, snake_block, snake_block])
        snake_Head = []
        snake_Head.append(x1)
        snake_Head.append(y1)
        snake_List.append(snake_Head)
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        our_snake(snake_block, snake_List)
        score_display(Length_of_snake - 1)

        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, display_width - snake_block) / 10.0) * 10.0
            foody = round(random.randrange(0, display_height - snake_block) / 10.0) * 10.0
            Length_of_snake += 1

        clock.tick(snake_speed)

    pygame.quit()
    quit()

game_loop()
