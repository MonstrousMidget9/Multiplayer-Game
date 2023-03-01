from tkinter import *
import socket
from threading import Thread
import pickle

helps = {
    "Free For All":"There are no teams and the last one remaining in the game is the winner.",
    "Heist":"Two teams, each with their own safe, have to destroy their opponent's safe to win. First one to destroy wins.",
    "Seek And Destroy":"Two teams i.e. attackers and defenders, the attackers need to plant the bomb within 90 seconds and let it blast to win, \n whereas the defenders have to prevent the attackers from planting the bomb and diffuse it if planted to win.",
}

def main(sock:socket.socket, username, gamemode):
    launch_game = False

    def listen():
        while True:
            x = pickle.loads(sock.recv(1024))
            if type(x) == list:
                for i in x:
                    display_box.insert(END,i + "\n")
            elif x == "break":
                nonlocal launch_game
                launch_game = True
                wn.destroy()
                break
            else:
                display_box.configure(state = 'normal')
                display_box.insert(END,x + "\n")
                display_box.configure(state = 'disabled')
    Thread(target=listen, daemon=True).start()

    def ready_up():
        if username:
            sock.send(pickle.dumps(["ready", username]))
            # uname_entry["state"] = "disable"
            butt_start["state"] = "disable"


    wn = Tk()
    wn.geometry("900x500")
    wn.title(gamemode)
    
    display_help = Label(wn , text = helps[gamemode])
    display_help.place(x = 25 , y = 80)
    butt_start = Button(wn , text = 'Ready Up' , command = ready_up)
    butt_start.place(x = 400 , y = 440)
    display_box = Text(wn,width = 100, height = 15 ,padx = 5,pady = 5)
    display_box.place(x = 35 , y = 140)
    sock.send(pickle.dumps(["join", username]))
    wn.mainloop()
    if not launch_game:
        sock.send(pickle.dumps(["leave", username]))
        # sock.close()
    return launch_game