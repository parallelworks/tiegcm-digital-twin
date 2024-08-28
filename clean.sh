#!/bin/bash
#=====================================
# Clean up default outputs to bucket
#=====================================

source job_metadata.sh

# Remove data copied to bucket from
# the run specified in the job_metadata.
rm -vrf /tiegcm/model-outputs/tiegcm/tiegcm2.0/ens/${PW_JOB_NUM}

# Remove local working directories/container
cd $WORK_DIR
rm -rfv script/ run/ tiegcm2.0_res5.0_data.tar.gz tiegcm_res5.0_data/ TIEGCM.sif truncated_samples_F107.txt

