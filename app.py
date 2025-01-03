import os
import time
from networktables import NetworkTables
import subprocess
from pathlib import Path
import logging
import datetime
import traceback
from datetime import datetime, timedelta

RIO_IP = "10.94.8.2"
RIO_USER = "lvuser"
REMOTE_LOG_DIR = "/media/sda1/logs"
LOCAL_LOG_DIR = Path("C:/Users/Admin/Documents/sync_logs")
SYNC_INTERVAL = 300



LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler( Path("./logs.txt")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def sync_logs():
    logger.info("Starting sync")
    try:
        if RIO_IP != "localhost":
            scp_command = [
                "scp",
                "-r", 
                f"{RIO_USER}@{RIO_IP}:{REMOTE_LOG_DIR}",
                str(LOCAL_LOG_DIR)  
            ]

            subprocess.run(scp_command, check=True)
            file_info,time_synced = fetch_remote_file_info()
            if time_synced:
                files_to_delete = [ fi[1] for fi in file_info if fi[0]>60]

                delete_remote_files(files_to_delete)
        else:
            logger.info("Running in simulation mode, not transferring logs from Rio.")
    except Exception as e:
        logger.error("Error during log synchronization:")
        logger.error(traceback.format_exc())

def fetch_remote_file_info():
    
    stat_command = [
        "ssh",
        f"{RIO_USER}@{RIO_IP}",
        "date +%s",
        ";"
        'stat',
        '-c',
        '%Y^%n',
        f"{REMOTE_LOG_DIR}/*"
    ]

    result = subprocess.check_output(stat_command, text=True).strip()
    result = list(result.splitlines())
    remote_time = int(result.pop(0))
    local_epoch_time  = int(time.time())
    time_synced = abs(local_epoch_time-remote_time)<20
    file_info = []
    for t in result:
        file_time,file_name = t.split("^")
        file_age_seconds =   remote_time-int(file_time)
        file_info.append((file_age_seconds,file_name))
    return file_info,time_synced

def delete_remote_files(files_to_delete):
    try:
        if files_to_delete:
            file_list = " ".join(files_to_delete)
            command = ["ssh",
             f"{RIO_USER}@{RIO_IP}",
            'rm'
            ] + files_to_delete
            subprocess.run(command, shell=True, check=True)
            logger.info(f"Deleted remote files: {', '.join(files_to_delete)}")
    except Exception as e:
        logger.error("Error deleting remote files:")
        logger.error(traceback.format_exc())

def value_changed(source, key, value, is_new, state):
    try:
        fms_control_data = bin(int(value))[2:]
        
        is_enabled = fms_control_data[-1] == "1" if fms_control_data != '0' else False
        is_connected_to_fms = fms_control_data[1] == "1" if fms_control_data != '0' else False

        if state["is_robot_enabled"] is None:
            state["is_robot_enabled"] = is_enabled

        if is_connected_to_fms and state["is_robot_enabled"] and not is_enabled:
            logger.info("went from enable to disabled while connected to fms, syncing now")
            sync_logs()

        state["is_robot_enabled"] = is_enabled
    except Exception as e:
         logger.error(traceback.format_exc())

def main_perpetual():
    NetworkTables.initialize(server=RIO_IP)
    state = {"is_robot_enabled": None}

    fmsinfo = NetworkTables.getTable("FMSInfo")
    fmsinfo.addEntryListener(lambda source, key, value, is_new: value_changed(source, key, value, is_new, state), key="FMSControlData")

    last_sync_time = time.time() 
    
    while True:
        try:
            time.sleep(1)
            if not state["is_robot_enabled"]:  
                if time.time() - last_sync_time > SYNC_INTERVAL:
                    logger.info("regular sync")
                    sync_logs()
                    last_sync_time = time.time()
        except Exception as e:
            logger.error(traceback.format_exc())
           
def main():
    NetworkTables.initialize(server=RIO_IP)
    state = {"is_robot_enabled": None}

    fmsinfo = NetworkTables.getTable("FMSInfo")
    fmsinfo.addEntryListener(lambda source, key, value, is_new: value_changed(source, key, value, is_new, state), key="FMSControlData")

    try:
        if not state["is_robot_enabled"]:  
            sync_logs()      
    except Exception as e:
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main_perpetual()
