#!/bin/bash
#=======================

source job_metadata.sh

# MEAN
#echo "AVG run time (s): " `cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | awk '{print $2}' | awk -Fm '{print $1*60 + $2}' | gmt gmtmath -Ca STDIN MEAN -Sl =`
avg_time=`cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | awk '{print $2}' | awk -Fm '{print $1*60 + $2}' | gmt gmtmath -Ca STDIN MEAN -Sl =`

# STD
#echo "STD run time (s): " `cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | awk '{print $2}' | awk -Fm '{print $1*60 + $2}' | gmt gmtmath -Ca STDIN STD -Sl =`
std_time=`cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | awk '{print $2}' | awk -Fm '{print $1*60 + $2}' | gmt gmtmath -Ca STDIN STD -Sl =`

# NUM
#echo "Number of runs: " `cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | wc -l`
num_time=`cat ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | grep real | wc -l`

# Print results on one line:
echo "AVG STD NUM"
echo "(s) (s) (no unit)"
echo ${avg_time} ${std_time} ${num_time}

