#!/bin/bash
export PW_JOB_ID=42
export PW_JOB_NUM=01
export N_NODES=1
export N_ENS=1
export TILE_OUTPUTS=False
export PARTITION=compute

# Where do we want the model to run?
# This value can be set to ${PWD} if
# you just want to run whereever
# the github repo is cloned.
# Other paths are possible.
export WORK_DIR=${PWD}
