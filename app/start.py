from utils import *
from time import sleep

def reset():
    global fd

    red_leds(fd=fd, on=False, inverse=False, sequence=False, show_output_msg=True)
    green_leds(fd=fd, on=False, inverse=False, sequence=False, show_output_msg=True)
    read_switches(fd=fd, show_output_msg=True)
    read_button(fd=fd, show_output_msg=True)
    read_button(fd=fd, show_output_msg=True)    

    os.close(fd)
    print('\nArquivo fechado com sucesso!\n')

def start():
    global fd

    print('\nAperte o botão de START para o show começar :)\n')

    while True:
        button = read_button(fd=fd, show_output_msg=False)
        if BUTTONS_OPTIONS[button] == "START":
            break

    print('\nPreparando para iniciar o jogo...')
    countdown(fd, start_num=3, delay=1)
    print('Começando o jogo!')

    # Turning on all leds
    red_leds(fd=fd, on=True, inverse=False , sequence=False, show_output_msg=True)
    green_leds(fd=fd, on=True, inverse=False , sequence=False, show_output_msg=True)
    
    # Turning off all leds
    red_leds(fd=fd, on=False, inverse=False, sequence=False, show_output_msg=True)
    green_leds(fd=fd, on=False, inverse=False, sequence=False, show_output_msg=True)

    # Turning on one led at a time in sequence
    red_leds(fd=fd, on=False, inverse=False, sequence=True, show_output_msg=True)    
    green_leds(fd=fd, on=False, inverse=False, sequence=True, show_output_msg=True)

    # Turning on one led at a time in a inverse sequence
    green_leds(fd=fd, on=False, inverse=True, sequence=True, show_output_msg=True)  
    red_leds(fd=fd, on=False, inverse=True, sequence=True, show_output_msg=True)    

    print('\nLigue todos os switches para o jogo começar!\n')

    while True:
        switches = read_switches(fd=fd, show_output_msg=False)
        if switches == '0b111111111111111111':
            break

    reset()

if __name__ == "__main__":
    fd = os.open(PATH, os.O_RDWR)
    print('Arquivo aberto com sucesso!')
    
    start()