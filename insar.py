#!/usr/bin/env python3

import numpy as np
import os
import subprocess
import re
import requests
import shutil
import datetime

from shutil import rmtree
from argparse import ArgumentParser
from zipfile import ZipFile
from getpass import getpass
from html.parser import HTMLParser
from jinja2 import Template
from get_dem import get_ISCE_dem
from shapely.geometry import Polygon

# added in to load local DEM here instead of in ode. Edit line below
DEM_LOCATION = os.environ["DEM_LOCATION"]


CHUNK_SIZE = 5242880
CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
QC_URL = "https://scihub.copernicus.eu/gnss/"

#Generic credentials to query and download orbit files
credentials = ('gnssguest', 'gnssguest')

orbitMap = [('precise', 'AUX_POEORB'),
            ('restituted', 'AUX_RESORB')]

datefmt = "%Y%m%dT%H%M%S"
queryfmt = "%Y-%m-%d"
queryfmt2 = "%Y/%m/%d/"

outdir = './'

COLLECTION_IDS = [
    "C1214470488-ASF",  # SENTINEL-1A_SLC
    "C1327985661-ASF",  # SENTINEL-1B_SLC
]
USER_AGENT = "python3 asfdaac/apt-insar"

def write_output_xml(reference_granule, secondary_granule, product_type, output_file, dem_name):
    template = get_xml_template("arcgis_template.xml")
    data = {
        "reference_granule": reference_granule["name"],
        "secondary_granule": secondary_granule["name"],
        "now": datetime.datetime.now(),
        "product_type": product_type,
        "dem_name": dem_name,
    }
    rendered = template.render(data)
    with open(output_file, "w") as f:
        f.write(rendered)


def get_polygon(entry):
    points = entry["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["GPolygons"][0]["Boundary"]["Points"]
    poly = [[point["Latitude"], point["Longitude"]] for point in points]
    return Polygon(poly)


def get_bounding_box(polygon):
    return {
        "lat_min": polygon.bounds[0],
        "lon_min": polygon.bounds[1],
        "lat_max": polygon.bounds[2],
        "lon_max": polygon.bounds[3],
    }


def update_xml_with_image_type(input_file):
    xml_file = input_file + ".xml"
    sed_command = 's|</imageFile>|<property name="image_type"><value>unw</value><doc>Image type used for displaying.</doc></property></imageFile>|'
    system_call(["sed", "-i", sed_command, xml_file])


def create_browse(input_file, output_file):
    temp_png_file = os.path.basename(input_file) + ".png"
    update_xml_with_image_type(input_file)
    system_call(["mdx.py", input_file, "-kml", "browse.kml"])
    system_call(["gdal_translate", "-of", "PNG", "-outsize", "0", "1024", temp_png_file, output_file])


def create_geotiff(input_file, output_file, input_band=1):
    temp_file = "tmp.tif"
    system_call(["gdal_translate", "-of", "GTiff", "-a_nodata", "0", "-b", str(input_band), input_file, temp_file])
    system_call(["gdaladdo", "-r", "average", temp_file, "2", "4", "6", "8"])
    system_call(["gdal_translate", "-co", "TILED=YES", "-co", "COPY_SRC_OVERVIEWS=YES", "-co", "COMPRESS=DEFLATE", temp_file, output_file])
    os.unlink(temp_file)


def generate_output_files(reference_granule, secondary_granule, dem_name, input_folder="merged", output_folder="/output"):
    print("\nGenerating output files")
    name = f"S1-INSAR-{reference_granule['acquisition_date']}-{secondary_granule['acquisition_date']}"
    create_geotiff(f"{input_folder}/phsig.cor.geo", f"{output_folder}/{name}-COR.tif")
    write_output_xml(reference_granule, secondary_granule, "COR", f"{output_folder}/{name}-COR.tif.xml", dem_name)
    create_geotiff(f"{input_folder}/filt_topophase.unw.geo", f"{output_folder}/{name}-AMP.tif", input_band=1)

    write_output_xml(reference_granule, secondary_granule, "AMP", f"{output_folder}/{name}-AMP.tif.xml", dem_name)
    create_geotiff(f"{input_folder}/filt_topophase.unw.geo", f"{output_folder}/{name}-UNW.tif", input_band=2)
    write_output_xml(reference_granule, secondary_granule, "UNW", f"{output_folder}/{name}-UNW.tif.xml", dem_name)
    create_browse(f"{input_folder}/filt_topophase.unw.geo", f"{output_folder}/{name}.png")


def system_call(params):
    print(" ".join(params))
    return_code = subprocess.call(params)
    if return_code:
        exit(return_code)


def get_xml_template(template_name):
    with open(template_name, "r") as t:
        template_text = t.read()
    template = Template(template_text)
    return template


def write_topsApp_xml(reference_granule, secondary_granule, dem_filename=None):
    template = get_xml_template("topsApp_template.xml")
    rendered = template.render(reference_granule=reference_granule, secondary_granule=secondary_granule, dem_filename=dem_filename)
    with open("topsApp.xml", "w") as f:
        f.write(rendered)


def run_topsApp(reference_granule, secondary_granule, dem_filename=None):
    print("\nRunning topsApp.py")
    write_topsApp_xml(reference_granule, secondary_granule, dem_filename)
    system_call(["topsApp.py", "--steps", "--end=geocode"])


def get_orbit_url(granule, orbit_type):
    platform = granule[0:3]
    date_time = f"{granule[17:21]}-{granule[21:23]}-{granule[23:25]}T{granule[26:28]}:{granule[28:30]}:{granule[30:32]}"

    params = {
        "product_type": orbit_type,
        "product_name__startswith": platform,
        "validity_start__lt": date_time,
        "validity_stop__gt": date_time,
        "ordering": "-creation_date",
        "page_size": "1",
    }

    response = requests.get(QC_URL, params=params, auth=credentials)
    response.raise_for_status()
    qc_data = response.json()

    orbit_url = None
    if qc_data["results"]:
        orbit_url = qc_data["results"][0]["remote_url"]
    print('Orbit URL: ', orbit_url)
    return orbit_url


def fileToRange(fname):
    '''
    Derive datetime range from orbit file name.
    '''

    fields = os.path.basename(fname).split('_')
    start = datetime.datetime.strptime(fields[-2][1:16], datefmt)
    stop = datetime.datetime.strptime(fields[-1][:15], datefmt)
    mission = fields[0]

    return (start, stop, mission)

def FileToTimeStamp(safename):
    '''
    Return timestamp from SAFE name.
    '''
    safename = os.path.basename(safename)
    fields = safename.split('_')
    sstamp = []  # sstamp for getting SAFE file start time, not needed for orbit file timestamps

    sstamp = datetime.datetime.strptime(fields[-5], datefmt)
    p = re.compile(r'(?<=_)\d{8}')
    dt2 = p.search(safename).group()
    tstamp = datetime.datetime.strptime(dt2, '%Y%m%d')

    satName = fields[0]

    return tstamp, satName, sstamp


class MyHTMLParser(HTMLParser):

    def __init__(self,url):
        HTMLParser.__init__(self)
        self.fileList = []
        self._url = url
        
    def handle_starttag(self, tag, attrs):
        for name, val in attrs:
            if name == 'href':
                if val.startswith("https://scihub.copernicus.eu/gnss/odata") and val.endswith(")/"):
                    pass
                else:
                    downloadLink = val.strip()
                    downloadLink = downloadLink.split("/Products('Quicklook')")
                    downloadLink = downloadLink[0] + downloadLink[-1]
                    self._url = downloadLink
                
    def handle_data(self, data):
        if data.startswith("S1") and data.endswith(".EOF"):
            self.fileList.append((self._url, data.strip()))


def get_orbit_file(granule):

    print('granule=',granule)

    fileTS, satName, fileTSStart = FileToTimeStamp(granule)
 
    print('fileTSStart=',fileTSStart)
    print('fileTS=',fileTS)
    tstamp = fileTS
    print('filename=',fileTS)
    print('Reference time: ', fileTS)
    print('Satellite name: ', satName)
    match = None
    session = requests.Session()

    for spec in orbitMap:
        oType = spec[0]
        delta = datetime.timedelta(days=1)
        print('delta=', delta)        
        timebef = (fileTS - delta).strftime(queryfmt)
        timeaft = (fileTS + delta).strftime(queryfmt)
#        timebef = `date -d "$fileTS -delta"`
#        timeaft = `date -d "$fileTS +delta"`
        print('timebef=',timebef)
        print('timeaft=',timeaft)
        url = QC_URL + 'search?q=( beginPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z] AND endPosition:[{0}T00:00:00.000Z TO {1}T23:59:59.999Z] ) AND ( (platformname:Sentinel-1 AND filename:{2}_* AND producttype:{3}))&start=0&rows=100'.format(timebef,timeaft, satName,spec[1])
        
        print('url=',url)

        success = False
        match = None
  
        try:
            r = session.get(url, verify=True, auth=credentials)
            r.raise_for_status()
            parser = MyHTMLParser(url)
            parser.feed(r.text)
            for resulturl, result in parser.fileList:
                tbef, taft, mission = fileToRange(os.path.basename(result))
                if (tbef <= fileTSStart) and (taft >= fileTS):
                    matchFileName = result
                    orbit_file = result
                    match = resulturl

            if match is not None:
                success = True
        except:
            pass

        if success:
            break
    
    print(f"\n{match}")
    print(f"\n{orbit_file}")
    print(f"\n{outdir}")

    if match is not None:
        output = os.path.join(outdir, matchFileName)
        res = download_orbit_file(match, output, session)
        if res is False:
            print('Failed to download URL: ', match)
    else:
        print('Failed to find {1} orbits for tref {0}'.format(fileTS, satName))

    return orbit_file


def unzip(zip_file):
    print(f"Extracting {zip_file}")
    with ZipFile(zip_file, "r") as zip_handle:
        zip_handle.extractall()
    os.unlink(zip_file)


def download_file(url):
    print(f"\nDownloading {url}")
    local_filename = url.split("/")[-1]
    headers = {"User-Agent": USER_AGENT}
    with requests.get(url, headers=headers, stream=True) as r:
        if r.status_code == 401:
            print("ERROR: Invalid username or password")
            exit(1)
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
    return local_filename


def download_orbit_file(url, outdir='.', session=None):
    if session is None:
        session = requests.session()

    path = outdir
    print('Downloading URL: ', url)
    request = session.get(url, stream=True, verify=True, auth=credentials)

    try:
        val = request.raise_for_status()
        success = True
    except:
        success = False

    if success:
        with open(path, 'wb') as f:
            for chunk in request.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

    return success


def get_attribute(entry, attribute_name):
    for attribute in entry["AdditionalAttributes"]:
        if attribute["Name"] == attribute_name:
            return attribute["Values"][0]
    return None


def get_download_url(entry):
    for url in entry["RelatedUrls"]:
        if url["Type"] == "GET DATA":
            return url["URL"]
    return None


def get_cmr_metadata(granule):
    params = {
        "readable_granule_name": granule,
        "provider": "ASF",
        "collection_concept_id": COLLECTION_IDS
    }
    response = requests.get(url=CMR_URL, params=params)
    response.raise_for_status()
    cmr_data = response.json()

    if not cmr_data["items"]:
        return None

    entry = cmr_data["items"][0]["umm"]
    polygon = get_polygon(entry)
    granule_metadata = {
        "acquisition_date": granule[17:25],
        "bbox": get_bounding_box(polygon),
        "directory": f"{granule}.SAFE",
        "polygon": polygon,
        "name": granule,
        "path_number": get_attribute(entry, "PATH_NUMBER"),
        "download_url": get_download_url(entry),
    }

    return granule_metadata


def get_metadata(granule):
    print(f"\nChecking {granule}")
    granule_metadata = get_cmr_metadata(granule)

    if granule_metadata:
        granule_metadata["orbit_file"] = get_orbit_file(granule)

    return granule_metadata


def get_granule(granule):
    granule_zip = download_file(granule)
    unzip(granule_zip)


def validate_granules(reference_granule, secondary_granule):
    if not reference_granule:
        print(f"\nERROR: Either reference granule does not exist or it is not a SLC product")
        exit(1)
    if not secondary_granule:
        print(f"\nERROR: Either secondary granule does not exist or it is not a SLC product")
        exit(1)
    if not reference_granule["polygon"].intersects(secondary_granule["polygon"]):
        print("\nERROR: The reference granule and the secondary granule do not overlap.")
        exit(1)
    if reference_granule["path_number"] != secondary_granule["path_number"]:
        print("\nERROR: The reference granule and the secondary granule are not on the same track.")
        exit(1)


def get_dem(dem, bbox):
    if dem == "ASF":
        print("\nPreparing digital elevation model")
        dem_filename = "dem.envi"
        xml_filename = f"{dem_filename}.xml"
        dem_name = get_ISCE_dem(bbox["lon_min"], bbox["lat_min"], bbox["lon_max"], bbox["lat_max"], dem_filename, xml_filename)
        os.unlink("temp.vrt")
        os.unlink("temp_dem.tif")
        if os.path.exists("temp_dem_wgs84.tif"):
            os.unlink("temp_dem_wgs84.tif")
        rmtree("DEM")
        return dem_filename, dem_name
    else:
        return None, "SRTMGL1"


def write_netrc_file(username, password):
    netrc_file = os.environ["HOME"] + "/.netrc"
    with open(netrc_file, "w") as f:
        f.write(f"machine urs.earthdata.nasa.gov login {username} password {password}")

def get_args():
    parser = ArgumentParser(description="Sentinel-1 InSAR using ISCE")
    parser.add_argument("--reference-granule", "-r", type=str, help="Reference granule name.", required=True)
    parser.add_argument("--secondary-granule", "-s", type=str, help="Secondary granule name.", required=True)
    parser.add_argument("--username", "-u", type=str, help="Earthdata Login username.")
    parser.add_argument("--password", "-p", type=str, help="Earthdata Login password.")
    parser.add_argument("--dem", "-d", type=str, help="Digital Elevation Model. ASF automatically selects the best geoid-corrected NED/SRTM DEM.  SRTM uses ISCE's default settings.", choices=["ASF", "SRTM"], default="ASF")
    args = parser.parse_args()

    if not args.username:
        args.username = input("\nEarthdata Login username: ")

    if not args.password:
        args.password = getpass("\nEarthdata Login password: ")

    return args



if __name__ == "__main__":
    args = get_args()
    write_netrc_file(args.username, args.password)

    reference_granule = get_metadata(args.reference_granule)
    secondary_granule = get_metadata(args.secondary_granule)

    validate_granules(reference_granule, secondary_granule)

    dem_filename = "dem.envi"
    xml_filename = f"{dem_filename}.xml"
    dem_name = "dem.envi"

    shutil.copy(DEM_LOCATION, "./")
    shutil.copy(DEM_LOCATION +".xml", "./")

    get_granule(reference_granule["download_url"])
    get_granule(secondary_granule["download_url"])

    run_topsApp(reference_granule, secondary_granule, dem_filename)
    generate_output_files(reference_granule, secondary_granule, dem_name)
