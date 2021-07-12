# EditsToISCEContainer
Edits to code provided by CU Boulder Research Computing container to run on RMACC. Their container can be found here: https://github.com/ResearchComputing/asf-insar-singularity
That container is based on the Docker provided by ASF Vertex here: https://github.com/asfadmin/apt-insar

Notes here are based on my workflow and subject to future change and clarification. Screenshots of particular steps to soon come. Currently in the following google doc: https://docs.google.com/document/d/1LAg0LL7I1km-GsywRS7GRg-eoM9lgSfYTsFIydGYXHY/

## ISCE with Research computing setup: Steps for using your own DEM and submitting job arrays

#### 1. Follow all the steps to download the ASF DOCKER from the RC Computing github: https://github.com/ResearchComputing/asf-insar-singularity

### 2. Copy the following files into your containers directory, which is created in the installation in step one. 
* jobscript_array.sh
* arcgis_template.xml -no edits are needed
* insar.py -no edits needed 
* topsApp_5m template.xml
* LagosP1F16Asc.txt -Provided as an example of an input file

### 3. Edit jobscript_5m_array settings. Relevant ones to change are listed here in the order they appear:
 #SBATCH --ntasks sets the number of tasks per job. It is more efficient to run larger batched jobs with the least number of tasks possible, while still finishing the job under 24 hours.
 
#SBATCH --mail-user input for the email address of the user, which receives an alert when the job finishes. Change this to your own email

#SBATCH --array declares which of the array elements to run, up to 1000 pairs in parallel. This command  is based off of a text file that lists SAR images to be downloaded from ASF. The provided example has a list of images over Lagos, with path 1, Frame 16, ascending view. 

SARimagelistexample.txt is set to a text file list of SLC images to process sequentially.

#Extract names of granules for given array ID. You will need to make a list pairs, or in this case a reference secondary image list. My naming convention has the path, frame, and other info included. The code below will match each reference granule with the following image. Edits can be made to run one reference image against several secondaries. More on this in step 5.

REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosP1F16Asc.txt)

SND_GRANULE=$(sed -n "$(expr $SLURM_ARRAY_TASK_ID + 1)p" LagosP1F16Asc.txt)
	

JOBDIR can also be changed according to your file structure. A quick sketch of mine is provided at the bottom of the instructions 
Be sure the –username and –password fields have your earthdata login instead of mine. *Make a link to earthdata setup here
### 4. DEM setup: 
The DOCKER wants a dem named “dem.envi” with SRTM pixel convention. These instructions assume that you have access to a DEM for processing. If you are happy with a standard DEM, you can skip this step.

Convert the DEM (in my case, .tif files that came with geoid removed) to .envi using gdal_translate.
($ gdal_translate -of envi smaller_10m.tif lagos10m.envi)

Rename the DEM to dem.envi, so the metadata files are consistent. 
($ mv lagos10m.envi dem.envi)

If ISCE is installed on your machine, you can convert and prep the DEM using gdal2isce_xml.py. It will generate an .xml and .vrt file automatically. If you do this, the final DEM step is to edit dem.envi.xml and change <property name="file_name"> to the location dem.envi will be stored on Summit.
($ gdal2isce_xml.py -i dem.envi)

Below are workaround instructions if ISCE is not installed

For SRTM pixel convention:
Now that the DEM is set up, edit the following fields in demeexample.envi.xml according to the output from calling gdalinfo on the newly created DEM. then rename the demexample.envi.xml to match your dem.
$gdalinfo dem.envi

Component Name (in .xml file) | | gdalinfo output
--- | --- | --- |
coordinate1 - delta |  | Pixel Size [0]
coordinate1 - starting value* | | Origin [0]
coordinate1 - size | | Size [0]
coordinate2 - delta | | Pixel Size [1]
coordinate2 - starting value* | | Origin [1]
coordinate2 - size| | Size [1]
length | | Size [1]
width | | Size [0]
FIRST_LONGITUDE | | Origin [0]
DELTA_LATITUDE | | Pixel Size [1]
FIRST_LATITUDE | | Origin [1]

Edit the <property name="file_name"> in the dem.xml file to match the location dem.envi will be stored on Summit

Generate a .vrt file to complete the necessary files for processing
($ gdalbuildvrt dem.envi.vrt dem.envi)

Copy dem.envi, dem.envi.xml, and dem.envi.vrt to Summit, in a directory you specified in the previous step. The example has my path, which follows the infrastructure displayed at the bottom. 

* In the future I will have instructions on how to make this transfer. Easiest way for large transfers is globus connect, instructions here https://curc.readthedocs.io/en/latest/compute/data-transfer.html. 


#### DEM setup part B: 
open topsApp_template5m.xml.

Edit the <property name=”dem filename”> path to match the stored DEM on Summit. 

Run gdal_info on your DEM, and make note of the corner coordinates in the output. Fill in the coordinates of the entire DEM in the "region of interest" and "geocode bounding box", or a smaller subset in SNWE order.
example: 
<property name="region of interest">[6.0229007, 7.0312007, 3.0039348, 4.0172348]</property>
<property name="geocode bounding box">[6.0229007, 7.0312007, 3.0039348, 4.0172348]</property>

Finally, open jobscript_5m_array.sh
Edit the "export DEM_LOCATION=/projects/jojo8550/dems/Lagos/5m/" to wherever your DEM is stored



### 5. SAR granules list setup. It is possible to get these lists from a couple different sites, and to generate lists that do more than run sequentially. As an example, here’s the one I used for my setup. I recommend looking at the google doc linked at the top for images of each section
Start at https://search.asf.alaska.edu/#/ 
	
Select your geographic area of interest with dataset of Sentinel 1, File type L1 SLC, as pictured below
	

Find a frame and path that fits your area of interest, you can use the filters to only show this Frame+Path images. 


Search again with the path and frame in your filter, which should narrow down the list of images. Add all results to downloads, open downloads, and select the “Copy file IDs” option on the bottom. 


Save this SLC list in a text file to the same containers directory, and double check that it matches the name given to the variable SLC_LIST in jobscript_10m_array.sh. If you are simply pairing each with the consecutive image, you can use the provided example format.

If you are running multiple secondary images with the same reference, you will need to generate a list. I hope to provide a script to generate these in the future. At the moment, you can use the provided LagosP1RefSample.txt and LagosP1SecSample.txt as an example. To do so, you would change REF_GRANULE and SEC_GRANULE in jobscript_5m
	
	REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosP1RefSample.txt)
	SND_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosP1SecSample.txt)

### 6. Submit the job to SUMMIT using the following command: $ sbatch jobscript_5m_array.sh
Progress can be checked by using the sacct command. By following these instructions, an email will be sent when it finishes. 
The completed files will be placed wherever JOBDIR is set to, in the jobscript_5m_array.sh file.

* Explanation of what the results are to come in the future.. Will be broken down by naming convention.

Best of luck! If additional questions remain, feel free to reach out.
