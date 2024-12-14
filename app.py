import os
import time
from networktables import NetworkTables
import subprocess
from pathlib import Path

import traceback

# Configuration
RIO_IP = "localhost"
RIO_USER = "lvuser"
LOG_PATH = Path("/media/sda1/logs/")
LOCAL_LOG_DIR = Path("C:/robot_logs")
SYNC_INTERVAL = 60

LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)

NetworkTables.initialize(server=RIO_IP)

def sync_logs():
    print("starting sync")
    try:
        if RIO_IP!="localhost":
            subprocess.run(
                [
                    "robocopy",
                    str(LOG_PATH),  
                    str(LOCAL_LOG_DIR),
                    "/MIR",  
                    "/Z",    
                    "/R:3",  
                    "/W:5"    
                ],
                check=True
            )
        else:
            print("running in sim, not sshing into rio")
    except Exception as e:
         print(traceback.format_exc())

def value_changed(source, key, value, is_new, state):
    try:
        
        fms_control_data = bin(int(value))[2:]
        
        is_enabled = fms_control_data[-1] == "1" if fms_control_data!='0' else False
        is_connected_to_fms = fms_control_data[1] == "1" if fms_control_data!='0' else False

        if state["is_robot_enabled"] is None:
            state["is_robot_enabled"] = is_enabled

        if is_connected_to_fms and state["is_robot_enabled"] and not is_enabled:
            print("went from enable to disabled while connected to fms, syncing now")
            sync_logs()

        state["is_robot_enabled"] = is_enabled
    except Exception as e:
         print(traceback.format_exc())

def main():
    state = {"is_robot_enabled": None}

    fmsinfo = NetworkTables.getTable("FMSInfo")
    fmsinfo.addEntryListener(lambda source, key, value, is_new: value_changed(source, key, value, is_new, state), key="FMSControlData")

    last_sync_time = time.time() 
    while True:
        try:
            time.sleep(1) #change to larger delay when not testing
            if not state["is_robot_enabled"]:  
                if time.time() - last_sync_time > SYNC_INTERVAL:
                    print("regular sync")
                    sync_logs()
                    last_sync_time = time.time()
        except Exception as e:
            print(traceback.format_exc())
            break

if __name__ == "__main__":
    main()
