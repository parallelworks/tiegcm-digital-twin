#!/bin/bash

# Function to extract number of cores from the partition name
extract_cores() {
  local partition=$1
  local value=$(echo "$partition" | grep -oE '[0-9]+xlarge' | grep -oE '[0-9]+')
  echo $((value * 2 * $NODE_COUNT))
}

# Gather the list of partitions
partitions=$(sinfo | awk '{print $1}' | egrep -v PARTITION | sed 's/*//' | sort)

# Mandatory notebook parameters
PARAM_RUNID="test001"
PARAM_START_TYPE="cold"
PARAM_SIMULATION_HOURS="24"
PARAM_RANGE_LIMIT="5"
PARAM_DATETIME_STR="2023/09/21/00:00:00"
PARAM_WALLTIME_LIMIT="01:00:00"
CONDA_PATH="$HOME/pw/software/.miniconda3c"
CONDA_NAME="parsl"
NODE_COUNT="2"

# Loop through each partition
for partition in $partitions; do
  # Calculate total cores and ensemble size
  total_cores=$(extract_cores "$partition")
  ensembles=$((total_cores / 4))

  # Run the notebook script
  ./notebook-execute.sh \
    --param_partition="$partition" \
    --param_runid="$PARAM_RUNID" \
    --param_start_type="$PARAM_START_TYPE" \
    --param_ens_size="$ensembles" \
    --param_simulation_hours="$PARAM_SIMULATION_HOURS" \
    --param_range_limit="$PARAM_RANGE_LIMIT" \
    --param_datetime_str="$PARAM_DATETIME_STR" \
    --param_walltime_limit="$PARAM_WALLTIME_LIMIT" \
    --conda-path="$CONDA_PATH" \
    --conda-name="$CONDA_NAME" \
    TIEGCM_davei_workflow.ipynb OUTPUT.ipynb

  # Check for success of notebook execution
  if [[ $? -ne 0 ]]; then
    echo "Notebook execution failed for partition $partition"
    exit 1
  fi

  # Copy the monitoring database
  monitoring_copy="monitoring.${partition}.${total_cores}_cores.${ensembles}_ensembles.${PARAM_SIMULATION_HOURS}_hours.db"
  cp runinfo/monitoring.db "$monitoring_copy"

  # Execute the clean script
  if [[ -f ./clean ]]; then
    ./clean
  else
    echo "Clean script not found! Skipping clean step."
  fi

done

echo "All partitions processed successfully."

