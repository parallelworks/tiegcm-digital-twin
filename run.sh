#!/bin/bash

# Load metadata vars
source job_metadata.sh

echo "PWD: $PWD"
echo "N_NODES: $N_NODES"
echo "N_ENS: $N_ENS"
echo "PW_JOB_ID: $PW_JOB_ID"
echo "PW_JOB_NUM: $PW_JOB_NUM"
echo "TILE_OUTPUTS: $TILE_OUTPUTS" 
echo "PARTITION: $PARTITION"
echo "WORK_DIR: $WORK_DIR"

echo "sbatch script is starting here:"
echo;pwd;echo;hostname;echo;ls;echo;

echo "Change to WORK_DIR and check again:"
# Create WORK_DIR if not already present.
# Command is silent if WORK_DIR exists.
mkdir -pv $WORK_DIR
cd $WORK_DIR
echo;pwd;echo;hostname;echo;ls;echo;

image_sif="TIEGCM.sif"

# I don't think this is being used and it confuses me.
#HOME=$PWD

job_pids=() # Array to store PIDs of local background jobs
sbatch_job_ids=() # Array to store SLURM job IDs

echo;echo Copying dependencies from s3 bucket...
# Import singularity .sif from mounted s3 bucket
if [ -f "$image_sif" ]; then
    echo "Using cached image.sif..."
else
    echo "Downloading image.sif from S3..."
    #cp /storage/model-images/tiegcm/TIEGCM.sif .
    cp /tiegcm/model-images-tiegcm/TIEGCM.sif .

    # Check if the download was successful
    if [ $? -eq 0 ]; then
        echo "Downloaded image.sif successfully."
    else
        echo "Failed to download image.sif!"
        exit 1
    fi
fi


# Import tar and uncompress
data_dir="tiegcm_res5.0_data"
if [ -d "$data_dir" ]; then
  echo "$data_dir exists."
else
    echo  Copying tar and uncompressing...
    #cp /storage/model-workflows/tiegcm/tiegcm2.0/data/tiegcm2.0_res5.0_data.tar.gz .
    cp /tiegcm/model-workflows-tiegcm2.0/data/tiegcm2.0_res5.0_data.tar.gz .

    tar -zxf tiegcm2.0_res5.0_data.tar.gz
    
    # Check if the uncompression was successful
    if [ $? -eq 0 ]; then
        echo "Uncompressed $data_dir successfully."
    else
        echo "Failed to untar $data_dir!"
        exit 1
    fi
fi

# Import script/ from mounted s3 bucket
script_dir="script"
if [ -d "$script_dir" ]; then
  echo "$script_dir exists."
else
    echo  Copying tar and uncompressing...
    #cp -r /storage/model-workflows/tiegcm/tiegcm2.0/script .
    cp -r /tiegcm/model-workflows-tiegcm2.0/script .

    # TODO: Fix this workaround
    touch script/truncated_samples_F107.txt

    # Check if the uncompression was successful
    if [ $? -eq 0 ]; then
        echo "Downloaded $script_dir successfully."
    else
        echo "Failed to download $script_dir!"
        exit 1
    fi
fi

export TGCMMODEL=${PWD}
export TGCMDATA=${TGCMMODEL}/tiegcm_res5.0_data

# Load shared libraries installed using miniconda
export SINGULARITYENV_LD_LIBRARY_PATH=/opt/miniconda3/lib

# Choose ensemble size and other parameters for F10.7 samples
ens_size=$N_ENS
mean=75
std_dev=1
range_limit=5

echo "Generate a truncated normal samples for F10.7"
singularity exec TIEGCM.sif /opt/miniconda3/bin/python script/generate_F107_samples.py $ens_size $mean $std_dev $range_limit

export RUNDIR=${TGCMMODEL}/run

# Create directory (job-id) in the s3 bucket for outputs
cd /tiegcm/model-outputs/tiegcm/tiegcm2.0/ens
mkdir -pv ${PW_JOB_NUM}

# I don't think this is being used
# (loop below uses cd to change dirs
# very quickly).
#cd $HOME

echo "Set up tigecm ensemble runs..."
for (( i=1; i<=$ens_size; i++))
do
  mem="mem"$(printf "%03d" $i)

  mkdir -p ${RUNDIR}/${PW_JOB_NUM}/${mem}
  cd ${RUNDIR}/${PW_JOB_NUM}/${mem}

  /bin/cp -f ${TGCMMODEL}/script/tiegcm_res5.0.inp .
  /bin/cp -f ${TGCMMODEL}/script/truncated_samples_F107.txt .
  /bin/cp -f ${TGCMMODEL}/script/modify_tgcm_input.py .

  singularity exec ${TGCMMODEL}/TIEGCM.sif /opt/miniconda3/bin/python modify_tgcm_input.py $i
  
if command -v sbatch &> /dev/null ; then
    echo "sbatch command found, submit batch job" 

# Key changes here:
# Removed --exclusive to allow for testing packing multiple runs on the same node
# Added --cpus-per-task=1 to explicitly tell the scheduler how many CPUs it needs
#    (this is the default anyway, but useful here in case we test other configs)
# Added --partition to allow pushing runs to different partitions.
# Insert time command before mpirun to get run time specifically for the compute,
# independent of the data staging in, node spin up, and data staging out. This
# time command output will end up in default slurm output log - if this is not
# configured in #SBATCH, then it will be in the run directory under slurm-<jobid>.out.
cat <<EOF >run.sh
#!/bin/bash
#SBATCH --job-name ${mem}
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00 # Max execution time
#SBATCH --partition=$PARTITION

echo "Hostname:"
hostname

export SINGULARITYENV_LD_LIBRARY_PATH=/opt/miniconda3/lib

echo "Run ensemble member..."
# Originally, it was assumed that this container
# ran somewhere under $HOME whose absolute path 
# is the same in the container and out of the 
# container and Singularity autobinds $HOME on
# startup of the container. When choosing other
# directories not under $HOME (or the limited
# subset of autobound dirs), however, we need to 
# explicitly include the --bind directive.
time mpirun -n 4 singularity exec --bind ${TGCMMODEL} ${TGCMMODEL}/TIEGCM.sif /opt/model/tiegcm.exec/tiegcm2.0 tiegcm_res5.0.inp &> tiegcm_res5.0_${mem}.out

echo "Export outputs to s3 bucket..."

cd /tiegcm/model-outputs/tiegcm/tiegcm2.0/ens/${PW_JOB_NUM}
mkdir -p ${mem}
cd ${RUNDIR}/${PW_JOB_NUM}/${mem}

rsync -r ${RUNDIR}/${PW_JOB_NUM}/${mem}/. /tiegcm/model-outputs/tiegcm/tiegcm2.0/ens/${PW_JOB_NUM}/${mem}

# Check if the export succeeded
if [ $? -eq 0 ]; then
    echo "Results exported to S3 Bucket successfully."
else
    echo "Failed to export results to the S3 Bucket."
fi

echo "Writing number of NFS threads to log:"
cat /etc/sysconfig/nfs | grep NFS.COUNT

now=$(date)

echo "$now"
echo "TIE-GCM Workflow Ran Successfully"

EOF

    # Submit job and capture job ID
    job_id=$(sbatch run.sh | awk '{print $4}')
    sbatch_job_ids+=($job_id)

else
    echo "sbatch command not found, run it locally."
    time mpirun -n 4 singularity exec --bind ${TGCMMODEL} ${TGCMMODEL}/TIEGCM.sif /opt/model/tiegcm.exec/tiegcm2.0 tiegcm_res5.0.inp &> tiegcm_res5.0_${mem}.out &
    job_pids+=($!) # Capture PID of the background job
fi

done # End of ensemble member launch loop

# Wait for SLURM jobs to finish
for job_id in "${sbatch_job_ids[@]}"; do
    while squeue -j $job_id | grep -q $job_id; do
        sleep 10 # Wait for 10 seconds before checking again
    done
done

# Wait for all local background jobs to finish
for pid in "${job_pids[@]}"; do
    wait $pid
done

echo "Do not remove job_metadata.sh yet!"
#rm job_metadata.sh

echo "All child processes have completed."

# If $TILE_OUTPUTS is true, make a POST request to the tiling service API
#if $TILE_OUTPUTS; then
#    echo "TILE_OUTPUTS set to true. Sending API request to tile outputs..."

#    curl http://terry13.idm.orionspace.com:4100/ping -H "Accept: application/json"

    # curl -X POST -H "Content-Type: application/json" -d \
    # '{ 
    #     "host": "aws",
    #     "input_path" : "model-outputs/tiegcm/tiegcm2.0/ens",
    #     "output_path" : "/output/models", 
    #     "iso_start_time" : "T06.00.00",
    #     "iso_start_date": "2024-02-06",
    #     "input_file_type" : "nc",
    #     "is_time_series" : true,
    #     "data_source_name": "tiegcm2.0",
    #     "product_id" : "TEC",
    #     "job_id": $PW_JOB_ID
    # }' \
    # http://terry13.idm.orionspace.com:4300/tiler/3dtiles/1

#fi


# Test - Set up certs for gitserver (pulling tiler image)
#sudo mkdir -p /etc/docker/certs.d/gitserver.idm.orionspace.com:5050
#openssl s_client -showcerts -connect gitserver.idm.orionspace.com:5050 \
#</dev/null 2>/dev/null|openssl x509 -outform PEM > /etc/docker/certs.d/gitserver.idm.orionspace.com:5050/ca.crt

# echo "$MY_PASSWORD" | docker login --username foo --password-stdin

#sudo docker login gitserver.idm.orionspace.com:5050

echo "Done!"
