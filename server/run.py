import os, os.path
from subprocess import Popen
import time

# cd to current directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("starting server")

pingserver = Popen(["python3","ping_server.py"])
databaseserver = Popen(["python3","database_server.py"])
time.sleep(0.5)
ffaserver = Popen(["python3","ffa_server.py"])
heistserver = Popen(["python3","heist_server.py"])
sndserver = Popen(["python3","snd_server.py"])

while True:
    time.sleep(1)
    # check if any process has terminated
    if pingserver.poll() is not None or databaseserver.poll() is not None or ffaserver.poll() is not None or heistserver.poll() is not None or sndserver.poll() is not None:
        pingserver.terminate()
        databaseserver.terminate()
        ffaserver.terminate()
        heistserver.terminate()
        sndserver.terminate()
        exit(32)
