


import os
import sys
from tkinter import filedialog
import tkinter as tk
win = tk.Tk()
win.withdraw()
import pygame as pg
from pygame._sdl2.video import Window
from PIL import Image, ImageOps

from pygame.locals import (
    K_LEFT,
    K_RIGHT,
)

file_list = []

WIDTH, HEIGHT = 1200, 800
screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN | pg.SCALED)
pg.display.set_caption("Slide Viewer")
ADVANCE_EVENT = pg.USEREVENT + 1

def select_image():
    filename = filedialog.askopenfilename()
    # filepath = filedialog.askopenfile(initialdir=".", title="select image", filetypes=(("all files", "*.*"),("all files", "*.*")))
    folder = os.path.dirname(filename)
    with open(filename, "rb") as image_file:
        # image = pg.image.load(filename)
        raw_image = Image.open(image_file)
        image = ImageOps.exif_transpose(raw_image)
        surface = pg.image.fromstring(image.tobytes(), image.size, image.mode)
    return filename, surface, folder

def scale_image(image, w, h):
    # image = ImageOps.exif_transpose(image)
    #surface = pg.image.fromstring(image.tobytes(), image.size, image.mode)
    iw, ih = image.get_width(), image.get_height()
    scale = min(w/iw, h/ih)
    new_size = (int(iw*scale), int(ih*scale))
    return pg.transform.scale(image, new_size)

image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'] #, '.heic']

def sort_analyse(folder, image_name):
    files = os.listdir(folder)
    image_names = []
    for file in files:
        if os.path.splitext(file)[1].lower() in image_extensions:
            # print('good extension')
            fullpath = os.path.join(folder, file)
            if os.path.isfile(fullpath):
                # print('is a file')
                image_names.append(fullpath)
    sorted_files = image_names #sorted(image_names, key=os.path.getctime)
    # print(f'sorted files: {sorted_files}')
    target = image_name #os.path.join(folder, image_name)
    index = sorted_files.index(target)
    return sorted_files, index


def get_image(filename):
    with open(filename, "rb") as image_file:
        # image = pg.image.load(filename)
        raw_image = Image.open(image_file)
        image = ImageOps.exif_transpose(raw_image)
        surface = pg.image.fromstring(image.tobytes(), image.size, image.mode)
    return surface


def reset_advance_timer():
    pg.time.set_timer(ADVANCE_EVENT, 0)
    pg.time.set_timer(ADVANCE_EVENT, 2000)


def main():
    # win = tk.Tk()
    # win.withdraw()
    pg.init()
    running = True
    image = None
    clock = pg.time.Clock()
    while running:
        window = Window.from_display_module()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.unicode == 'l':
                    image_name, image, folder = select_image()
                    file_list, index = sort_analyse(folder, image_name)
                    reset_advance_timer()
                elif event.key == K_LEFT:
                    if index is not None:
                        index = (index - 1) % len(file_list)
                        image = get_image(file_list[index])
                        reset_advance_timer()
                elif event.key == K_RIGHT:
                    if index is not None:
                        index = (index + 1) % len(file_list)
                        image = get_image(file_list[index])
                        reset_advance_timer()
            elif event.type == ADVANCE_EVENT:
                if index is not None:
                    index = (index + 1) % len(file_list)
                    image = get_image(file_list[index])
                    reset_advance_timer()

        screen.fill((50, 80, 120))
        if image is not None:
            scaled_image = scale_image(image, WIDTH, HEIGHT)
            image_rect = scaled_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_image, image_rect)
        pg.display.flip()
        clock.tick(60)
    # win.quit()
    pg.quit()
    sys.exit()

if __name__ == '__main__':
    main()