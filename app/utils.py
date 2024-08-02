import os
from fcntl import ioctl
from time import sleep
from constants import SEVEN_SEGMENT_OPTIONS, WR_RED_LEDS, WR_GREEN_LEDS, RD_SWITCHES, RD_PBUTTONS

def seven_segment_encoder(num):
    display = 0
    num_digits = 0

    while True:
        digit = num % 10
        display |= (SEVEN_SEGMENT_OPTIONS[digit] << 8 * num_digits)
        num_digits += 1
        num = num // 10
        
        if num == 0:
            break

    for i in range (num_digits, num_digits + (4 - num_digits)):
        display |= (SEVEN_SEGMENT_OPTIONS["OFF"] << 8 * i)

    return display

def seven_segment(fd, num, display, show_output_msg):
    data = seven_segment_encoder(num)
    
    ioctl(fd, display)
    retval = os.write(fd, data.to_bytes(4, 'little'))

    if show_output_msg:
        print(f'>>> wrote {retval} bytes on seven segments!')

def red_leds(fd, on, inverse, sequence, show_output_msg):
    if sequence:
        if inverse:
            data = 0b111111111111111111
            output_msg = '>>> red leds inverse sequence!'

            for i in range(18, -1, -1):
                ioctl(fd, WR_RED_LEDS)
                os.write(fd, data.to_bytes(4,'little'))
                sleep(0.1)
                data_bin = bin(data)
                data_bin = data_bin[2:]
                data_bin = data_bin[:i] + '0' + data_bin[i+1:]
                data_bin = '0b' + data_bin
                data = int(data_bin, 2)
        else:
            data = 0b111111111111111111
            output_msg = '>>> red leds sequence!'

            for i in range(0, 18):
                ioctl(fd, WR_RED_LEDS)
                os.write(fd, data.to_bytes(4,'little'))
                sleep(0.1)
                data >>= 1
    else:
        if on:
            data = 0b111111111111111111
            output_msg = '>>> red leds on!'
        else:
            data = 0b000000000000000000
            output_msg = '>>> red leds off!'

        ioctl(fd, WR_RED_LEDS)
        os.write(fd, data.to_bytes(4, 'little'))
    
    if show_output_msg:
        print(output_msg)

def green_leds(fd, on, inverse, sequence, show_output_msg):
    if sequence:
        if inverse:
            data = 0b11111111
            output_msg = '>>> green leds inverse sequence!'

            for i in range(18, -1, -1):
                ioctl(fd, WR_GREEN_LEDS)
                os.write(fd, data.to_bytes(4,'little'))
                sleep(0.1)
                data_bin = bin(data)
                data_bin = data_bin[2:]
                data_bin = data_bin[:i] + '0' + data_bin[i+1:]
                data_bin = '0b' + data_bin
                data = int(data_bin, 2)
        else:
            data = 0b11111111       
            output_msg = '>>> green leds sequence!'

            for i in range(0, 9):
                ioctl(fd, WR_GREEN_LEDS)
                os.write(fd, data.to_bytes(4,'little'))
                sleep(0.1)
                data >>= 1
    else:
        if on:
            data = 0b111111111
            output_msg = '>>> green leds on!'
        else:
            data = 0b000000000
            output_msg = '>>> green leds off!'

        ioctl(fd, WR_GREEN_LEDS)
        os.write(fd, data.to_bytes(4, 'little'))

    if show_output_msg:
        print(output_msg)

def read_button(fd, show_output_msg):
    ioctl(fd, RD_PBUTTONS)
    button = os.read(fd, 4)
    button = bin(int.from_bytes(button, 'little'))

    if show_output_msg:
        print(f'>>> button {button}')

    return button

def read_switches(fd, show_output_msg):
    ioctl(fd, RD_SWITCHES)
    switches = os.read(fd, 4)
    switches = bin(int.from_bytes(switches, 'little'))  

    if show_output_msg:
        print(f'>>> switches {switches}')

    return switches