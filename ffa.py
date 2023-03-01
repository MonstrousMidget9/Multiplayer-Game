import socket
import pygame
from pygame import draw
from threading import Thread
import time
import pickle
from math import sqrt
from classes import wall, player, center, bush
from graphics import speed, animations, update, bullets
import classes, graphics
from functions import dist, relcords, realcords
from pygame import font, mixer
from networking import network_packet, packet_split, server_ip
import os


def run(username):
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    del path

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip , 6977))
    import lobby
    launch = lobby.main(sock, username, "Free For All")
    if not launch:
        exit()

    health = 100
    dead = False
    pygame.init()
    screen = pygame.display.set_mode((900,600))

    moving = 0
    move_flag = 0
    attack_flag = 0
    game_over = False
    end_font = font.Font("Minecraft.ttf", 64)

    pl_list = pickle.loads(sock.recv(2048)) #example playerlist: [0, (0, 'tom'), (1, 'rita')]
    player_no = pl_list[0] #local player number    
    localPlayer = pygame.Rect((400, 250, 50, 70))
    remotePlayers = {} # player objects for players from outside
    for i in pl_list[1::]:
        if i[0] != player_no:
            remotePlayers[i[0]] = player(i[1])
    
    usernames_dict = {i:j for i, j in pl_list[1::]}


    wall_list = [wall((123, 147, 32*4, 32)), wall((396, 323, 32, 32*3)), 
                wall((705, 324, 32, 32*3)), wall((855, 139, 32*4, 32)),
                wall((889, 516, 32*4 , 32)), wall((0, 543, 32*4, 32)),
                wall((192, 551, 32, 32*5)), wall((161, 660, 30, 40)),
                wall((0, 673, 47, 27)), wall((0, 573, 24, 23)),
                wall((0, 0, 10, 698)),# boundary
                wall((20, 0, 1164, 10)),# boundary
                wall((0, 698, 1164, 10)),# boundary
                wall((1164, 0, 10, 698))]# boundary

    def sendThread():
        m = [player_no, relcords((400, 250)), moving]
        sock.send(pickle.dumps(m))
        prev = [relcords((400, 250)), moving]
        while not dead:
            if relcords((400, 250)) != prev[0] or moving != prev[1]:
                m = [player_no, relcords((400, 250)), moving]
                prev = relcords((400, 250)), moving
                if not game_over:
                    sock.send(pickle.dumps(m))
                else:
                    return
                time.sleep(0.09)

    def recvThread():
        nonlocal health
        while True:
            # try:
            for packet in packet_split(sock.recv(2048)):
                dat = pickle.loads(packet)
                if type(dat) == network_packet:

                    if dat.heading == "health":
                        nonlocal health
                        health = dat.data
                    
                    if dat.heading == "dead":
                        if dat.data[0] == player_no:
                            nonlocal dead
                            dead = True
                            health = 0
                            localPlayer.size = (1, 1)
                            graphics.dead = 1 # death animation

                            def _move(delx, dely):
                                for i in everything:
                                    i.rect.x -= delx
                                    i.rect.y -= dely
                                
                                for i in bullets:
                                    bullets[i][0] -= delx
                                    bullets[i][1] -= dely

                                localPlayer.x -= delx
                                localPlayer.y -= dely
                            nonlocal move
                            move = _move # dettach the player object while moving
                        else:
                            remotePlayers[dat.data[0]].kill()
                        print(usernames_dict[dat.data[0]], "has been shot by", usernames_dict[dat.data[1]], "\a")
                    
                    if dat.heading == "game over":
                        nonlocal game_over
                        if dat.data == player_no:
                            game_over = "self"
                        else:
                            game_over = usernames_dict[dat.data]
                        
                        time.sleep(5)
                        nonlocal running
                        running = False # end game
                        return

                elif type(dat) == dict:
                    for rp in dat:
                        if rp == "shots":
                            for shot in dat["shots"]:
                                if shot[0] != player_no: # dont duplicate a bullet shot by local player
                                    gun.set_volume(1-(dist(realcords(shot[1]), localPlayer.center)/1000))
                                    gun.play()
                                    remotePlayers[shot[0]].shoot(realcords((shot[1])), realcords((shot[2])))            
                        elif rp != player_no:
                            remotePlayers[rp].set_cords(realcords(dat[rp][0]))
                            remotePlayers[rp].moving = dat[rp][1]
                

    clock = pygame.time.Clock()
    bush_list = [bush((100, 400)), bush((1000, 500), type=2), bush((550, 250), type=3)]
    everything = wall_list + list(remotePlayers.values()) + [center] + bush_list
    cantmove = []
    def move(delx, dely):
        # global everything, cantmove
        for i in everything:
            i.rect.x -= delx
            i.rect.y -= dely
        
        for i in bullets:
            bullets[i][0] -= delx
            bullets[i][1] -= dely

    def goto(x, y):
        rel = relcords((localPlayer.x, localPlayer.y))
        move(x-rel[0], y-rel[1])

    def shoot(initial, final, range=700, speed=15):
        cords = list(initial)
        key = time.time()
        try:
            slope = (final[1]-initial[1]) / (final[0]-initial[0])
        except ZeroDivisionError:
            slope = float("inf")
            print("zerodivision error")
        delx = speed/sqrt((slope**2+1))
        dely = slope*delx
        def kill_bullet():
            try:
                del bullets[key]
            except Exception as e:
                print(f"ERROR2: {e}")
        def _s():
            r = 0
            if final[0] < initial[0]:#left
                nonlocal delx, dely
                delx = - delx
                dely = - dely
            else:#right
                pass

            moving = 1
            attack_flag = time.time()
            while r < range:
                bullets[key] = cords
                cords[0] += delx
                cords[1] += dely
                r += speed
                for w in wall_list:
                    if w.rect.collidepoint(cords):
                        kill_bullet()
                        return

                for rp in remotePlayers:
                    if remotePlayers[rp].rect.collidepoint(cords):
                        if cords[1] - remotePlayers[rp].rect.top > 23:
                            m = network_packet("damage", (rp, 5)) # normal shot damage=5
                        else:
                            m = network_packet("damage", (rp, 10)) # headshot damage=10
                            print("headshot")
                        sock.send(pickle.dumps(m))
                    
                        kill_bullet()
                        return
                time.sleep(0.02)

            kill_bullet()
                # del bullets[0]
        
        Thread(target=_s, daemon=True).start()

    mapImg = pygame.image.load('ffa_map.png')
    gun = mixer.Sound("gunshot.wav")
    f = font.Font("Minecraft.ttf", 12)
    font_text = f.render(username, False, (255, 255, 255), (0, 0, 0))
    font_text_box = font_text.get_rect()
    cantmove = [0,0,0,0]#up,right,left,down

    classes.init(localPlayer, wall_list, remotePlayers)
    graphics.init(sock, wall_list, localPlayer, remotePlayers)

    from random import randint
    goto(randint(30, 1100), randint(30, 500)) # start from a random position

    Thread(target=sendThread, daemon=True).start()
    Thread(target=recvThread, daemon=True).start()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and time.time() - attack_flag >= 0.2 and not dead:
                attack_flag = time.time()
                pos = pygame.mouse.get_pos()
                shoot(localPlayer.center, pos) # primary attack
                if not game_over:
                    m = [relcords((localPlayer.centerx, localPlayer.centery)), relcords((pos[0], pos[1]))]
                    sock.sendall(pickle.dumps(m))
                gun.set_volume(100)
                gun.play()

        screen.fill((30, 30, 30))
        screen.blit(mapImg , (center.rect.x, center.rect.y))

        #1-->left, 2-->right, 0--> None
        keys=pygame.key.get_pressed()
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT] ) and not cantmove[1]:
            move(speed, 0)
        if (keys[pygame.K_a] or keys[pygame.K_LEFT] ) and not cantmove[2]:
            move(-speed, 0)
        if (keys[pygame.K_w] or keys[pygame.K_UP] ) and not cantmove[0]:
            move(0, -speed)
        if (keys[pygame.K_s] or keys[pygame.K_DOWN] ) and not cantmove[3]:
            move(0, speed)
        if time.time() - move_flag >= 0.1:
            move_flag = time.time()
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                moving = 2
            elif (keys[pygame.K_a] or keys[pygame.K_LEFT]):
                moving = 1
            elif (keys[pygame.K_s] or keys[pygame.K_DOWN]) or (keys[pygame.K_w] or keys[pygame.K_UP]):
                if not moving:
                    moving = 2
            else:
                moving = 0

        for rp in remotePlayers:
            remotePlayers[rp].animate(screen)
        
        cantmove = [0,0,0,0]
        for w in wall_list:
            # w.draw(screen)
            if w.rect.colliderect(localPlayer):
                if abs(w.rect.right - localPlayer.left) < 15:
                    cantmove[2] = 1             
                elif abs(w.rect.left - localPlayer.right) < 15:
                    cantmove[1] = 1
                elif abs(w.rect.bottom - localPlayer.top) < 15:
                    cantmove[0] = 1
                elif abs(w.rect.top - localPlayer.bottom) < 15:
                    cantmove[3] = 1
        #health
        draw.rect(screen, (0, 0, 0), (45, 495, 210, 35))
        draw.rect(screen, (0, 255, 0), (50, 500, health*2, 25))

        update(screen) # update bullets
        animations(moving, localPlayer, screen) # animate localplayer
        font_text_box.center = (localPlayer.centerx, localPlayer.centery-45)
        screen.blit(font_text, font_text_box) # nametag
        draw.rect(screen, (0, 255, 0), center)

        for b in bush_list:
            if not localPlayer.colliderect(b.rect):
                b.draw(screen, alpha=False)
            else:
                b.draw(screen, alpha=True)
        if game_over !=  False:
            if game_over == "self":
                screen.blit(end_font.render(f"Victory!", True, (255, 255, 255), (0, 0, 0)), (250, 200))
            else:
                screen.blit(end_font.render(f"{game_over} WON", True, (255, 255, 255), (0, 0, 0)), (250, 200))

        pygame.display.flip()
        clock.tick(60)

