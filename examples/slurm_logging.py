#!/root/.venv/codecarbon/bin/python3

import os

import logging
from codecarbon import OfflineEmissionsTracker

import time

import psutil
import sys
import traceback

import subprocess as sp

import argparse



def _print_process_tree(proc, indent=0):
    prefix = " " * indent
    try:
        name = proc.name()
        pid = proc.pid
    except psutil.NoSuchProcess:
        return

    log_message(f"{prefix}{name} (pid {pid})\n")

    # Children
    for child in proc.children(recursive=False):
        _print_process_tree(child, indent + 4)

def print_process_tree(pid=os.getpid()):
    logger = logging.getLogger()
    current = psutil.Process(pid)
    log_message("\n=== Parent Tree ===\n")
    p = current
    stack = []
    while p is not None:
        stack.append(p)
        p = p.parent()

    # Print ancestors from root → current
    for proc in reversed(stack):
        log_message(f"{proc.name()} (pid {proc.pid})\n")
    log_message("\n=== Children Tree ===\n")
    _print_process_tree(current)

    
def query_slurm_pids(jobid):
        
    try:
        sp_output = sp.check_output(["/usr/local/bin/scontrol", "listpids", str(jobid)],  stderr=sp.STDOUT)
        log_message(f"scontrol output:\n{sp_output.decode()}")
    except sp.CalledProcessError as e:
        log_message(f"scontrol failed for job {jobid}\n")
        log_message(f"Return code: {e.returncode}\n")
        log_message(f"Output:\n{e.output.decode(errors='replace')}\n")
        return []
    except Exception as e:
        # Catch-all for other failures
        log_message(f"Unexpected error calling scontrol: {e}\n")
        return []
        
    pids = []
    lines = sp_output.decode().strip().splitlines()
    for line in lines[1:]:  # Skip the first line
        parts = line.split()
        if not parts:
            continue
        
        pid = parts[0]
        # skip invalid PIDs
        if pid in ("-1", "-"):
            continue
        
        try:
            pids.append(int(pid))
        except ValueError:
            # In case pid is something unexpected
            continue
        
    return pids


def log_message(message):
    print(message)
    if logfile is not None:
        logfile.write(message + "\n")
        logfile.flush()
        
        
def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="CodeCarbon job wrapper"
    )
    group_ids = parser.add_mutually_exclusive_group(required=True)
    group_ids.add_argument(
        "--jobid",
        type=int,
        required=False,
        default=None,
        help="SLURM Job ID"
    )
    group_ids.add_argument(
        "--pids",
        type=int,
        nargs="+",
        required=False,
        default=[],
        help="Process ID"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="SLURM Job User"
    )
    parser.add_argument(
        "--gpuids",
        type=str,
        required=False,
        help="Comma-separated GPU IDs assigned to the job"
    )
    return parser

###################################################################

# Loglevel debug
logging.basicConfig(level=logging.DEBUG)

logfile = None
try:
    parser = build_argument_parser()
    args = parser.parse_args()
   
    jobid = args.jobid
    pids = args.pids
    
    user = args.user
    if args.gpuids:
        gpuids = args.gpuids.split(",")
    else:
        gpuids = []
        
    os.environ["SLURM_JOB_ID"] = str(jobid)
    os.environ["SLURM_JOB_USER"] = str(user)
    os.environ["SLURM_JOB_GPUS"] = ",".join(gpuids)
    
       
    logfile = open(f"/tmp/cc_{jobid}.log", "w", buffering=1)
    log_message("Python started")
    log_message(f"Interpreter: {sys.executable}")
   
    log_message("CodeCarbon SLURM Prolog Script Started")
    log_message(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    
    
    log_message("Available environment variables:")
    for key, value in os.environ.items():
        log_message(f"{key}: {value}")
             
    log_message("Wait 60 seconds to allow job processes to start")  
    for i in range(60):
        log_message(f"  Waiting... {1 * i} seconds elapsed")      
        time.sleep(1)  # Give some time for the job to start properly
        
    log_message("Wait completed at " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))  
    
    
    if jobid is None:
        log_message(f"Using provided PIDs: {pids}")
    else:
        log_message("Parse scontrol for process IDs with \"scontrol listpids\"")
        pids = query_slurm_pids(jobid)
        
    log_message(f"Found PIDs: {pids}")
    
    for pid in pids:
        log_message(f"Process tree for PID {pid}:")
        print_process_tree(pid)
    
    
    log_message(f"Job ID: {jobid}, User: {user}, GPU IDs: {gpuids}")
    
    tracker = OfflineEmissionsTracker(country_iso_code="DEU", region="DE-NW", measure_power_secs=10, api_call_interval=2, 
                                      gpu_ids=f"{gpuids}", tracking_mode="process", tracking_pids=args.jobid,
                                      save_to_prometheus=True, prometheus_url="129.217.31.239:9091",
                                      project_name=f"{user}", experiment_name=f"{jobid}",
                                      output_dir="/tmp/codecarbon_log/", output_file="/tmp/codecarbon_log/emission.csv")
    
    tracker.start()
    
    # Check for termination signal every second
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("Received termination signal. Stopping CodeCarbon tracker...")  
    except Exception as e:
        log_message(f"Exception in tracking loop: {e}")
        raise e     
    finally:
        tracker.stop()
        log_message("CodeCarbon tracker stopped.")

except Exception:
    log_message("Exception occurred:")
    log_message(traceback.format_exc())
    
finally:
    if logfile is not None:
        log_message("CodeCarbon SLURM Prolog Script Ended")
        logfile.close()
    
