# tiegcm-digital-twin
Using TIEGCM as a digital twin

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

