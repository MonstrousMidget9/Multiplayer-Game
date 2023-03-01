import pygame
from math import pow, sqrt
from classes import center
# import numpy as np

clock = pygame.time.Clock()

def relcords(cords):
    return (cords[0]-center.rect.x, cords[1]-center.rect.y)

def realcords(cords):
    return (cords[0]+center.rect.x, cords[1]+center.rect.y)

def dist(initial, final):
    return sqrt(pow(initial[0]-final[0], 2)+pow(initial[1]-final[1], 2))
