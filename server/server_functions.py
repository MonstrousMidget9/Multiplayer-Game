import socket, pickle

online = {} # every socket object connected to the server

def init(online_dict:dict): # initialise the module
    global online
    online = online_dict

def shuffled_enumerate(dic:dict):
    import random
    d = dic.copy()
    l = []
    for i in range(len(d)):
        k = random.choice(list(d.keys()))
        l.append([i, k])
        d.pop(k)
    return l

def send_to_all(x):# x --> object
    global online
    temp = None
    for i in online:
        try:
            i.send(pickle.dumps(x))
        except BrokenPipeError:
            temp = i
    if temp:
        u = online[temp]
        del online[temp]
        return u

def sendall_to_all(x):# x --> object
    global online
    temp = None
    for i in online:
        try:
            i.sendall(pickle.dumps(x))
        except BrokenPipeError:
            temp = i
    if temp:
        u = online[temp]
        del online[temp]
        return u

def send_to_all_except(_sock:socket.socket, x):# x -- > object, _sock -- > except whom
    global online
    temp = None
    for i in online:
        try:
            if _sock != i:
                i.send(pickle.dumps(x))
        except BrokenPipeError:
            temp = i
    if temp:
        u = online[temp]
        del online[temp]
        return u

def send_to(_sock:socket.socket, x):# x -- > object, _sock -- > to whom
    try:
        _sock.send(pickle.dumps(x))
    except BrokenPipeError:
        pass

def sendall_to(_sock:socket.socket, x):# x -- > object, _sock -- > to whom
    # socket.sendall() to ensure no packet loss
    try:
        _sock.sendall(pickle.dumps(x))
    except BrokenPipeError:
        pass