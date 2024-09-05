#!/bin/bash

# Currently unused. Keep as is for merging later.
export PW_JOB_ID=42

# This setting can be a number or a string
# This is the main job identifier.
export PW_JOB_NUM=hpc6a_hpc6a_w_lustre

# Currently unused. Keep as is for merging later.

# This setting is not used.
export N_NODES=1

# This setting controls the number of
# ensemble members. run.sh is hardcoded
# to request 4 tasks per ensemble member.
export N_ENS=120

# This setting is not used.
export TILE_OUTPUTS=False

# This setting controls which partition of
# the cluster to use. The partition name is
# specific to each cluster; in this case
# I use it as a way to switch between
# instance types since I've configured
# my cluster to have a different instance
# type on each partition.
export PARTITION=biggest

# Where do we want the model to run?
# This value can be set to ${PWD} if
# you just want to run whereever
# the github repo is cloned.
# Other paths are possible.
export WORK_DIR=/lustre/work/
