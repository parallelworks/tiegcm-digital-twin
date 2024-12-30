# tiegcm-digital-twin
Using TIEGCM as a digital twin

## Dependencies

This workflow depends on the following:
1. the Jupyter notebook or `main.py` workflow in this repo;
2. the Conda env with Parsl bootstrapped by the notebook/workflow;
3. TIEGCM Docker container converted to Singularity on-the-fly; and
4. some initialization and configuration tarballs in a cloud bucket.

The original TIEGCM model is available from http://www.hao.ucar.edu/modeling/tgcm/download.php and is distributed under an academic, non-commercial [license](https://www.hao.ucar.edu/modeling/tgcm/download/files/tiegcmlicense.txt).

5. TIEGCM is launched by mpiexec, so you'll also need OpenMPI or Intel MPI. Please see `install_openmpi.sh` distributed with this repository for an example of OpenMPI installation.

## Container conversion

The TIEGCM container was provided as a Singularity `.sif`. To convert 
it to a Docker container to host it on DockerHub,
```
git clone https://github.com/singularityhub/singularity2docker.git
sudo ./singularity2docker/singularity2docker.sh -n parallelworks/tiegcm:latest ./TIEGCM.sif
docker login
...
docker push parallelworks/tiegcm
docker logout
```

Now, a single singularity command can pull this container, e.g.
```
singularity pull tiegcm.sif docker://parallelworks/tiegcm.sif
```
This command is integrated into the workflow.

## Organization

+ `requirements` specifies the Conda environments used in this project.
+ `scripts.manual` contains scripts used during the initial manual tests of TIEGCM.
+ `tiegcm_utils` contains supporting scripts for gathering solar forcing and building TIEGCM namelists (`.inp` files)
+ `workflow` contains a Parallel Works workflow specification `.yaml`

Other files in the top level of this repository are core files used by the workflow.

## Compute resource usage
```
time run.sh

real    3m3.184s
user    0m1.073s
sys     0m1.335s
```

### Default configuration (tiegcm_res5.0_data)

4 CPUs - full utilization
~1.5GB RAM

