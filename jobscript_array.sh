#!/bin/bash

# Written by: jojo8550@colorado.edu
# Date: 20200709
# Purpose: This script submits a job on Summit. Has been edited to accept a 5m local DEM instead of downloading one. 
# It is possible that the python script still downloads one, but doesn't use it.  
#SBATCH -account=ucb62_summit3     # Summit allocation
#SBATCH --partition=shas     # Summit partition
#SBATCH --qos=normal                 # Summit qos
#SBATCH --time=024:00:00           # Max wall time
#SBATCH --nodes=1            # Number of Nodes
#SBATCH --ntasks=2           # Number of tasks per job

#SBATCH --job-name=aptinsar        # Job submission name
#SBATCH --output=aptinsar.%A_%a.out   # Output file name with Job ID

#SBATCH --mail-type=END            # Email user when job finishes
#SBATCH --mail-user=jojo8550@colorado.edu # Email address of user

#SBATCH --array=1-2

# purge all existing modules
module purge

# clean up LD_LIBRARY_PATH
unset LD_LIBRARY_PATH

# load any modules needed to run your program
module load singularity/3.6.4

# location of the DEM to pass to insar.py
# make sure to change the dem.envi.xml file to put in the correct location
export DEM_LOCATION=/projects/$USER/dems/Lagos/5m/dem.envi

# Extract names of granules for given array ID
# Here the program reads from one file and picks sequential pairs; --array, above, should be one less than the number of images in the file

REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosP1F16Asc.txt)
SND_GRANULE=$(sed -n "$(expr $SLURM_ARRAY_TASK_ID + 1)p" LagosP1F16Asc.txt)

echo $REF_GRANULE 
echo $SND_GRANULE

SETUP_DIR=/scratch/summit/$USER/Lagos/5m
#echo $SETUP_DIR

# The directory where you want the job to run. Edited for naming
JOBDIR=$SETUP_DIR/${REF_GRANULE:17:8}_${SND_GRANULE:17:8}
export JOBDIR
mkdir -p $JOBDIR

#cp *.EOF $JOBDIR
cd $JOBDIR

cp $SETUP_DIR/arcgis_template.xml arcgis_template.xml
cp $SETUP_DIR/insar.py insar.py
cp $SETUP_DIR/topsApp_template.xml topsApp_template.xml

singularity exec --bind ${PWD}:/output --bind /scratch/summit /projects/$USER/containers/apt-insar.sif python3 -u insar.py \
 --reference-granule $REF_GRANULE \
 --secondary-granule $SND_GRANULE \
 --username jojohnson --password summitS3tuo
