
# hysplit_metdata_cds 
Code to download ERA5 meteorological data from ECMWF that will suitable for converting to ARL format for ingestion into HYSPLIT.
The downloaded grib files will be suitable for use with the era52arl program available with the HYSPLIT distribution.
The era52arl program will be updated in the HYPSLIT repository as soon as the government shutdown ends.

hysplit_metdata_cds uses cdsapi module from Copernicus Data Service.
ERA5 will soon only be available through the cdsapi.
If you are using ecmwf-api see below.

There may be a problem with the  velocity fields on the pressure levels. See:
https://confluence.ecmwf.int/pages/viewpage.action?pageId=127305868

PYTHON 3.x
Written to run on linux operating system

This python program aids in retrieving  meteorological variables from the ERA5 dataset which HYSPLIT needs.
grib files can be input into the era52arl fortran utility program (provided with the HYSPLIT distrubtion) 
to create a meteorological file that can be used
as input into HYSPLIT. 

for command line options run with --help <br>
The program will write a file called new_era52arl.cfg. This file can be used as an input into the era52arl conversion program.
It should be renamed  era52arl.cfg  to be read automatically by the program.

# installing cdsapi
https://cds.climate.copernicus.eu/api-how-to
You will need to create an account with Copernicus Data Service to receive an api key.

# hysplit_metdata uses the ecmwf-api
# Installing ecmwfapi module
For instructions on creating an ecmwf account and retrieving a key see <br>
[https://software.ecmwf.int/wiki/display/WEBAPI/Accessing+ECMWF+data+servers+in+batch]

The api key must be stored in the $HOME/.ecmwfapirc file. <br>
The api key can be found at [https://api.ecmwf.int/v1/key/]

You may also download the tar file from the webpage and place the ecmwfapi directory so
that is in your PYTHONPATH or it can also be a subdirectory of the directory where get_era5.py is located.

If you have conda you  can also install by
conda install -c conda-forge ecmwf-api-client
