import pickle
import socket
import time
from select import select
from server_functions import send_to_all, send_to, sendall_to, sendall_to_all
from networking import network_packet, packet_split
import server_functions

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = socket.gethostbyname(socket.gethostname())
port = 6977

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))
sock.listen()
print("Free for All server started")

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

    positions = []

    for i, j in enumerate(online):# modify online to map player names and their data
        online[j] = {
            "pl_no":i, # player no
            "usr":online[j], # username
            "health":100,
            "dead":False,
            "heal_flag":0,
            "last_hit_flag":0,
        }

    for i in online:
        send_to(i, [online[i]["pl_no"]]+list([j["pl_no"], j["usr"]] for j in online.values())) # send to each player their number and other players' usernames
        
    dat = {}
    flag = time.time()
    while True:
        r = select(list(online.keys()), [], [], 0.01)[0]
        if r:
            for i in r:
                try:
                    temp = i.recv(1024)
                    if not temp:
                        sendall_to_all(network_packet("dead", [online[i]["pl_no"], online[i]["pl_no"]]))
                        del online[i]
                        continue
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
                                        online[s]["last_hit_flag"] = time.time()
                                        
                                        if online[s]["health"] > 0:
                                            sendall_to(s, network_packet("health", online[s]["health"]))
                                        else: # else the player is dead
                                            online[s]["dead"] = True
                                            positions.append(s)
                                            sendall_to_all(network_packet("dead", [online[s]["pl_no"], online[i]["pl_no"]]))
                        else:
                            print("unknown data received:", d)

                    # check for no of alive players
                    c = 0
                    lastman = None
                    lastman_s = None
                    for s in online:
                        if not online[s]["dead"]:
                            c += 1
                            lastman = online[s]["pl_no"]
                            lastman_s = s
                    if c == 1:
                        positions.append(lastman_s)
                        time.sleep(3)
                        sendall_to_all(network_packet("game over", lastman))

                        positions = positions[::-1]

                        # sql database update
                        name_player = ''
                        new_trophies = 0
                        new_ffa_play = 0
                        new_ffa_wins = 0
                        rank = 0
                        from mysql import connector
                        sql_connect = connector.connect(host = 'localhost' , user = 'root' , passwd = 'newpassword', auth_plugin='mysql_native_password')
                        cur = sql_connect.cursor()
                        cur.execute('use game;')
                        a = []
                        cur.execute('select Name from leaderboard;')
                        for b in cur:
                            a = a + list(b)
                        for j in range(len(positions)):
                            name_player = online[positions[j]]["usr"]
                            new_trophies = 0
                            new_ffa_wins = 0
                            new_ffa_play = 1
                            if positions[j] == positions[0] :
                                new_trophies = 10
                                new_ffa_wins = 1
                            elif positions[j] == positions[-1] :
                                new_trophies = -5
                                new_ffa_wins = 0
                            else:
                                new_ffa_wins = 0
                                new_trophies = 10-(15//(len(positions)-1))*j
                            if name_player not in a:
                                rank = 0
                                cur.execute(f'insert into leaderboard values ({rank} , "{name_player}" , {new_ffa_play} , {new_ffa_wins} , 0 , 0 , 0 , 0 , {new_ffa_play} , {new_ffa_wins} , {new_trophies});')
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
                                cur.execute(f"update leaderboard set number_of_ffa_games_played = {int(data[2])+1}, number_of_ffa_wins = {int(data[3])+new_ffa_wins} , total_games_played = {int(data[8])+1} , total_wins = {int(data[9])+new_ffa_wins} , total_trophies = {int(data[10])+new_trophies} where Name = '{name_player}'")
                            # Rank 
                            cur.execute('select name from leaderboard order by total_trophies desc;')
                            count = 0
                            for i in list(cur):
                                count = count + 1
                                cur.execute(f"update leaderboard set _Rank_ = {count} where name = '{i[0]}';")
                                sql_connect.commit()
                        return # game over

                except ConnectionResetError:
                    print("connection reset error")
                    pass
        
        # heal the players
        for s in online:
            if not online[s]["dead"] and online[s]["health"] != 100 and time.time() - online[s]["last_hit_flag"] >= 5:
                if time.time() - online[s]["heal_flag"] >= 1:
                    online[s]["heal_flag"] = time.time()
                    if online[s]["health"] < 95:
                        online[s]["health"] += 5
                    else:
                        online[s]["health"] = 100
                    sendall_to(s, network_packet("health", online[s]["health"]))

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
