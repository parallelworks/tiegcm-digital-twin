#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 <input_notebook> [--output-notebook <output_notebook>] [--iterations <#>] [--all-partitions | --partitions \"<partition1> <partition2> ...\"] [--help]"
  echo "  <input_notebook>: The Jupyter notebook file to execute."
  echo "  --output-notebook: Specify a custom output notebook name."
  echo "  --iterations: Number of iterations to execute the workflow (default: 1)."
  echo "  --all-partitions: Run across all partitions found in 'sinfo'."
  echo "  --partitions: Specify a space-delimited list of partition names to process."
  echo "  --help:       Display this help message."
  exit 0
}

# Function to extract number of cores from the partition name
extract_cores() {
  local partition=$1
  local value=$(echo "$partition" | grep -oE '[0-9]+xlarge' | grep -oE '[0-9]+')
  echo $((value * 2))
}

# Function to ensure unique filenames with RUN# suffix
ensure_unique_filename() {
  local base_name=$1
  local extension=$2
  local counter=1

  while [[ -e "${base_name}.RUN${counter}.${extension}" ]]; do
    ((counter++))
  done

  echo "${base_name}.RUN${counter}.${extension}"
}

# Parse command-line arguments
input_notebook=""
output_notebook=""
user_partitions=""
all_partitions=false
iterations=1

while [[ $# -gt 0 ]]; do
  case $1 in
    --all-partitions)
      all_partitions=true
      shift
      ;;
    --partitions)
      shift
      user_partitions=$1
      shift
      ;;
    --output-notebook)
      shift
      output_notebook=$1
      shift
      ;;
    --iterations)
      shift
      iterations=$1
      shift
      ;;
    --help)
      usage
      ;;
    *)
      if [[ -z "$input_notebook" ]]; then
        input_notebook=$1
      else
        echo "Unknown argument: $1"
        usage
      fi
      shift
      ;;
  esac
done

# Ensure input_notebook is provided
if [[ -z "$input_notebook" ]]; then
  echo "Error: Input notebook is required."
  usage
fi

# Gather the list of partitions
if $all_partitions; then
  partitions=$(sinfo | awk '{print $1}' | egrep -v PARTITION | sed 's/*//' | sort)
elif [[ -n "$user_partitions" ]]; then
  partitions="$user_partitions"
else
  echo "Error: You must specify either --all-partitions or --partitions."
  usage
fi

# Mandatory notebook parameters
PARAM_RUNID="test001"
PARAM_START_TYPE="cold"
PARAM_SIMULATION_HOURS="24"
PARAM_RANGE_LIMIT="5"
PARAM_DATETIME_STR="2023/09/21/00:00:00"
PARAM_WALLTIME_LIMIT="01:00:00"
CONDA_PATH="$HOME/pw/software/.miniconda3c"
CONDA_NAME="parsl"

# Loop through each partition
for partition in $partitions; do
  # Calculate total cores and ensemble size
  total_cores=$(extract_cores "$partition")
  ensembles=$((total_cores / 4))

  # Display informational line about the benchmark
  echo "========================================"
  echo "Starting benchmark for partition: $partition"
  echo "Total cores: $total_cores"
  echo "Number of ensembles: $ensembles"
  echo "Simulation hours: $PARAM_SIMULATION_HOURS"
  echo "Walltime limit: $PARAM_WALLTIME_LIMIT"
  echo "Iterations: $iterations"
  echo "========================================"

  # Perform the specified number of iterations for the current partition
  for ((i = 1; i <= iterations; i++)); do
    echo "--- Iteration $i/$iterations for partition $partition ---"

    # Determine the output notebook filename
    if [[ -z "$output_notebook" ]]; then
      base_name="monitoring.${partition}.${total_cores}_cores.${ensembles}_ensembles.${PARAM_SIMULATION_HOURS}_hours"
      output_notebook="${base_name}.OUTPUT.ipynb"
      if [[ -e "$output_notebook" ]]; then
        output_notebook=$(ensure_unique_filename "${base_name}.OUTPUT" "ipynb")
      fi
    fi

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
      "$input_notebook" "$output_notebook"

    # Check for success of notebook execution
    if [[ $? -ne 0 ]]; then
      echo "Notebook execution failed for partition $partition, iteration $i"
      exit 1
    fi

    # Create the monitoring database filename
    base_name="monitoring.${partition}.${total_cores}_cores.${ensembles}_ensembles.${PARAM_SIMULATION_HOURS}_hours"
    monitoring_copy="${base_name}.db"

    if [[ -e "$monitoring_copy" ]]; then
      monitoring_copy=$(ensure_unique_filename "$base_name" "db")
    fi

    cp runinfo/monitoring.db "$monitoring_copy"

    # Run dump-timings10.py for text output
    text_output="${monitoring_copy%.db}.txt"
    ./dump-timings10.py "$monitoring_copy" > "$text_output"

    # Run dump-timings10.py for CSV output
    csv_output="${monitoring_copy%.db}.csv"
    ./dump-timings10.py "$monitoring_copy" --csv > "$csv_output"

    # Execute the clean script
    if [[ -f ./clean ]]; then
      ./clean
    else
      echo "Clean script not found! Skipping clean step."
    fi
  done

done

echo "All partitions processed successfully."
