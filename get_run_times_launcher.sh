#!/bin/bash
#==============================
# Based on the most recent run
# information, grab the run times
# of the ensemble members and find
# the mean and standard deviation.
#
# Use GMT math for the mean and std,
# since we're already using TIEGCM
# in a container, it's not a big
# step to pull parallelworks/gmt.
#===============================

# Get basic information about where
# the data is
source job_metadata.sh

# Get the mean, std run times and 
# print number of NFS threads from log file
# (auto pulls the GMT container if first run)
singularity exec --bind ${ARCHIVE_DIR}/${PW_JOB_NUM} docker://parallelworks/gmt ./get_run_times.sh

# Number of NFS threads
grep NFS.COUNT ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/slurm-*.out | head -1

