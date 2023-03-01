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
from functions import relcords, realcords, dist
import pygame.transform
from pygame import font, mixer
from networking import network_packet, server_ip, packet_split
import os


def run(username):
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    del path

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip , 6978))

    import lobby
    is_ready = lobby.main(sock, username, "Heist")
    if not is_ready:
        exit()

    health = 100
    dead = False
    pygame.init()
    screen = pygame.display.set_mode((900,600))

    moving = 0
    move_flag = 0
    attack_flag = 0
    game_over = False

    pl_list = pickle.loads(sock.recv(2048))
    player_no = pl_list["me"][0] #local player number
    team_no = pl_list["me"][1]

    localPlayer = pygame.Rect((400, 250, 50, 70))
    remotePlayers = {}
    for i in pl_list:
        if i != "me" and i != player_no:
            if pl_list[i][1] == team_no:
                remotePlayers[i] = player(pl_list[i][0], same_team=True)
            else:#opponent team
                remotePlayers[i] = player(pl_list[i][0], same_team=False)

    class localSafe():
        def draw(*args):
            pass
    class remoteSafe():
        def draw(*args):
            pass

    #  two safe objects
    if team_no == 0:
        localSafe.rect = pygame.Rect((50, 300, 100, 100))
        remoteSafe.rect = pygame.Rect((1650, 100, 100, 100))
    elif team_no == 1:
        localSafe.rect = pygame.Rect((1650, 100, 100, 100))
        remoteSafe.rect = pygame.Rect((50, 300, 100, 100))
    remoteSafe.health = 350
    localSafe.health = 350

    wall_list = [wall((272, 83, 32, 32*3)), wall((396, 281, 32*4, 32)), localSafe, remoteSafe,
                wall((1302, 115, 32*4, 32)) , wall((1555,249,32,32*3)),
                wall((678, 141, 148, 60)) , wall((970, 277, 133, 71)),
                wall((847, 373, 36, 62)),wall((910 , 0 , 40 , 63)),
                wall((0, 0, 10, 438)),#Borders
                wall((20, 0, 1800, 10)),
                wall((20, 438, 1800, 10)),
                wall((1800, 0, 10, 438))] # create more walls and change positions according to map ## and also i added the safes so that we can not walk over it
    end_font = font.Font("Minecraft.ttf", 64)
    timer_font = font.Font("Minecraft.ttf", 18)
    f = font.Font("Minecraft.ttf", 12)
    font_text = f.render(username, False, (255, 255, 255), (0, 0, 0))
    font_text_box = font_text.get_rect()

    def sendThread():
        m = [player_no, relcords((400, 250)), moving]
        sock.send(pickle.dumps(m))
        prev = [relcords((400, 250)), moving]
        while True:
            if relcords((400, 250)) != prev[0] or moving != prev[1]:
                m = [player_no, relcords((400, 250)), moving]
                prev = relcords((400, 250)), moving
                if not game_over and not dead:
                    sock.send(pickle.dumps(m))
                elif game_over:
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
                    
                    elif dat.heading == "safe health":
                        if dat.data[0] != team_no:
                            remoteSafe.health = dat.data[1]
                        else:
                            localSafe.health = dat.data[1]
                    
                    elif dat.heading == "dead":
                        if dat.data[0] == player_no:
                            nonlocal dead
                            dead = True
                            health = 0
                            localPlayer.size = (1, 1)
                            graphics.dead = 1 # death animation

                        else:
                            remotePlayers[dat.data[0]].kill()
                        print(pl_list[dat.data[0]][0], "has been shot by", pl_list[dat.data[1]][0], "\a")
                    
                    elif dat.heading == "respawn":
                        if dat.data == player_no:
                            # nonlocal dead
                            dead = False
                            localPlayer.size = (50, 70)
                            graphics.dead = False

                            # go back to start
                            if team_no == 0:
                                goto(300, 250)
                            else:
                                goto(1700, 200)

                        else:
                            remotePlayers[dat.data].respawn()


                    elif dat.heading == "game over":
                        nonlocal game_over, running
                        if dat.data == team_no: # win
                            game_over = "win"
                            remoteSafe.health = 0
                        else: # lose
                            game_over = "lose"
                            localSafe.health = 0
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
    bush_list = [bush((200, 300), type=2), bush((1350, 300), type=2)]
    everything = wall_list + list(remotePlayers.values()) + [center] + bush_list

    def move(delx, dely):
        nonlocal everything, cantmove
        for i in everything:
            i.rect.x -= delx
            i.rect.y -= dely
        
        for i in bullets:
            bullets[i][0] -= delx
            bullets[i][1] -= dely
        
        # change safe positions # already changing as they are a part of walls list
        # localSafe.rect.x -= delx
        # localSafe.rect.y -= dely
        # remoteSafe.rect.x -= delx
        # remoteSafe.rect.y -= dely

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
            nonlocal remotePlayers, player_no, attack_flag, moving, team_no
            r = 0
            if final[0] < initial[0]:#left
                nonlocal delx, dely
                delx = -delx
                dely = -dely
            else:#right
                pass
            while r < range:
                bullets[key] = cords
                cords[0] += delx
                cords[1] += dely
                r += speed

                if remoteSafe.rect.collidepoint(cords) and not game_over:
                    # remoteSafe.health -= 10
                    if team_no == 0:
                        sock.sendall(pickle.dumps(network_packet("safe damage", [1, 10])))
                    else:
                        sock.sendall(pickle.dumps(network_packet("safe damage", [0, 10])))
                    kill_bullet()
                    return

                for w in wall_list:
                    if w.rect.collidepoint(cords) and w is not localSafe:
                        kill_bullet()
                        return
                
                for rp in remotePlayers:
                    if not remotePlayers[rp].same_team and remotePlayers[rp].rect.collidepoint(cords):
                        if cords[1] - remotePlayers[rp].rect.top > 23:
                            m = network_packet("damage", (rp, 7)) # normal shot damage=7
                        else:
                            m = network_packet("damage", (rp, 12)) # headshot damage=12
                            print("headshot")
                        sock.send(pickle.dumps(m))
                    
                        kill_bullet()
                        return
                time.sleep(0.02)

            kill_bullet()
                # del bullets[0]
        
        Thread(target=_s, daemon=True).start()

    mapImg = pygame.image.load('heist_map.png')
    gun = mixer.Sound("gunshot.wav")
    safe_img = pygame.image.load('sprites/chest.png')
    safe_img = pygame.transform.scale(safe_img, (100, 100))
    cantmove = [0,0,0,0]#up,right,left,down

    classes.init(localPlayer, wall_list, remotePlayers)
    graphics.init(sock, wall_list, localPlayer, remotePlayers)

    def goto(x, y):
        rel = relcords((localPlayer.x, localPlayer.y))
        move(x-rel[0], y-rel[1])

    if team_no == 0:
        goto(300, 250)
    else:
        goto(1700, 200)

    Thread(target=sendThread, daemon=True).start()
    Thread(target=recvThread, daemon=True).start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and time.time() - attack_flag >= 0.55 and not dead and not game_over:
                pos = pygame.mouse.get_pos()
                attack_flag = time.time()
                def burst():
                    for i in range(3):
                        if not dead and not game_over:
                            shoot(localPlayer.center, pos)
                            gun.set_volume(100)
                            gun.play()
                            m = [relcords((localPlayer.centerx, localPlayer.centery)), relcords((pos[0], pos[1]))]
                            sock.sendall(pickle.dumps(m))
                        time.sleep(0.15)
                Thread(target=burst).start()

        screen.fill((30, 30, 30))
        screen.blit(mapImg , (center.rect.x, center.rect.y))

        #1-->left, 2-->right, 0--> None
        if not dead and not game_over:
            keys=pygame.key.get_pressed()
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT] ) and not cantmove[1]:
                move(speed, 0)
            if (keys[pygame.K_a] or keys[pygame.K_LEFT] ) and not cantmove[2]:
                move(-speed, 0)
            if (keys[pygame.K_w] or keys[pygame.K_UP] ) and not cantmove[0]:
                move(0, -speed)
            if (keys[pygame.K_s] or keys[pygame.K_DOWN] ) and not cantmove[3]:
                move(0, speed)
            if time.time() - attack_flag >= 0.3:
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
        
        
        if localSafe.health > 0 :            
            screen.blit(safe_img, (localSafe.rect.x, localSafe.rect.y-5))
        if remoteSafe.health > 0 :
            screen.blit(safe_img, (remoteSafe.rect.x, remoteSafe.rect.y-5))


        #health 
        draw.rect(screen, (0, 0, 0), (45, 495, 210, 35))
        draw.rect(screen, (0, 255, 0), (50, 500, health*2, 25))

        update(screen)
        animations(moving, localPlayer, screen)
        font_text_box.center = (localPlayer.centerx, localPlayer.centery-45)
        screen.blit(font_text, font_text_box) # nametag
        draw.rect(screen, (0, 255, 0), center)

        for b in bush_list:
            if not localPlayer.colliderect(b.rect):
                b.draw(screen, alpha=False)
            else:
                b.draw(screen, alpha=True)

        # safe health
        draw.rect(screen, (0, 255, 0), (localSafe.rect.x-20, localSafe.rect.y-35 , int(localSafe.health/2), 15))
        draw.rect(screen, (255, 0, 0), (remoteSafe.rect.x-20, remoteSafe.rect.y -35, int(remoteSafe.health/2), 15))

        if not game_over:
            pygame.display.flip()
        else: # before ending
            screen.fill((30, 30, 30))
            screen.blit(mapImg , (center.rect.x, center.rect.y))
            for rp in remotePlayers:
                remotePlayers[rp].animate(screen)
            if localSafe.health > 0 :            
                screen.blit(safe_img, (localSafe.rect.x, localSafe.rect.y-40))
            if remoteSafe.health > 0 :
                screen.blit(safe_img, (remoteSafe.rect.x, remoteSafe.rect.y-40))
            for b in bush_list:
                if not localPlayer.colliderect(b.rect):
                    b.draw(screen, alpha=False)
                else:
                    b.draw(screen, alpha=True)
            # safe health
            draw.rect(screen, (0, 255, 0), (localSafe.rect.x, localSafe.rect.y-40 , int(localSafe.health/2), 15))
            draw.rect(screen, (255, 0, 0), (remoteSafe.rect.x, remoteSafe.rect.y -40, int(remoteSafe.health/2), 15))
            #health 
            draw.rect(screen, (0, 0, 0), (45, 495, 210, 35))
            draw.rect(screen, (0, 255, 0), (50, 500, health*2, 25))

            update(screen)
            animations(moving, localPlayer, screen)
            draw.rect(screen, (0, 255, 0), center)
            if game_over == "win":
                screen.blit(end_font.render("YOU WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                screen.blit(timer_font.render("Opponent's treasure has been Destroyed.", False, (255, 255, 255), (0, 0, 0)), (300, 320))
            elif game_over == "lose":
                screen.blit(end_font.render("YOU LOSE", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                screen.blit(timer_font.render("Your treasure has been Destroyed.", False, (255, 255, 255), (0, 0, 0)), (300, 320))
            pygame.display.flip()
            time.sleep(6)
            return

        clock.tick(60)

