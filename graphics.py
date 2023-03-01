from pygame import transform
import pygame
import pygame.image
import os
import time

bullets = {}
speed = 2
dead = 0

running_count = 0
idle_count = 0

path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)
del path

class black:
    img0 = pygame.image.load("characters/Black/run1.png")
    img1 = pygame.image.load("characters/Black/run2.png")
    img2 = pygame.image.load("characters/Black/run3.png")
    img3 = pygame.image.load("characters/Black/run4.png")
    img4 = pygame.image.load("characters/Black/run5.png")
    img5 = pygame.image.load("characters/Black/run6.png")

    img6 = pygame.image.load("characters/Black/idle1.png")
    img7 = pygame.image.load("characters/Black/idle2.png")
    img8 = pygame.image.load("characters/Black/idle3.png")
    img9 = pygame.image.load("characters/Black/idle4.png")
    img10 = pygame.image.load("characters/Black/idle5.png")

    img11 = pygame.image.load("characters/black_death/black_death1.png")
    img12 = pygame.image.load("characters/black_death/black_death2.png")
    img13 = pygame.image.load("characters/black_death/black_death3.png")
    img14 = pygame.image.load("characters/black_death/black_death4.png")
    img15 = pygame.image.load("characters/black_death/black_death5.png")
    img16 = pygame.image.load("characters/black_death/black_death6.png")
    img17 = pygame.image.load("characters/black_death/black_death7.png")
    img18 = pygame.image.load("characters/black_death/black_death8.png")

    running_list = [img0, img1, img2, img3, img4, img5]
    idle_list = [img6, img7, img8, img9, img10]
    death_list = [img11, img12, img13, img14, img15, img16, img17, img18, img18, img18, img18]
    for i in running_list:
        running_list[running_list.index(i)] = transform.scale(i, (96, 96))

    for i in idle_list:
        idle_list[idle_list.index(i)] = transform.scale(i, (96, 96))

    for i in death_list:
        death_list[death_list.index(i)] = transform.scale(i, (96, 96))


blt_img = transform.scale(pygame.image.load("characters/bullet.png"), (9,3))

class red:
    img0 = pygame.image.load("characters/Red/run1.png")
    img1 = pygame.image.load("characters/Red/run2.png")
    img2 = pygame.image.load("characters/Red/run3.png")
    img3 = pygame.image.load("characters/Red/run4.png")
    img4 = pygame.image.load("characters/Red/run5.png")
    img5 = pygame.image.load("characters/Red/run6.png")

    img6 = pygame.image.load("characters/Red/idle1.png")
    img7 = pygame.image.load("characters/Red/idle2.png")
    img8 = pygame.image.load("characters/Red/idle3.png")
    img9 = pygame.image.load("characters/Red/idle4.png")
    img10 = pygame.image.load("characters/Red/idle5.png")

    img11 = pygame.image.load("characters/red_death/red_death1.png")
    img12 = pygame.image.load("characters/red_death/red_death2.png")
    img13 = pygame.image.load("characters/red_death/red_death3.png")
    img14 = pygame.image.load("characters/red_death/red_death4.png")
    img15 = pygame.image.load("characters/red_death/red_death5.png")
    img16 = pygame.image.load("characters/red_death/red_death6.png")
    img17 = pygame.image.load("characters/red_death/red_death7.png")
    img18 = pygame.image.load("characters/red_death/red_death8.png")

    running_list = [img0, img1, img2, img3, img4, img5]
    idle_list = [img6, img7, img8, img9, img10]
    death_list = [img11, img12, img13, img14, img15, img16, img17, img18, img18, img18, img18]
    for i in running_list:
        running_list[running_list.index(i)] = transform.scale(i, (96, 96))

    for i in idle_list:
        idle_list[idle_list.index(i)] = transform.scale(i, (96, 96))

    for i in death_list:
        death_list[death_list.index(i)] = transform.scale(i, (96, 96))

running_list = black.running_list
idle_list = black.idle_list
death_list = black.death_list

def init(s, wl, lp, rp): # initialise this module
    global sock, wall_list, localPlayer, remotePlayers
    sock = s
    wall_list = wl
    localPlayer = lp
    remotePlayers = rp

def update(screen):
    try:
        bls = bullets.copy()
        for b in bls:
            screen.blit(blt_img, bls[b])
        for rp in remotePlayers:
            bls = remotePlayers[rp].bullets.copy()
            for b in bls:
                screen.blit(blt_img, bls[b])
    except:
        print("ITERATION ERROR")
        

move_flag = 0
def animations(mv, lp, screen):
    global running_count, move_flag, idle_count, dead
    cords = (lp.x-20, lp.y-15)
    if dead == 2:
        screen.blit(death_list[-1], cords)
        return
    if dead:
        try:
            if time.time() - move_flag >= 0.1:
                screen.blit(death_list[idle_count], cords)
                idle_count += 1
            else:
                screen.blit(death_list[idle_count], cords)
        except IndexError:
            dead = 2
        return
    if time.time() - move_flag >= 0.1:
        move_flag = time.time()
        if mv == 2:
            screen.blit(running_list[running_count%6], cords)
            running_count += 1
        elif mv == 1:
            screen.blit(pygame.transform.flip(running_list[running_count%6], True, False), cords)
            running_count += 1
        elif mv == 0:
            screen.blit(idle_list[idle_count%5], cords)
            idle_count += 1
    else:
        if mv == 2:
            screen.blit(running_list[running_count%6], cords)
        elif mv == 1:
            screen.blit(pygame.transform.flip(running_list[running_count%6], True, False), cords)
        elif mv == 0:
            screen.blit(idle_list[idle_count%5], cords)

