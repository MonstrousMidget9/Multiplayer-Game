import socket
import pygame
from pygame import draw, font, transform, mixer
from threading import Thread
import time
import pickle
from math import sqrt
from classes import wall, player, center
from graphics import speed, animations, update, bullets
import classes, graphics
from functions import dist, relcords, realcords
from networking import network_packet, server_ip, packet_split
import os

def run(username):
    path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(path)
    del path

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip , 6979))

    import lobby
    is_ready = lobby.main(sock, username, "Seek And Destroy")
    if not is_ready:
        exit()

    health = 100
    pygame.init()
    screen = pygame.display.set_mode((900,600))

    moving = 0
    game_over = False
    attack_flag = 0
    dead = False

    pl_list = pickle.loads(sock.recv(2048))
    player_no = pl_list["me"][0] #local player number
    team_no:int = pl_list["me"][1]

    localPlayer = pygame.Rect((400, 250, 50, 70))
    remotePlayers = {}
    for i in pl_list:
        if i != "me" and i != player_no:
            if pl_list[i][1] == team_no:
                remotePlayers[i] = player(pl_list[i][0], same_team=True)
            else:#opponent team
                remotePlayers[i] = player(pl_list[i][0], same_team=False)

    wall_list = [wall((546, 0, 551, 29)), wall((1026, 30, 31, 269)), wall((834 ,180 ,191 ,29)), wall((578 ,180 ,769-578 ,29)),
                wall((946, 113, 1024-946, 178-113)), wall((657, 29, 711-657, 89-29)),
                wall((752, 312, 851-752, 372-312)), wall((546, 630, 1057-546, 689-630)),
                wall((963 ,510 ,1025-963 ,551-510)), wall((578 , 510 , 727-578 , 539-510)), wall((546 , 30 , 577-546 , 59-30)), wall((546 , 150 , 577-546 , 539-150)),
                wall((578 , 480 , 769-578 , 509-480)), wall((834 , 480 , 1025-834 , 509-480)), wall((1026 , 390 , 1057-1026 , 659-390)) , wall((2192 , 0 , 2702-2192 , 121)),
                wall((2175 , 561 , 2703-2175 , 689-561)), wall((2571 , 104 , 2700-2571 , 580-104)) , wall((2256 , 268 , 2390-2256 , 426-268)),
                wall((0, 0, 10, 700)),# boundary
                wall((20,0 , 2800, 10)),# boundary
                wall((20, 700, 2800, 10)),# boundary
                wall((2800, 0, 10, 700))# boundary
    ]

    def sendThread():
        m = [player_no, relcords((400, 250)), moving]
        sock.send(pickle.dumps(m))
        prev = [relcords((400, 250)), moving]
        while True:
            time.sleep(0.09)
            if relcords((400, 250)) != prev[0] or moving != prev[1]:
                m = [player_no, relcords((400, 250)), moving]
                prev = relcords((400, 250)), moving
                if dead or game_over:
                    return
                if not game_over:
                    sock.send(pickle.dumps(m))
                else:
                    return

    def recvThread():
        nonlocal health
        while True:
            try:
                for packet in packet_split(sock.recv(2048)):
                    dat = pickle.loads(packet)
                    if type(dat) == network_packet:
                        if dat.heading == "health":
                            nonlocal health
                            health = dat.data
                        
                        elif dat.heading == "timer":
                            nonlocal time_left, spike_planted
                            time_left = dat.data
                            if spike_planted:
                                def play_ticks(ticks_per_second:int):
                                    for i in range(ticks_per_second):
                                        tick.play()
                                        time.sleep(1/ticks_per_second)
                                if time_left < 10 and time_left > 5:
                                    Thread(target=play_ticks, args=[2]).start() # 2 ticks per second
                                elif time_left <= 5:
                                    Thread(target=play_ticks, args=[4]).start() # 4 ticks per second
                                else:
                                    tick.play()
                        
                        elif dat.heading == "spike":
                            if dat.data == True:
                                spike_planted = True
                                def _spike():
                                    mixer.Sound("spike.wav").play()
                                    time.sleep(1)
                                    mixer.Sound("planted.wav").play()
                                Thread(target=_spike).start()
                            else:
                                spike_planted = False
                        
                        elif dat.heading == "dead":
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

                                    point[0] -= delx
                                    point[1] -= dely

                                    localPlayer.x -= delx
                                    localPlayer.y -= dely
                                nonlocal move
                                move = _move # dettach the player object while moving

                            elif dat.data[0] in remotePlayers:
                                remotePlayers[dat.data[0]].kill()
                            if dat.data[1] == "lava":
                                print(pl_list[dat.data[0]][0], "tried to swim in lava.", "\a")
                            else:
                                print(pl_list[dat.data[0]][0], "has been shot by", pl_list[dat.data[1]][0], "\a")

                        elif dat.heading == "game over":
                            nonlocal game_over
                            game_over = dat.data
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

            except Exception as e:
                print("bad data received:", type(e), e)

    point = [2494, 344]
    clock = pygame.time.Clock()
    bush_list = []
    everything = wall_list + list(remotePlayers.values()) + [center] + bush_list
    cantmove = []
    def move(delx, dely):
        nonlocal everything, point
        for i in everything:
            i.rect.x -= delx
            i.rect.y -= dely
        
        for i in bullets:
            bullets[i][0] -= delx
            bullets[i][1] -= dely

        point[0] -= delx
        point[1] -= dely

    def goto(x, y):
        rel = relcords((localPlayer.x, localPlayer.y))
        move(x-rel[0], y-rel[1])

    if team_no == 0:
        goto(150, 360)
    else:
        goto(1210, 350)

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

                for w in wall_list:
                    if w.rect.collidepoint(cords):
                        kill_bullet()
                        return
                
                for rp in remotePlayers:
                    if not remotePlayers[rp].same_team and remotePlayers[rp].rect.collidepoint(cords):
                        if cords[1] - remotePlayers[rp].rect.top > 23:
                            m = network_packet("damage", (rp, 5)) # normal shot damage=5
                        else:
                            m = network_packet("damage", (rp, 8)) # headshot damage=8
                            print("headshot")
                        sock.send(pickle.dumps(m))
                    
                        kill_bullet()
                        return
                time.sleep(0.02)

            kill_bullet()
                # del bullets[0]
        
        Thread(target=_s, daemon=True).start()

    mapImg = pygame.image.load('snd_map.png')
    spikeImg = pygame.image.load('sprites/spike_.png')
    spikeImg = transform.scale(spikeImg, (30, 50))
    f = font.Font("Minecraft.ttf", 12)
    font_text = f.render(username, False, (255, 255, 255), (0, 0, 0))
    font_text_box = font_text.get_rect()
    cantmove = [0,0,0,0]#up,right,left,down

    classes.init(localPlayer, wall_list, remotePlayers)
    graphics.init(sock, wall_list, localPlayer, remotePlayers)

    Thread(target=sendThread, daemon=True).start()
    Thread(target=recvThread, daemon=True).start()
    time_left = 90
    timer_font = font.Font("Minecraft.ttf", 18)
    end_font = font.Font("Minecraft.ttf", 64)
    spike_planted = False
    spike_planting_flag = None
    spike_isplanting = False
    running = True
    gun = mixer.Sound("gunshot.wav")
    tick = mixer.Sound("tick.wav")
    detonate = mixer.Sound("detonate.wav")
    diffuse = mixer.Sound("diffuse.wav")
    while running:
        # try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and time.time() - attack_flag >= 0.2 and not dead and not spike_isplanting:
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
        # draw.circle(screen, (255, 255, 0), point, radius=50)
        if spike_planted:
            screen.blit(spikeImg, (point[0]-10, point[1]-20))

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

        if team_no == 0 and not dead:
            if keys[pygame.K_e] and dist(localPlayer.center, point) < 50 and not spike_isplanting and not spike_planted:
                spike_isplanting = True
                spike_planting_flag = time.time()
            
            if spike_isplanting:
                if (time.time()-spike_planting_flag) <= 5 and not moving:
                    draw.rect(screen, (0, 0, 0), (245, 350, 110, 25))
                    draw.rect(screen, (0, 255, 255), (250, 355, (time.time()-spike_planting_flag)*20, 15))
                elif moving: # cancel spike plant when moved
                    spike_planted = False
                    spike_isplanting = False
                else:
                    sock.sendall(pickle.dumps(network_packet("spike", True)))
                    def _spike():
                        mixer.Sound("spike.wav").play()
                        time.sleep(1)
                        mixer.Sound("planted.wav").play()
                    Thread(target=_spike).start()

                    spike_isplanting = False

        elif not dead:
            if keys[pygame.K_e] and dist(localPlayer.center, point) < 50 and spike_planted:
                spike_isplanting = True
                spike_planting_flag = time.time()

            if spike_isplanting:
                if (time.time()-spike_planting_flag) <= 5 and not moving:
                    draw.rect(screen, (0, 0, 0), (245, 350, 110, 25))
                    draw.rect(screen, (0, 255, 255), (250, 355, (time.time()-spike_planting_flag)*20, 15))
                elif moving:
                    spike_planted = True
                    spike_isplanting = False
                else:
                    sock.sendall(pickle.dumps(network_packet("spike", False)))
                    spike_isplanting = False


        #health 
        draw.rect(screen, (0, 0, 0), (45, 495, 210, 35))
        draw.rect(screen, (0, 255, 0), (50, 500, health*2, 25))

        update(screen) # update
        animations(moving, localPlayer, screen) # animations
        font_text_box.center = (localPlayer.centerx, localPlayer.centery-45)
        screen.blit(font_text, font_text_box) # nametag
        draw.rect(screen, (0, 255, 0), center)

        for b in bush_list:
            if not localPlayer.colliderect(b.rect):
                b.draw(screen, alpha=False)
            else:
                b.draw(screen, alpha=True)

        if spike_planted:
            screen.blit(timer_font.render(f"Spike will detonate in:{time_left}", False, (255, 255, 255), (150, 150, 150)), (430, 500))
        else:
            screen.blit(timer_font.render(f" {time_left} ", False, (255, 255, 255), (150, 150, 150)), (430, 500))

        if team_no == 0:
            screen.blit(timer_font.render("Attackers", False, (255, 255, 255), (255, 115, 0)), (0, 0))
        else:
            screen.blit(timer_font.render("Defenders", False, (255, 255, 255), (117, 170, 255)), (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
        if game_over: # game end
            if game_over[0] == 0:
                if game_over[1] == "detonated":
                    screen.blit(end_font.render("ATTACKERS WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                    screen.blit(timer_font.render("The Spike has \nDetonated.", False, (255, 255, 255), (0, 0, 0)), (430, 500))
                    detonate.play()
                elif game_over[1] == "dead":
                    screen.blit(end_font.render("ATTACKERS WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                    screen.blit(timer_font.render("All the Denfenders have been killed.", False, (255, 255, 255), (0, 0, 0)), (430, 500))
            elif game_over[0] == 1:
                if game_over[1] == "timeout":
                    screen.blit(end_font.render("DEFENDERS WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                    screen.blit(timer_font.render("The Attackers werenot able\n to plant the spike in time.", False, (255, 255, 255), (0, 0, 0)), (430, 500))
                elif game_over[1] == "diffused":
                    screen.blit(end_font.render("DEFENDERS WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                    screen.blit(timer_font.render("The Spike has been Diffused.", False, (255, 255, 255), (0, 0, 0)), (430, 500))
                    diffuse.play()
                elif game_over[1] == "dead":
                    screen.blit(end_font.render("DEFENDERS WIN", True, (255, 255, 255), (0, 0, 0)), (250, 200))
                    screen.blit(timer_font.render("All the Attackers have been killed.", False, (255, 255, 255), (0, 0, 0)), (430, 500))
            
            pygame.display.flip()
            time.sleep(10)
            return
