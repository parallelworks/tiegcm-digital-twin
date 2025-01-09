#!/bin/bash

# Function to display help
usage() {
  echo "Usage: $0 \
    --param_partition=value \
    --param_runid=value \
    --param_start_type=value \
    --param_ens_size=value \
    --param_simulation_hours=value \
    --param_range_limit=value \
    --param_datetime_str=value \
    --param_walltime_limit=value \
    --conda-path=value \
    --conda-name=value \
    <input_file> <output_file>"
  exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --param_partition=*)
      param_partition="${1#*=}"
      shift
      ;;
    --param_runid=*)
      param_runid="${1#*=}"
      shift
      ;;
    --param_start_type=*)
      param_start_type="${1#*=}"
      shift
      ;;
    --param_ens_size=*)
      param_ens_size="${1#*=}"
      shift
      ;;
    --param_simulation_hours=*)
      param_simulation_hours="${1#*=}"
      shift
      ;;
    --param_range_limit=*)
      param_range_limit="${1#*=}"
      shift
      ;;
    --param_datetime_str=*)
      param_datetime_str="${1#*=}"
      shift
      ;;
    --param_walltime_limit=*)
      param_walltime_limit="${1#*=}"
      shift
      ;;
    --conda-path=*)
      conda_path="${1#*=}"
      shift
      ;;
    --conda-name=*)
      conda_name="${1#*=}"
      shift
      ;;
    --*)
      echo "Unknown option $1"
      usage
      ;;
    *)
      if [[ -z "$input_file" ]]; then
        input_file="$1"
      elif [[ -z "$output_file" ]]; then
        output_file="$1"
      else
        echo "Unexpected argument $1"
        usage
      fi
      shift
      ;;
  esac
done

# Ensure all mandatory arguments are provided
if [[ -z "$param_partition" || -z "$param_runid" || -z "$param_start_type" || \
      -z "$param_ens_size" || -z "$param_simulation_hours" || -z "$param_range_limit" || \
      -z "$param_datetime_str" || -z "$param_walltime_limit" || -z "$conda_path" || \
      -z "$conda_name" || -z "$input_file" || -z "$output_file" ]]; then
  echo "Missing required arguments."
  usage
fi

# Activate the conda environment
source "$conda_path/bin/activate" "$conda_name"
if [[ $? -ne 0 ]]; then
  echo "Failed to activate conda environment: $conda_name"
  exit 1
fi

# Run the papermill command
papermill -k python3 \
  -p param_partition "$param_partition" \
  -p param_runid "$param_runid" \
  -p param_start_type "$param_start_type" \
  -p param_ens_size "$param_ens_size" \
  -p param_simulation_hours "$param_simulation_hours" \
  -p param_range_limit "$param_range_limit" \
  -p param_datetime_str "$param_datetime_str" \
  -p param_walltime_limit "$param_walltime_limit" \
  "$input_file" "$output_file" 2>&1 | tee _papermill.log

# Check the exit status of papermill
if [[ $? -ne 0 ]]; then
  echo "Papermill execution failed. Check _papermill.log for details."
  exit 1
fi

# Success
echo "Papermill execution completed successfully. Output saved to $output_file."

