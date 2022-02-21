# Helpful scripts for generating MSBAS timeseries. 
Versions of these scripts also exist at https://github.com/jaha2600/ISCE-MSBAS-Codes , along with a containerized version of MSBAS which can be used to quickly test a range of R values for time series generation. 

## SummitMovescript.py is for substantially cutting down the amount of data transferred off of Summit.

You want to copy it into /scratch/summit/$USER/Lagos/5m or wherever your date pairs starting with 20**_20** are stored. Then you call it by saying $: python movescript.py $PWD
It also has a few lines of help, which can be called with python movescript.py -h

It generates a text file with your failed pairs, and makes a folder called MSBAS_FILES that saves only the files needed for MSBAS in the correct format. This script is compatible with the setup script for MSBAS, msbasPrep.py

There is an additional -rm flag that removes the big files you don't need. It isn't always that useful because once you've ran the script, you can just delete the entire directories unless you need them for something other than MSBAS. 

Depending on your file sizes, it can cut down storage from 50-90gigs per interferogram to 4gigs in the MSBAS_FILES folder. With the -rm flag, it reduces each original interferogram storage to about 30-40gigs.

## msbasPrep.py sets up header file for MSBAS, but does still require the R, C and I flag to be configured. 
Command for running on local machine. Takes formatted files moved from SUMMIT and prepares them for usage with MSBAS. Needs to be handed a inputs.txt with extents in SNWE format as well as a directory to run on.
