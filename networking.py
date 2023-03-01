
server_ip = "20.204.24.120"

def packet_split(x:bytes):
    l = []
    for i in x.split(b".\x80"):
        if i:
            if not i.startswith(b"\x80"):
                i = b"\x80"+i
            if not i.endswith(b"."):
                i = i + b"."
            l.append(i)        
    return l

class network_packet():
    def __init__(self, heading:str, data):
        self.heading = heading
        self.data = data
