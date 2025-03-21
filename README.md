# tiegcm-digital-twin
Using TIEGCM as a digital twin

## Goals

This workflow is meant to be run three different ways:
1. interactively by executing the cells of the notebook `TIEGCM_workflow.ipynb` (user is responsible for installing OpenMPI);
2. via the Parallel Works ACTIVATE graphical user interface (i.e. a remote workflow that uses `papermill` to invoke the notebook in \#1 and automated installation of OpenMPI); and
3. via an API call to activate.parallel.works that starts the workflow (\#2).

This hierarchy of workflow execution types allows for the integration of workflow development (i.e. interactive testing of new features in the notebook) with automated/programmatic launching of the workflow.

## Dependencies

The 3 different workflow launch mechanisms depend on the following heirarchy of files:
1. Jupyter notebook `TIEGCM_workflow.ipynb`;
2. workflow definition file `./workflow/workflow.yaml` in this repo; and
3. API client in `API_launch`.

In all cases, the workflow also depends on the following artifacts:
4. a Conda env with Parsl (often bootstrapped by the notebook);
6. TIEGCM Docker container converted to Singularity on-the-fly;
7. publicly available TIEGCM initialization and configuration files downloaded on-the-fly; and
8. TIEGCM is launched by `mpiexec`, so you'll also need OpenMPI or Intel MPI. Please see `install_openmpi.sh` distributed with this repository (and executed automatically as part of workflow levels \#2 and \#3) for an example of OpenMPI installation.

The original TIEGCM model is available from http://www.hao.ucar.edu/modeling/tgcm/download.php and is distributed under an academic, non-commercial [license](https://www.hao.ucar.edu/modeling/tgcm/download/files/tiegcmlicense.txt).

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
+ `API_launch` contains scripts and example input data for launching the workflow from an API call to the the PW platform.

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

