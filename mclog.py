import time
import os

#FILL IN WITH YOUR CLIENT'S LOG PATH
log_path = "C:/Users/boncz/AppData/Roaming/.minecraft/logs/latest.log"

#filter messages with these words in it
use_filter = False
filter_list = ["gold", "golden"]

#blacklist messages with these words in it
use_blacklist = True
blacklist = ["webshop"]

def process_chat_message(msg):
    msg_lower = msg.lower()

    if "[chat]" not in msg_lower:
        return
    
    if use_blacklist:
        if any(b.lower() in msg_lower for b in blacklist):
            return
    
    if use_filter:
        if not any(f.lower() in msg_lower for f in filter_list):
            return
    
    msg_split = msg.strip().split(" ")

    for x in range(4):
        msg_split.pop(1)

    if len(msg_split) > 1 and msg_split[1] and msg_split[1][0] == "\uf801":
        msg_split.pop(1)

    print(" ".join(msg_split), end='\n')

print("Program started\nUse Ctrl+C to exit!")

try:
    with open(log_path, 'r', encoding="utf-8", errors="replace") as file:
        file.seek(0, os.SEEK_END)
        
        while True:
            line = file.readline()
            
            if not line:
                time.sleep(0.1)
                continue

            process_chat_message(line)
            
except FileNotFoundError:
    print(f"Error! Could not open the log file on the followin path: {log_path}")
except KeyboardInterrupt:
    print("Program ended\n")
