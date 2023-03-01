import pickle
import socket
import time
from select import select
from server_functions import send_to_all, send_to, sendall_to, sendall_to_all, shuffled_enumerate
from networking import network_packet, packet_split
import server_functions
from pygame import Rect


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = socket.gethostbyname(socket.gethostname())
port = 6979

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))
sock.listen()
print("Seek and Destroy started")

def main():
    online = {}
    waiting_list = {}
    server_functions.init(online)

    print("entering readyup loop")
    log = []
    while True:
        read_list = select(list(waiting_list)+[sock], [], [], 0.1)[0]
        if read_list:
            if read_list[0] is sock: # accept inbound connections
                conn, addr = sock.accept()
                online[conn] = None
                waiting_list[conn] = False
                
            else: # else data
                x = pickle.loads(read_list[0].recv(2048))

                if x[0] == "ready":
                    waiting_list[read_list[0]] = True
                    send_to_all(f"{x[1]} is ready")
                    log.append(f"{x[1]} is ready")
                    online[read_list[0]] = x[1]
                    print(f"{x[1]} is ready")
                
                elif x[0] == "join":
                    send_to(read_list[0], log) # send the previous log to new players
                    send_to_all(f"{x[1]} has joined the lobby.")
                    log.append(f"{x[1]} has joined the lobby.")
                    print(f"{x[1]} has joined")
                
                elif x[0] == "leave":
                    read_list[0].close()
                    del online[read_list[0]]
                    del waiting_list[read_list[0]]
                    send_to_all(f"{x[1]} has left the lobby.")
                    log.append(f"{x[1]} has left the lobby.")
                    print(f"{x[1]} has left")

                if all(waiting_list.values()) and list(waiting_list.values()) and len(waiting_list) >= 2:
                    print("exited readyup loop")
                    break

    send_to_all("Everyone is ready, game is starting in 5 seconds")
    time.sleep(5)
    send_to_all("break")
    time.sleep(1)

    for i, j in shuffled_enumerate(online):# modify online to map player names and their data
        online[j] = {
            "pl_no":i, # player no
            "usr":online[j], # username
            "health":100,
            "dead":False,
            "team":i%2,
            "cords":(0, 0),
            "lava_flag":0,
        }

    for i in online:
        d = {"me":[online[i]["pl_no"], online[i]["team"]]} # respective player's data
        d.update({j["pl_no"] : [j["usr"], j["team"]] for j in online.values()}) # other player's data
        send_to(i, d)
    
    # game variables
    spike_planted = False
    time_left = 90
    lava_list = [
        Rect(1363 , 0 , 1938-1363 , 23), Rect(1387 , 24 , 1914-1387 , 47-24), Rect(1387 , 48 , 1890-1387 , 71-48), Rect(1507 , 72 , 1795-1507 , 95-72), Rect(1603 , 96 , 1699-1603 , 119-96), Rect(1363 , 666 , 1914-1363 , 689-666), Rect(1387 , 618 , 1890-1387 , 665-618),
        Rect(1507 , 594 , 1794-1507 , 617-594), Rect(1603 , 570 , 1698-1603 , 593-570), Rect(1555 , 138 , 1626-1555 , 191-138), Rect(1747 , 168 , 1795-1747 , 191-168), Rect(1771 , 144 , 1818-1771 , 167-144), Rect(1531 , 436 , 1578-1531 , 459-436),
        Rect(1536 , 437 , 1603-1536 , 483-437), Rect(1771 , 258 , 1818-1771 , 281-258), Rect(1772 , 144 , 1819-1772 , 167-144), Rect(1747 , 168 , 1795-1747 , 191-168), Rect(1411 , 120 , 1435-1411 , 143-120),
        Rect(1435 , 144 , 1459-1435 , 167-144), Rect(1435 , 484 , 24 , 24), Rect(1459 , 508 , 23 , 23), Rect(1435 , 282 , 1458-1435 , 329-282), Rect(1459 , 258 , 1482-1459 , 329-258),Rect(1483 , 234 , 1506-1483 , 305-234),Rect(1507 , 234 , 1530-1507 , 281-234),
        Rect(1771 , 484 , 1794-1771 , 531-484),Rect(1795 , 460 , 1818-1795 , 531-460),Rect(1819 , 436 , 1842-1819 , 507-436),Rect(1843 , 436 , 1867-1843 , 483-436),Rect(1603 , 340 , 1626-1603 , 387-340),Rect(1627 , 316 , 1653-1627 , 411-316),Rect(1651 , 316 , 1674-1651 , 411-316),Rect(1675 , 340 , 1698-1675 , 387-340)
]
    winning_team = None
    def count_alive():
        c0, c1 = 0, 0
        for s in online:
            if not online[s]["dead"] and online[s]["team"] == 0:
                c0 += 1
            elif not online[s]["dead"] and online[s]["team"] == 1:
                c1 += 1
        return c0, c1  # team0, team1

    def sql_update():
        nonlocal winning_team
        name_player = ''
        new_trophies = 0
        new_s_and_d_play = 0
        new_s_and_d_wins = 0
        rank = 0
        from mysql import connector
        sql_connect = connector.connect(host = 'localhost' , user = 'root' , passwd = 'newpassword', auth_plugin='mysql_native_password')
        cur = sql_connect.cursor()
        cur.execute('use game;')
        a = []
        cur.execute('select Name from leaderboard;')
        for b in cur:
             a = a + list(b)
        for s in online:
            name_player = online[s]['usr']
            new_trophies = 0
            new_s_and_d_wins = 0
            new_s_and_d_play = 1
            if online[s]['team'] == winning_team:
                new_trophies = 7
                new_s_and_d_wins = 1
            else:
                new_trophies = -5
                new_s_and_d_wins = 0
            if name_player not in a:
                rank = 0
                cur.execute(f'insert into leaderboard values ({rank} , "{name_player}" , 0 , 0 , 0 , 0 , {new_s_and_d_play} , {new_s_and_d_wins} , {new_s_and_d_play} , {new_s_and_d_wins} , {new_trophies});')
                sql_connect.commit()
            elif name_player in a:
                rank = 0
                z = []
                cur.execute('select * from leaderboard;')
                for i in cur:
                    z.append(list(i))
                for rec in z:
                    if rec[1] == name_player:
                        data = rec
                        break
                cur.execute(f"update leaderboard set number_of_seek_and_destroy_games_played = {int(data[6])+1}, number_of_seek_and_destroy_wins = {int(data[7])+ new_s_and_d_wins} , total_games_played = {int(data[8])+1} , total_wins = {int(data[9])+new_s_and_d_wins} , total_trophies = {int(data[10])+new_trophies} where Name = '{name_player}'")
            # Rank 
            cur.execute('select name from leaderboard order by total_trophies desc;')
            count = 0
            for i in list(cur):
                count = count + 1
                cur.execute(f"update leaderboard set _Rank_ = {count} where name = '{i[0]}';")
                sql_connect.commit()

    dat = {}
    flag = time.time()
    timer_flag = time.time()
    while True:
        r = select(list(online.keys()), [], [], 0.01)[0]
        if r:
            for i in r:
                try:
                    temp = i.recv(1024)
                    for packet in packet_split(temp):
                        try:
                            d = pickle.loads(packet)
                        except:
                            print("pickle error")
                            print(temp)
                            print(packet)
                            exit()

                        if type(d) == list and len(d) == 3: #player movement
                            dat[d[0]] = d[1::]
                            online[i]["cords"] = d[1]

                        elif type(d) == list and len(d) == 2: #gun shot
                            try:
                                dat["shots"].append([online[i]["pl_no"]]+d)
                            except KeyError:
                                dat["shots"] = [[online[i]["pl_no"]]+d]
                        
                        elif type(d) == network_packet:

                            if d.heading == "damage":
                                # reduce the given players health by damage
                                for s in online:
                                    if online[s]["pl_no"] == d.data[0]:
                                        online[s]["health"] -= d.data[1] #reduce
                                        
                                        if online[s]["health"] > 0:
                                            sendall_to(s, network_packet("health", online[s]["health"]))
                                        else: # else the player is dead
                                            online[s]["dead"] = True
                                            sendall_to_all(network_packet("dead", [online[s]["pl_no"], online[i]["pl_no"]]))
                            
                            elif d.heading == "spike":
                                if d.data == True:
                                    spike_planted = True
                                    sendall_to_all(network_packet("spike", True))
                                    time_left = 30
                                else:
                                    spike_planted = False
                                    sendall_to_all(network_packet("spike", False))
                                    # time.sleep(1)
                                    sendall_to_all(network_packet("game over", [1, "diffused"]))
                                    winning_team = 1
                                    sql_update()
                                    return
                                    

                        else:
                            print("unknown data received:", d)

                except ConnectionResetError:
                    print("connection reset error")
                    pass
        
        # timer
        if time.time() - timer_flag >= 1:
            time_left -= 1
            timer_flag = time.time()
            send_to_all(network_packet("timer", time_left))

            if time_left <= 0:
                # time over
                if spike_planted:
                    print("spike detonated")
                    # time.sleep(1)
                    sendall_to_all(network_packet("game over", [0, "detonated"]))
                    winning_team = 0
                    sql_update()
                    return
                elif not spike_planted:
                    print("attackers timeout")
                    time.sleep(1)
                    sendall_to_all(network_packet("game over", [1, "timeout"]))
                    winning_team = 1
                    sql_update()
                    return
        
        # collision with lava
        for s in online:
            if not online[s]["dead"]:
                for l in lava_list:
                    if Rect(online[s]["cords"][0]+10, online[s]["cords"][1]+45, 30, 15).colliderect(l) and time.time() - online[s]["lava_flag"] >= 0.5: # if player feet collides lava
                        online[s]["lava_flag"] = time.time()
                        online[s]["health"] -= 5
                        if online[s]["health"] > 0:
                            sendall_to(s, network_packet("health", online[s]["health"]))
                        else:
                            online[s]["dead"] = True
                            sendall_to_all(network_packet("dead", [online[s]["pl_no"], "lava"]))
                        break

        # check for full team deaths
        c0, c1 = count_alive()
        if c0 == 0 and not spike_planted:
            time.sleep(1)
            sendall_to_all(network_packet("game over", [1, "dead"]))
            winning_team = 1
            sql_update()
            return
        if c0 > 0 and c1 == 0 and spike_planted:
            time.sleep(1)
            sendall_to_all(network_packet("game over", [0, "dead"]))
            winning_team = 0
            sql_update()
            return
        
        if dat and time.time() - flag >= 0.1: # send data to players every 0.1 seconds

            for i in online.keys():
                send_to(i, {a:b for a, b in dat.items() if a != online[i]["pl_no"]}) # send every other players' data and not self's


            flag = time.time()
            dat = {}


while True:
    try:
        main()
    except KeyboardInterrupt:
        sock.close()
        break
