# EditsToISCEContainer
Edits to code provided by CU Boudler Research Computing container to run on RMACC. Their container can be found here: https://github.com/ResearchComputing/asf-insar-singularity
That container is based on the Docker provided by ASF Vertex here: https://github.com/asfadmin/apt-insar

Notes here are based on my workflow and subject to future change and clarification

## ISCE with Research computing setup: Steps for using your own DEM and submitting job arrays

#### 1. Follow all the steps to download the ASF DOCKER from the RC Computing github: https://github.com/ResearchComputing/asf-insar-singularity

### 2. Copy the following files into your containers directory, which is created in the installation in step one. 
*jobscript_5m_array.sh
*arcgis_template.xml
*topsApp_5m template.xml
*SARimagelistexample.txt (You will need to make a reference list and a secondary list from this)

### 3. Edit jobscript_5m_array settings. Relevant ones to change are listed here in the order they appear:
 #SBATCH --ntasks sets the number of tasks per job. It is more efficient to run larger batched jobs with the least number of tasks possible, while still finishing the job under 24 hours.
 
#SBATCH --mail-user input for the email address of the user, which receives an alert when the job finishes running

#SBATCH --array declares which of the array elements to run, up to 1000 pairs in parallel. This is based off of a text file that lists SAR images to be downloaded from ASF. The provided example has a list of images over Mumbai, with path 34, Frame 527, descending view. 

SARimagelistexample.txt is set to a text file list of SLC images to process sequentially.

#Extract names of granules for given array ID. You will need to make a list pairs, or in this case a reference secondary image list. More on this in step 5. My naming convention has the path, frame, and other info included. 

REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" MumbaiP34F527DescVVgranules.txt)
SND_GRANULE=$(sed -n "$(expr $SLURM_ARRAY_TASK_ID + 1)p" MumbaiP34F527DescVVgranules.txt)
	

JOBDIR can also be changed according to your file structure. A quick sketch of mine is provided at the bottom of the instructions 
Be sure the –username and –password fields have your earthdata login instead of mine. *Make a link to earthdata setup here
### 4. DEM setup: 
The DOCKER wants a dem in  “dem.envi” format, and I have not changed. Convert the DEM (in my case, .tif files that came with geoid removed) to .envi using gdal_translate.
($ gdal_translate -of envi smaller_10m.tif mumbai10m.envi)

Create an .xml file for the DEM. The automated gdal creation with the previous command is .aux.xml, which is not what you need. Use gdal2isce_xml.py, which creates an envi.xml file for you. 
($ gdal2isce_xml.py -i mumbai10m.envi)

Copy both the DEM and the of these files into summit, in a directory you specify to the container in the following step. The example has my path, which follows the infrastructure displayed at the bottom. *show how to transfer


Rename both the dem and the associated xml file as dem.envi and dem.envi.xml so they work with the docker seamlessly

#### DEM setup part B: 
open topsApp_template5m.xml.

Edit the <property name=”dem filename”> path to match wherever you store your DEM on summit. 

For best results, I recommend also running gdal_info on your local DEM, and getting a coordinate list of the boundaries of your DEM so it doesn’t process more data than needed. Provide the coordinates in the following order, SNWE. Below is an example of the coordinates from my Lagos DEM. 





I then add in the following region of interest and geocode bounding box so only the area covered by my DEM is processed. 
Lagos DEM bounding: 6.0229007, 7.0312007, 3.0039348, 4.0172348 


### 5. SAR granules list setup. It is possible to get these lists from a couple different sites, and to generate lists that do more than run sequentially. As an example, here’s the one I used for my setup
	Start at https://search.asf.alaska.edu/#/ 
	
	Select your geographic area of interest with dataset of Sentinel 1, File type L1 SLC, as pictured below
	

Once you find a frame and path that fits your area of interest, you can use the filters to only show this Frame+Path images. 





Search again with the path and frame in your filter, which should narrow down the list of images. Add all results to downloads, open downloads, and select the “Copy file IDs” option on the bottom. 


Save this SLC list in a text file to the same containers directory, and double check that it matches the name given to the variable SLC_LIST in jobscript_10m_array.sh. If you are simply pairing each with the consecutive image, you can use the following format to pair them. 

If you are running multiple secondary images with the same reference, you will need to generate a list. I hope to provide a script to generate these in the future.


### 6. Submit the job to SUMMIT using the following command: $ sbatch jobscript_5m_array.sh
	Progress can be checked by using the sacct command. By following these instructions, an email will be sent when it finishes. 
	The completed files will be placed wherever JOBDIR is set to, in the jobscript_5m_array.sh file.

*Explanation of what the results are.. explain by naming convention.

Best of luck! If additional questions remain, feel free to email me.




Sketch of file infrastructure, referenced earlier in instructions:
 
