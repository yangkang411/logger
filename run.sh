#!/bin/bash

echo "run shell script: run.sh"
time=`date +"%Y%m%d_%H%M%S"`
echo ${time}

nohup python3 multi_logger.py >  log_${time}.txt  2>&1 &			
