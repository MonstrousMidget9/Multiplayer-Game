import pygame
import time
from pygame import draw
from pygame import transform
from graphics import black, red
from math import sqrt
from threading import Thread
from pygame import font
import os

path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)
del path

localPlayer = None
wall_list = []
remotePlayers = {}
def init(lp, wl, rp):
    global localPlayer, wall_list, remotePlayers
    localPlayer = lp
    wall_list = wl
    remotePlayers = rp

class player():
    def __init__(self, username, same_team=False):
        self.rect = pygame.Rect((100, 100, 50, 70))
        self.moving = 0
        self.move_flag = 0
        self.death_flag = 0
        self.running_count = 0
        self.idle_count = 0
        self.bullets = {}
        f = font.Font("Minecraft.ttf", 12)
        self.text = f.render(username, False, (255, 255, 255), (0, 0, 0))
        self.text_box = self.text.get_rect()
        self.dead = 0
        self.same_team = same_team

        if same_team:
            self.running_list = black.running_list
            self.idle_list = black.idle_list
            self.death_list = black.death_list
        else:
            self.running_list = red.running_list
            self.idle_list = red.idle_list
            self.death_list = red.death_list
    
    # def draw(self, screen):
    #     draw.rect(screen, (255, 255, 255),self.rect)
    
    def set_cords(self, cords):
        self.rect.x, self.rect.y = cords

    def shoot(self, initial, final, rng=700, speed=15):
        cords = list(initial)
        key = time.time()
        try:
            slope = (final[1]-initial[1]) / (final[0]-initial[0])
        except ZeroDivisionError:
            delx = 0
            dely = 10
        else:
            delx = speed/sqrt((slope**2+1))
            dely = slope*delx
        def kill_bullet():
            try:
                del self.bullets[key]
            except Exception as e:
                print(f"ERROR2: {e}")
        def _s():
            global remotePlayers, wall_list, localPlayer
            r = 0
            try:
                if final[0] < initial[0]:
                    nonlocal delx, dely
                    delx = - delx
                    dely = - dely
                else:#right
                    pass                    
                while r < rng:
                    self.bullets[key] = cords
                    cords[0] += delx
                    cords[1] += dely
                    r += speed
                    if localPlayer.collidepoint(cords) and not self.same_team:
                        break
                    for w in wall_list:
                        if w.rect.collidepoint(cords):
                            kill_bullet()
                            return
                    for rp in remotePlayers:
                        if remotePlayers[rp] != self and remotePlayers[rp].rect.collidepoint(cords) and remotePlayers[rp].same_team != self.same_team:
                            kill_bullet()
                            return
                    time.sleep(0.02)
                kill_bullet()
            except:
                print(r, rng)
        Thread(target=_s, daemon=True).start()
    
    def animate(self, screen):
        if self.dead and time.time()-self.death_flag > 3: # after 3 seconds the object will no longer be blit on the screen
            return

        self.text_box.center = (self.rect.centerx, self.rect.centery-45)
        screen.blit(self.text, self.text_box) # nametag

        cords = (self.rect.x-20, self.rect.y-15)
        if self.dead == 2:
            screen.blit(self.death_list[-1], cords)
            return
        if self.dead:
            try:
                if time.time() - self.move_flag >= 0.1:
                    screen.blit(self.death_list[self.idle_count], cords)
                    self.idle_count += 1
                else:
                    screen.blit(self.death_list[self.idle_count], cords)
            except IndexError:
                self.dead = 2
            return
        if time.time() - self.move_flag >= 0.1:
            self.move_flag = time.time()
            if self.moving == 2:
                screen.blit(self.running_list[self.running_count%6], cords)
                self.running_count += 1
            elif self.moving == 1:
                screen.blit(pygame.transform.flip(self.running_list[self.running_count%6], True, False), cords)
                self.running_count += 1
            elif self.moving == 0:
                screen.blit(self.idle_list[self.idle_count%5], cords)
                self.idle_count += 1
        else:
            if self.moving == 2:
                screen.blit(self.running_list[self.running_count%6], cords)
            elif self.moving == 1:
                screen.blit(pygame.transform.flip(self.running_list[self.running_count%6], True, False), cords)
            elif self.moving == 0:
                screen.blit(self.idle_list[self.idle_count%5], cords)
    
    def kill(self):
        self.dead = True
        self.death_flag = time.time()
        self.idle_count = 0
        self.rect.size = (1, 1)
    
    def respawn(self):
        self.dead = False
        self.rect.size = (50, 70)

    
class wall():
    def __init__(self, size, color = (252, 65, 3)):
        self.rect = pygame.Rect(size)
        self.x, self.y = size[0], size[1]
        self.rect.x, self.rect.y = self.x, self.y
        self.color = color
        
    def draw(self, screen):
        # if not self.is_invisible:
        draw.rect(screen, self.color, self.rect)

class bush():
    def __init__(self, cords, type=1) -> None:
        if type == 1:
            self.img = transform.scale(pygame.image.load(f"sprites/bush1.png"), (130, 93))
            self.rect = pygame.Rect(*cords, 120, 90)
        elif type == 2:
            self.img = transform.scale(pygame.image.load(f"sprites/bush2.png"), (120, 130))
            self.rect = pygame.Rect(*cords, 120, 130)    
        elif type == 3:
            self.img = transform.scale(pygame.image.load(f"sprites/bush3.png"), (int(570/3)+10, int(440/3)+20))
            self.rect = pygame.Rect(*cords, int(570/3), int(440/3))
    
    def draw(self, screen, alpha=False):
        if not alpha:
            self.img.set_alpha(255)
        else:
            self.img.set_alpha(150)
        screen.blit(self.img, self.rect)

class _center:
    def __init__(self):
        self.rect = pygame.Rect((0, 0, 10, 10))

center = _center()