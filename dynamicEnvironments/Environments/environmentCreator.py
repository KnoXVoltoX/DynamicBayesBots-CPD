# -*- coding: utf-8 -*-
"""
This code creates a new environment for the Kilosim.
You can set your desired fill-ratio f where f > 0.5 generates more white tiles.
The environment consists out of 10x10 tiles á ~24.75cm limited by a gray border.
"""

# import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import os
import random as rnd

# get the image path
os_path = os.path.dirname(os.path.realpath(__file__))


# set the fill ratio
ratio = float(input("Please enter the wanted fill-ratio. \n(There will be 5 environments with the same fill-ratio generated.)\nFill-ratio: "))

for numb in range(1,6):
    # set the filename
    dir_path = f"{os_path}/{ratio}_{numb}.png"

    #image size
    size = (340, 340)       # image size including the gray border

    # Tile configs
    tileSize = 33           # SxS sized tile
    tileN = 10
    amount = tileN**2         # environment consists out of NxN tiles
    amountW = ratio * amount
    amountB = amount - amountW
    nw = 0
    nb = 0

    # init image
    img = Image.new('RGBA', size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # draw the border
    draw.rectangle([0, 0, 340, 340], fill=(100, 100, 100, 255))

    if ratio < 0.5:
        for i in range(0, tileN):
            for j in range(0, tileN):

                r = rnd.random()

                if  nb != amountB and r > ratio or nw == amountW:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(0, 0, 0, 255))
                    nb += 1

                elif nw != amountW:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(255, 255, 255, 255))
                    nw += 1
                else:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(0, 0, 0, 255))
                    nb += 1
    else:
        for i in range(0, tileN):
            for j in range(0, tileN):

                r = rnd.random()

                if  nw != amountW and r > 1-ratio or nb == amountB:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(255, 255, 255, 255))
                    nw += 1

                elif nb != amountB:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(0, 0, 0, 255))
                    nb += 1
                else:
                    draw.rectangle([5+i*tileSize, 5+j*tileSize, 38+i*tileSize, 38+j*tileSize], fill=(255, 255, 255, 255))
                    nw += 1

    print("NW: ",nw,"   NB: ",nb)

    img.show()

    # save image as png
    img.save(dir_path)
