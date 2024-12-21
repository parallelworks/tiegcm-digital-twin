#!/bin/bash
#===========================
# Download Miniconda, install,
# and create a new environment
#
# Specify the Conda install location
# and environment name, e.g.:
#
# ./create_conda_env.sh ${HOME}/.miniconda3 sl_onnx
#
# With a fast internet connection
# (i.e. download time minimal)
# this process takes < 5 min.
#
# For moving conda envs around,
# it is possible to put the
# miniconda directory in a tarball
# but the paths will need to be
# adjusted.  The download and
# decompression time can be long.
# As an alternative, consider:
# conda list -e > requirements.txt
# to export a list of the req's
# and then:
# conda create --name <env> --file requirements.txt
# to build another env elsewhere.
# This second step runs faster
# than this script because
# Conda does not stop to solve
# the environment.  Rather, it
# just pulls all the listed
# packages assuming everything
# is compatible.
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

# Python version
python_version="=3.9"

# Start conda
source ${miniconda_loc}/etc/profile.d/conda.sh
conda activate base

# Create new environment
# (if we are running Jupter notebooks, include ipython here)
conda create -y --name $my_env python${python_version}

# Jump into new environment
conda activate $my_env

# Install packages
conda install -y pandas matplotlib requests ipykernel psycopg2 numpy scipy --quiet
conda install -y -c anaconda jinja2 --quiet

echo Finished $0
