import math
import os
import sys
from tkinter import filedialog
import tkinter as tk
from pygame import freetype, SurfaceType
from geopy.geocoders import Nominatim
# from PIL.ExifTags import GPSTAGS

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
    K_SPACE,
)

file_list = []

PRIV = 20. # Fraction of a degree lat/long we will obscure, for privacy. 20 gives ~5km lat
WIDTH, HEIGHT = 1740, 1040
SMALL_WIDTH, SMALL_HEIGHT = (WIDTH - 200), (HEIGHT - 40)
screen = pg.display.set_mode((WIDTH, HEIGHT))#, pg.FULLSCREEN | pg.SCALED)
pg.display.set_caption("Slide Viewer")
ADVANCE_EVENT = pg.USEREVENT + 1
DUMMY_DATE = '1900:01:01 23:30:00'
geolocator = None

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


def to_decimal(lat):
    if lat is None:
        return None
    else:
        return float(lat[0]) + float(lat[1]) / 60. + float(lat[2]) / 3600.


def get_data(fullpath):
    img = Image.open(fullpath)
    date = DUMMY_DATE
    lat, lon = None, None
    lat_ref, lon_ref = None, None
    exif_data = img.getexif()
    if exif_data:
        try:
            ifd = exif_data.get_ifd(ExifTags.IFD.Exif)
            for k, v in ifd.items():
                tag = TAGS.get(k, k)
                if tag == 'DateTimeOriginal':
                    date = v
                    break
            gps = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
            for k, v in gps.items():
                tag = GPSTAGS.get(k, k)
                # print(f'{tag}: {v}')
                if tag == 'GPSLatitude':
                    lat = v
                if tag == 'GPSLatitudeRef':
                    lat_ref = v
                if tag == 'GPSLongitude':
                    lon = v
                if tag == 'GPSLongitudeRef':
                    lon_ref = v
        except KeyError:
            pass
    return date, to_decimal(lat), lat_ref, to_decimal(lon), lon_ref

def sort_analyse(folder, image_name):
    files = os.listdir(folder)
    image_names_dates = []
    for file in files:
        if os.path.splitext(file)[1].lower() in image_extensions:
            fullpath = os.path.join(folder, file)
            if os.path.isfile(fullpath):
                date, lat, lat_ref, lon, lon_ref = get_data(fullpath)
                image_names_dates.append((fullpath, date, lat, lat_ref, lon, lon_ref))
    image_names_dates.sort(key=lambda x: x[1])
    # print(f'sorted files[:10]: {image_names_dates[:5]}')
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
        # print('>>>>>>>>>', ifd_id.name, '<<<<<<<<<<')
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
                # print(f' - tag{tag}, v:{v}')
        except KeyError:
            pass


FONT = freetype.Font(None, size=20)
TEXT_COLOUR = (255, 255, 210)

def display_date_time(screen, date_time):
    FONT.render_to(screen, (10, 10), date_time, TEXT_COLOUR)


def display_info(paused, index, param, folder, info):
    x,y = 10, 40
    FONT.render_to(screen, (x, y), f'Image {index+1}/{param}', TEXT_COLOUR)
    y += 30
    FONT.render_to(screen, (x, y), f'/{os.path.basename(folder)}', TEXT_COLOUR)
    y += 30
    if paused:
        FONT.render_to(screen, (x, y), "Paused", TEXT_COLOUR)


def blit_geos(screen, lat_surf, lon_surf, country_surf, state_surf, town_surf):
    x, y = 10, 120
    for surf in [lat_surf, lon_surf, country_surf, state_surf, town_surf]:
        if surf is not None:
            # print(type(surf))
            # print(f'{surf[0]}, {surf[1]}')
            screen.blit(surf[0], (x, y))
            y += surf[0].get_height() + 5


def main():
    # win = tk.Tk()
    # win.withdraw()
    global geolocator
    pg.init()
    running = True
    image = None
    index = None
    paused = False
    clock = pg.time.Clock()
    old_index = None
    geolocator = Nominatim(user_agent="a_geopy_app")
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
                    paused = False
                    reset_advance_timer()
                elif event.key == K_LEFT:
                    if index is not None:
                        old_index = index
                        index = (index - 1) % len(file_list)
                        image = get_image(file_list[index])
                        if not paused:
                            reset_advance_timer()
                elif event.key == K_RIGHT:
                    if index is not None:
                        old_index = index
                        index = (index + 1) % len(file_list)
                        image = get_image(file_list[index])
                        if not paused:
                            reset_advance_timer()
                elif event.key == K_SPACE:
                    paused = not paused
                    pg.time.set_timer(ADVANCE_EVENT, 0)
                    if not paused:
                        reset_advance_timer()
            elif event.type == ADVANCE_EVENT:
                if index is not None:
                    old_index = index
                    index = (index + 1) % len(file_list)
                    image = get_image(file_list[index])
                    print(f'image displayed: {file_list[index]}')
                    reset_advance_timer()
        if (old_index != index):
            lat_surf, lon_surf, country_surf, state_surf, town_surf = make_geo_display_surface(file_list, geolocator, index)
            old_index = index

        screen.fill((50, 80, 120))
        if image is not None:
            if index is not None:
                display_date_time(screen, file_list[index][1])
                display_info(paused, index, len(file_list), folder, file_list[index])
                blit_geos(screen, lat_surf, lon_surf, country_surf, state_surf, town_surf)
            scaled_image = scale_image(image, SMALL_WIDTH, SMALL_HEIGHT)
            image_rect = scaled_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_image, image_rect)
        pg.display.flip()
        clock.tick(60)
    # win.quit()
    pg.quit()
    sys.exit()


def make_geo_display_surface(file_list, geolocator: Nominatim, index):
    info = file_list[index]
    lat_surf, lon_surf, country_surf, state_surf, town_surf = None, None, None, None, None
    if (info[2] is not None) and (info[3] is not None):
        lat_surf = FONT.render(f'Lat:{info[2]:.2f} {info[3]}', TEXT_COLOUR)
        lon_surf = FONT.render( f'Lon:{info[4]:.2f} {info[5]}', TEXT_COLOUR)
        lat = info[2] if info[3] == 'N' else - info[2]
        lon = info[4] if info[5] == 'E' else - info[4]
        #The long. rounding takes the latitude into account (roughly!):
        lat_priv =  PRIV * 1/math.cos(lat * math.pi / 180)#91/(91 - abs(lat))
        priv_lat, priv_lon = math.ceil(lat * PRIV ) / PRIV, math.ceil(lon * lat_priv) / lat_priv
        print(f'priv_lat: {priv_lat}, priv_lon: {priv_lon}')
        location = geolocator.reverse(f'{priv_lat},{priv_lon}')
        country, state, town = None, None, None
        if location is not None:
            address = location.raw['address']
            print(address)
            country = address['country']
            if 'state' in address:
                state = address['state']
            elif 'province' in address:
                state = address['province']
            if 'city' in address:
                town = address['city']
            elif 'town' in address:
                town = address['town']
            elif 'municipality' in address:
                town = address['municipality']
            elif 'suburb' in address:
                town = address['suburb']
        country_surf = FONT.render( country, TEXT_COLOUR) if country is not None else None
        state_surf = FONT.render( state, TEXT_COLOUR) if state is not None else None
        town_surf = FONT.render(town, TEXT_COLOUR) if town is not None else None
    return lat_surf, lon_surf, country_surf, state_surf, town_surf


if __name__ == '__main__':
    main()