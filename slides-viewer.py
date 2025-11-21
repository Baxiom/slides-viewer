


import os
import sys
from tkinter import filedialog
import tkinter as tk
from pygame import freetype

win = tk.Tk()
win.withdraw()
import pygame as pg
pg.font.init()
pg.freetype.init()
from pygame._sdl2.video import Window
from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS, IFD
from pillow_heif import register_heif_opener

register_heif_opener()

from pygame.locals import (
    K_LEFT,
    K_RIGHT,
)

file_list = []

WIDTH, HEIGHT = 1740, 1040
SMALL_WIDTH, SMALL_HEIGHT = (WIDTH - 200), (HEIGHT - 40)
screen = pg.display.set_mode((WIDTH, HEIGHT))#, pg.FULLSCREEN | pg.SCALED)
pg.display.set_caption("Slide Viewer")
ADVANCE_EVENT = pg.USEREVENT + 1
DUMMY_DATE = '1900:01:01 23:30:00'

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


def get_date(fullpath):
    img = Image.open(fullpath)
    date = DUMMY_DATE
    exif_data = img.getexif()
    if exif_data:
        try:
            ifd = exif_data.get_ifd(ExifTags.IFD.Exif)
            for k, v in ifd.items():
                tag = TAGS.get(k, k)
                if tag == 'DateTimeOriginal':
                    date = v
                    break
        except KeyError:
            pass
    return date

def sort_analyse(folder, image_name):
    files = os.listdir(folder)
    image_names_dates = []
    for file in files:
        if os.path.splitext(file)[1].lower() in image_extensions:
            fullpath = os.path.join(folder, file)
            if os.path.isfile(fullpath):
                date = get_date(fullpath)
                image_names_dates.append((fullpath, date))
    image_names_dates.sort(key=lambda x: x[1])
    print(f'sorted files[:10]: {image_names_dates[:5]}')
    image_names = [c[0] for c in image_names_dates]
    index = image_names.index(image_name)
    return image_names_dates, index


def get_image(filename):
    with open(filename[0], "rb") as image_file:
        raw_image = Image.open(image_file)
        image = ImageOps.exif_transpose(raw_image)
        analyse(raw_image)
        surface = pg.image.fromstring(image.tobytes(), image.size, image.mode)
    return surface


def reset_advance_timer():
    pg.time.set_timer(ADVANCE_EVENT, 0)
    pg.time.set_timer(ADVANCE_EVENT, 2000)


def analyse(img):
    exif_data = img.getexif()
    if not exif_data:
        return "No EXIF data found."
    date_taken_tag = None
    for ifd_id in IFD:
        print('>>>>>>>>>', ifd_id.name, '<<<<<<<<<<')
        try:
            ifd = exif_data.get_ifd(ifd_id)

            if ifd_id == IFD.GPSInfo:
                resolve = GPSTAGS
            else:
                resolve = TAGS

            for k, v in ifd.items():
                tag = resolve.get(k, k)
                if tag == 'DateTimeOriginal':
                    print(tag, v)
        except KeyError:
            pass


FONT = freetype.Font(None, size=20)
TEXT_COLOUR = (255, 255, 210)

def display_date_time(screen, date_time):
    FONT.render_to(screen, (10, 10), date_time, TEXT_COLOUR)

def main():
    # win = tk.Tk()
    # win.withdraw()
    pg.init()
    running = True
    image = None
    index = None
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
                    print(f'image displayed: {file_list[index]}')
                    reset_advance_timer()

        screen.fill((50, 80, 120))
        if image is not None:
            if index is not None:
                display_date_time(screen, file_list[index][1])
            scaled_image = scale_image(image, SMALL_WIDTH, SMALL_HEIGHT)
            image_rect = scaled_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_image, image_rect)
        pg.display.flip()
        clock.tick(60)
    # win.quit()
    pg.quit()
    sys.exit()

if __name__ == '__main__':
    main()