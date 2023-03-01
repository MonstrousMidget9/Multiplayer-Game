from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import tkinter.font as tkFont
from networking import server_ip
import pickle, socket
import os

wn = Tk()
wn.geometry("350x450")
wn.title('Launcher')

path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)
del path


login = False

# login 
try:
    login = pickle.load(open("user.bin", "rb"))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip , 6969))
    sock.sendall(pickle.dumps({'username':login['username'] , 'password':login['password'], "create":False}))
    data = pickle.loads(sock.recv(1024)) 
    if data == True:
        pass
    else:
        login = False
        messagebox.showerror('Login Error' , data)
except FileNotFoundError:
    login  = False



def signin():    
    login_wn = Tk()
    login_wn.geometry("200x300")
    login_wn.title('Sign in')
    tabControl = ttk.Notebook(login_wn)
    
    create_account_frame = ttk.Frame(tabControl)
    login_frame = ttk.Frame(tabControl)
    tabControl.add(login_frame, text="Sign in")
    tabControl.add(create_account_frame, text="Sign Up")
    tabControl.pack(expand=1, fill="both")
    
    username_label = ttk.Label(login_frame , text = 'Username')
    username_label.pack()
    username_entry = ttk.Entry(login_frame)
    username_entry.pack()
    password_label = ttk.Label(login_frame , text = 'Password')
    password_label.pack()
    password_entry = ttk.Entry(login_frame, show="*")
    password_entry.pack()
    def login_game():
        global login,player_label
        if username_entry.get() and password_entry.get():
            username = username_entry.get()
            password = password_entry.get()
            user_dictionary = {'username':username , 'password':password}
            try: 
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((server_ip , 6969))
                sock.sendall(pickle.dumps({'username':username , 'password':password, "create":False}))
                data = pickle.loads(sock.recv(1024)) 
                if data == True:
                    f = open('user.bin' , 'wb')
                    pickle.dump(user_dictionary , f)
                    f.close()
                    Login_Status.config(text = "Logged in ✅" , fg = 'green')
                    login_wn.destroy()
                    messagebox.showinfo('Login Successful' , 'You Have Logged in')
                    login = user_dictionary
                    player_label.config(text ='Logged in as: ' + login['username'])
                    return
                else:
                    login = False
                    messagebox.showerror('Login Error' , data)
            except PermissionError:
                messagebox.showerror('Error' , 'Permission Denied , Logged in but Unable To Store Login Data') 
        else:
            print(username_entry.get(), password_entry.get())
            messagebox.showerror('Create Account Error' , 'Username and Password Cannot Be Empty')

        
    submit_login_button = ttk.Button(login_frame , text = 'Login' , command=login_game)
    submit_login_button.pack()

    signup_username_label = ttk.Label(create_account_frame , text = 'Username')
    signup_username_label.pack()
    signup_username_entry = ttk.Entry(create_account_frame)
    signup_username_entry.pack()
    signup_password_label = ttk.Label(create_account_frame , text = 'Password')
    signup_password_label.pack()
    signup_password_entry = ttk.Entry(create_account_frame, show="*")
    signup_password_entry.pack()
    signup_confirm_password_label = ttk.Label(create_account_frame , text = 'Confirm Password')
    signup_confirm_password_label.pack()
    signup_confirm_password_entry = ttk.Entry(create_account_frame, show="*")
    signup_confirm_password_entry.pack()
    def createacc():
        global login,Login_Status,player_label
        if signup_username_entry.get() and signup_password_entry.get():
            if signup_confirm_password_entry.get() == signup_password_entry.get() :
                username = signup_username_entry.get()
                password = signup_password_entry.get()
                user_dictionary = {'username':username , 'password':password}
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((server_ip , 6969))
                sock.sendall(pickle.dumps({'username':username , 'password':password, "create":True}))
                #recv
                if pickle.loads(sock.recv(1024)) == True:
                    try:
                        f = open('user.bin' , 'wb')
                        pickle.dump(user_dictionary , f)
                        f.close()
                        messagebox.showinfo('Account Created' , 'Your Account has been created')
                        login_wn.destroy()
                        login = user_dictionary
                        Login_Status.config(text = "Logged in ✅" , fg = 'green')
                        player_label.config(text =  'Logged in as: ' + login['username'])
                        return
                    except:
                        messagebox.showerror('Error' , 'Permission Denied , Account Created but Unable To Store Login Data')
                else:
                    messagebox.showerror('Error' , 'That username has already been taken.')
            else:
               messagebox.showerror('Create Account Error' , 'Password and Confirm Password Do Not Match') 
        else:
            messagebox.showerror('Create Account Error' , 'Username and Password Cannot Be Empty')

    submit_signup_button = ttk.Button(create_account_frame, text='Sign Up', command = createacc)
    submit_signup_button.pack()
 
    login_wn.mainloop()

if login:
    Login_Status = Label(wn , text = "Logged in ✅" , fg = 'green')
    Login_Status.place(x = 140 , y = 100)
else:
    Login_Status = Label(wn , text = "Logged out ❌" , fg = 'red')
    Login_Status.place(x = 140 , y = 100)

login_button = Button(wn , text = 'Login', command=signin)
login_button.place(x = 155 , y = 120)

fontName = tkFont.Font(family="Times", size=30 ,weight = 'bold' , slant = 'italic')
name_Label = Label(wn , text = '2D ShooterZ' , font = fontName)
name_Label.place(x = 55 , y = 20)

def ffa():
    global login
    if login:
        wn.destroy()
        import ffa
        ffa.run(login["username"])
    else:
        messagebox.showerror("Not logged in", "Please login to play.")

def heist():
    global login
    if login:
        wn.destroy()
        import heist
        heist.run(login["username"])
    else:
        messagebox.showerror("Not logged in", "Please login to play.")

def sd():
    global login
    if login:
        wn.destroy()
        import seekanddestroy
        seekanddestroy.run(login["username"])
    else:
        messagebox.showerror("Not logged in", "Please login to play.")

def leaderboard():
    wn_leaderboard = Tk()
    wn_leaderboard.geometry("800x900")
    wn_leaderboard.title('Leaderboard')
    display_box = Text(wn_leaderboard,width = 80, height = 40 ,padx = 5,pady = 5)
    display_box.place(x = 50 , y = 200)
    def get(req):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip , 6969))
        sock.sendall(bytes(req, "utf-8"))
        sock.settimeout(1)
        try:
            data = sock.recv(4096).decode()
        except socket.timeout:
            display_box.configure(state = 'normal')
            display_box.insert(INSERT , "couldn't reach the server, please try again.")
            display_box.configure(state = 'disabled')
        else:
            display_box.configure(state = 'normal')
            display_box.delete('1.0', END)
            display_box.insert(INSERT , data)
            display_box.configure(state = 'disabled')
        finally:
            sock.close()
            del sock
    def get_total():
        get("ranks")
    def get_ffa():
        get("ffa")
    def get_heist():
        get("heist")
    def get_snd():
        get("snd")
    butt_get_total = Button(wn_leaderboard , text = 'Display total details' , command = get_total)
    butt_get_total.place(x = 60 , y = 30)
    butt_get_ffa = Button(wn_leaderboard , text = 'Display ffa details' , command = get_ffa)
    butt_get_ffa.place(x = 60 , y = 70)
    butt_get_heist = Button(wn_leaderboard , text = 'Display heist details' , command = get_heist)
    butt_get_heist.place(x = 60 , y = 110)
    butt_get_snd = Button(wn_leaderboard , text = 'Display Seek and Destroy details' , command = get_snd)
    butt_get_snd.place(x = 60 , y = 150)

    get_total()
    wn_leaderboard.mainloop()


butt_ffa = Button(wn , text = '      Free for all       ' , command = ffa)
butt_ffa.place(x = 120 , y = 180)

butt_heist = Button(wn , text = '           Heist            ' , command = heist)
butt_heist.place(x = 120 , y = 220)

butt_sd = Button(wn , text = ' Seek and Destroy ' , command = sd)
butt_sd.place(x = 120 , y = 260)

server_status = Label(wn, text="Server: pinging...")
server_status.place(x=130, y=320)

butt_leaderboard = Button(wn , text = ' LeaderBoard ' , command = leaderboard)
butt_leaderboard.place(x = 130 , y = 360)


if login:
    player_label = Label(wn , text = 'Logged in as: ' + login['username'])
    player_label.place(x = 10 , y = 400)
else:
    player_label = Label(wn , text = 'Signed Out')
    player_label.place(x = 10 , y = 400)
# connect to ping server
import socket, time
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def ping():
    try:
        sock.send(b"ping")
        sock.settimeout(1) # timeout after 1 seconds
        start = time.time_ns()
        x = sock.recv(16)
        server_status.config(text=f"Server: Online\nping: {round((time.time_ns() - start)/1000000)} ms")
    except socket.timeout:
        server_status.config(text="ping failed, retrying...")

    wn.after(2000, ping)

try:
    sock.connect((server_ip , 6998))
except ConnectionRefusedError:
    server_status.config(text="Server: Offline")
else:
    wn.after(2000, ping)

wn.mainloop()