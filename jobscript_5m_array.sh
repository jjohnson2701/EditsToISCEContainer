#!/bin/bash

# Written by: jojo8550@colorado.edu
# Date: 20200709
# Purpose: This script submits a job on Summit. Has been edited to accept a 5m local DEM instead of downloading one. 
# It is possible that the python script still downloads one, but doesn't use it.  


#SBATCH --partition=shas     # Summit partition
#SBATCH --qos=normal                 # Summit qos
#SBATCH --time=024:00:00           # Max wall time
#SBATCH --nodes=1            # Number of Nodes
#SBATCH --ntasks=2           # Number of tasks per job

#SBATCH --job-name=aptinsar        # Job submission name
#SBATCH --output=aptinsar.%A_%a.out   # Output file name with Job ID

#SBATCH --mail-type=END            # Email user when job finishes
#SBATCH --mail-user=jojo8550@colorado.edu # Email address of user

#SBATCH --array=6-20

# purge all existing modules
module purge

# load any modules needed to run your program
unset LD_LIBRARY_PATH
module load singularity/3.6.4

# location of the DEM to pass to insar_5m.py
export DEM_LOCATION=/projects/jojo8550/dems/Lagos/5m/

#Extract names of granules for given array ID
REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosRef5.txt)
SND_GRANULE=$(sed -n "$(expr $SLURM_ARRAY_TASK_ID + 1)p" LagosSec5.txt)

# The directory where you want the job to run. Edited to follow expected input convention for time series creation with STARTDATE_ENDDATE
JOBDIR=/scratch/summit/$USER/Lagos/5m/${REF_GRANULE:17:8}_${SND_GRANULE:17:8}

export JOBDIR
mkdir -p $JOBDIR
cd $JOBDIR

cp /projects/jojo8550/containers/arcgis_template.xml arcgis_template.xml
cp /projects/jojo8550/containers/topsApp_template5m.xml topsApp_template.xml
cp /projects/jojo8550/containers/insar_5m.py insar.py

#singularity exec --bind ${PWD}:/output --bind ./applications:/opt/isce2.3/applications /projects/jojo8550/containers/apt-insar.sif python3 -u insar.py \
singularity exec --bind ${PWD}:/output --bind /scratch/summit /projects/jojo8550/containers/apt-insar.sif python3 -u insar.py \
 --reference-granule $REF_GRANULE \
 --secondary-granule $SND_GRANULE \
 --username jojohnson --password summitS3tuo
