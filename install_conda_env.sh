#!/bin/bash
#===========================
# Download Miniconda, install,
# and create a new environment
#
# Specify the Conda install location
# and environment name, e.g.:
#
# ./create_conda_env.sh ${HOME}/.miniconda3 parsl
#
# With a fast internet connection
# (i.e. download time minimal)
# this process takes < 5 min.
#
#===========================

echo Starting $0

# Miniconda install location
# The `source` command somehow
# doesn't work with "~", so best
# to put an absolute path here
# if putting Miniconda in $HOME.
#
# Assuming HOME is a universally
# accessible location on the cluster.
miniconda_loc=$1

# Check if OpenMPI is already installed
if [ -d $miniconda_loc ]; then
	echo It appears that Miniconda is already installed at $miniconda_loc
	echo Exiting the installer.
        exit 0
fi

# Download current version of
# Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run Miniconda installer
chmod u+x ./Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p $miniconda_loc

# Clean up
rm ./Miniconda3-latest-Linux-x86_64.sh

# Define environment name
my_env=$2


# Start conda
source ${miniconda_loc}/etc/profile.d/conda.sh
conda activate base

# Build environment from cached .yaml
# (see .ipynb for how to create this file):
conda env update -f ./requirements/${my_env}.yaml --name ${my_env}

echo Finished $0

