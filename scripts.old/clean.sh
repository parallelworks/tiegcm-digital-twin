#!/bin/bash
#=====================================
# Clean up default outputs to bucket
#=====================================

source job_metadata.sh

# Remove data copied to bucket from
# the run specified in the job_metadata.
# In this case, remove only the two netcdf
# files (the bulk of the data) and leave the
# log files for diagnosis later.
rm -vrf ${ARCHIVE_DIR}/${PW_JOB_NUM}/mem*/*.nc

# Remove local working directories/container
cd $WORK_DIR
rm -rfv script/ run/ tiegcm2.0_res5.0_data.tar.gz tiegcm_res5.0_data/ TIEGCM.sif truncated_samples_F107.txt

