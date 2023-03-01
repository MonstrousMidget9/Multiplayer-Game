import pickle
import socket
from mysql import connector
from tabulate import tabulate

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = socket.gethostbyname(socket.gethostname())
port = 6969

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))
sock.listen()

try:
    open("logins.dat", "rb")
except FileNotFoundError:
    with open("logins.dat", "wb") as f:
        pickle.dump({}, f)

print("database server started!")

while True:
    conn, addr = sock.accept()
    
    try:
        request = conn.recv(1024)
        request = request.decode()
    except:
        sql_connect = connector.connect(host = 'localhost' , user = 'root' , passwd = 'newpassword', auth_plugin='mysql_native_password')
        cur = sql_connect.cursor()
        cur.execute('use game;')

        login = pickle.loads(request)
        print(login)
        if login["create"] == True:
            with open("logins.dat", "rb") as f:
                existing_logins = pickle.load(f)
                if login["username"] not in existing_logins:
                    existing_logins[login["username"]] = login["password"]
                    with open("logins.dat", "wb") as f:
                        pickle.dump(existing_logins, f)

                    cur.execute(f'insert into leaderboard values (0 , "{login["username"]}" , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0);')
                    sql_connect.commit()
                    cur.execute('select name from leaderboard order by total_trophies desc;')
                    count = 0
                    for i in list(cur):
                        count = count + 1
                        cur.execute(f"update leaderboard set _Rank_ = {count} where name = '{i[0]}';")
                        sql_connect.commit()
                    conn.send(pickle.dumps(True))
                else:
                    conn.send(pickle.dumps(False))
        else:
            with open("logins.dat", "rb") as f:
                existing_logins = pickle.load(f)  
                try:
                    if existing_logins[login["username"]] == login["password"]:
                        conn.send(pickle.dumps(True))
                    else:
                        conn.send(pickle.dumps("password is incorrect."))
                except KeyError:
                    conn.send(pickle.dumps("An account with that username does not exist")) 

        continue





    sql_connect = connector.connect(host = 'localhost' , user = 'root' , passwd = 'newpassword', auth_plugin='mysql_native_password')
    cur = sql_connect.cursor()
    cur.execute('use game;')
        
    if request == "ranks":# if string, get data
        a = []
        cur.execute('select _Rank_, Name, Total_Games_Played, Total_Wins, Total_Trophies from leaderboard order by _Rank_')
        for i in cur:
            a.append(list(i))
        conn.send(bytes(str(tabulate(a, headers=["Rank", "Player", "Total games played", "total wins","total trophies"])), "utf-8"))
    elif request == "ffa":
        a = []
        cur .execute('select Name, Number_of_FFA_games_played, Number_of_FFA_wins from leaderboard order by Number_of_FFA_wins desc')
        for i in cur:
            a.append(list(i))
        conn.send(bytes(str(tabulate(a, headers=["Player", "No. of games played", "wins", ])), "utf-8"))

    elif request == "heist":
        a = []
        cur .execute('select Name, Number_of_Heist_games_played, Number_of_Heist_wins from leaderboard order by Number_of_Heist_wins desc')
        for i in cur:
            a.append(list(i))
        conn.send(bytes(str(tabulate(a, headers=["Player", "No. of games played", "wins", ])), "utf-8"))
    
    elif request == "snd":
        a = []
        cur .execute('select Name, Number_of_Seek_and_Destroy_games_played, Number_of_Seek_and_Destroy_wins from leaderboard order by Number_of_Seek_and_Destroy_wins desc')
        for i in cur:
            a.append(list(i))
        conn.send(bytes(str(tabulate(a, headers=["Player", "No. of games played", "wins", ])), "utf-8"))
    
    conn.close()
    del conn
    sql_connect.close()
    del sql_connect, cur
