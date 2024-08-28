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

# Pull the GMT container
singularity exec docker://parallelworks/gmt /bin/bash

# Grab results from the slurm-<jobid>.out files
# cat mem*/slurm-*.out | grep real | awk {convert columns to seconds} | gmt gmtmath mean ...
