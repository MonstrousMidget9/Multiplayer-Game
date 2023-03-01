import pickle
import socket
import time
from select import select
from server_functions import send_to_all, send_to, sendall_to, sendall_to_all, shuffled_enumerate
from networking import network_packet, packet_split
import server_functions

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = socket.gethostbyname(socket.gethostname())
port = 6978

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))
sock.listen()
print("Heist server started")

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

    safe_health_team0 = 350
    safe_health_team1 = 350
    winning_team = None

    for i, j in shuffled_enumerate(online):# modify online to map player names and their data
        online[j] = {
            "pl_no":i, # player no
            "usr":online[j], # username
            "health":100,
            "dead":False,
            "death_flag":0,
            "team":i%2,
        }

    for i in online:
        d = {"me":[online[i]["pl_no"], online[i]["team"]]} # respective player's data
        d.update({j["pl_no"] : [j["usr"], j["team"]] for j in online.values()}) # other player's data
        send_to(i, d)
    
    def sql_update():
        nonlocal winning_team
        name_player = ''
        new_trophies = 0
        new_heist_play = 0
        new_heist_wins = 0
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
            new_heist_wins = 0
            new_heist_play = 1
            if online[s]['team'] == winning_team:
                new_trophies = 7
                new_heist_wins = 1
            else:
                new_trophies = -5
                new_heist_wins = 0
            if name_player not in a:
                rank = 0
                cur.execute(f'insert into leaderboard values ({rank} , "{name_player}" , 0 , 0 , {new_heist_play} , {new_heist_wins} , 0 , 0 , {new_heist_play} , {new_heist_wins} , {new_trophies});')
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
                cur.execute(f"update leaderboard set number_of_heist_games_played = {int(data[4])+1}, number_of_heist_wins = {int(data[5])+ new_heist_wins} , total_games_played = {int(data[8])+1} , total_wins = {int(data[9])+new_heist_wins} , total_trophies = {int(data[10])+new_trophies} where Name = '{name_player}'")
            # Rank 
            cur.execute('select name from leaderboard order by total_trophies desc;')
            count = 0
            for i in list(cur):
                count = count + 1
                cur.execute(f"update leaderboard set _Rank_ = {count} where name = '{i[0]}';")
                sql_connect.commit()


    dat = {}
    flag = time.time()
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
                                            online[s]["death_flag"] = time.time()
                                            sendall_to_all(network_packet("dead", [online[s]["pl_no"], online[i]["pl_no"]]))
                            
                            if d.heading == "safe damage":
                                # reduce the opponent team safe health
                                if d.data[0] == 0:
                                    safe_health_team0 -= d.data[1]
                                    if safe_health_team0 > 0:
                                        sendall_to_all(network_packet("safe health", [0, safe_health_team0]))
                                    else:
                                        sendall_to_all(network_packet("game over", 1)) # team 1 wins
                                        winning_team = 1
                                        sql_update()
                                        return
                                else:
                                    safe_health_team1 -= d.data[1]
                                    if safe_health_team1 > 0:
                                        sendall_to_all(network_packet("safe health", [1, safe_health_team1]))
                                    else:
                                        sendall_to_all(network_packet("game over", 0)) # team 0 wins
                                        winning_team = 0
                                        sql_update()
                                        return
                        else:
                            print("unknown data received:", d)
                    


                except ConnectionResetError:
                    print("connection reset error")
                    pass
        
        # check for dead people and check if 5 seconds is past their death_flag
        for s in online:
            if online[s]["dead"] and time.time() - online[s]["death_flag"] >= 5:
                sendall_to_all(network_packet("respawn", online[s]["pl_no"]))
                online[s]["health"] = 100
                online[s]["dead"] = False
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
