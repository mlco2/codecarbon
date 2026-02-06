#!/bin/bash

JOBID=$SLURM_JOB_ID
LOGFILE="/tmp/prolog_${JOBID}.log"
PIDFILE="/tmp/prolog_${JOBID}.pid"

echo "Starting CodeCarbon for job $JOBID" >> "$LOGFILE"

mkdir -p /tmp/codecarbon_log/

# Check if GPU IDs are available
if [ -z "$SLURM_JOB_GPUS" ]; then    
    # We cannot inherit the cgroup because slum kills the entire cgroup on end of initialization
    systemd-run --unit codecarbon_$JOBID \
        /etc/slurm/pyscripts/_codecarbon.py \
        --jobid $JOBID \
        --user $SLURM_JOB_USER \
        &>> "$LOGFILE"
else
    systemd-run --unit codecarbon_$JOBID \
        /etc/slurm/pyscripts/_codecarbon.py \
        --jobid $JOBID \
        --user $SLURM_JOB_USER \
        --gpuids $SLURM_JOB_GPUS \
        &>> "$LOGFILE"
fi

# Save PID for epilog
sleep 1
exit 0


