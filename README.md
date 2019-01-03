# hysplit_metdata uses the ecmwf-api
# hysplit_metdata_cds (under construction) uses cdsapi from Copernicus data service.
ERA5 will soon only be available through the cdsapi.

Code to download ERA5 meteorological data from ECMWF that will suitable for converting to ARL format for ingestion into HYSPLIT.

There may be an problem with the  velocity fiels on the pressure levels. See:
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
See https://confluence.ecmwf.int/display/CKB/C3S+ERA5%3A+Web+API+to+CDS+API
You will need to create an account with Copernicus Data Service to receive an api key.

# Installing ecmwfapi module
For instructions on creating an ecmwf account and retrieving a key see <br>
[https://software.ecmwf.int/wiki/display/WEBAPI/Accessing+ECMWF+data+servers+in+batch]

The api key must be stored in the $HOME/.ecmwfapirc file. <br>
The api key can be found at [https://api.ecmwf.int/v1/key/]

You may also download the tar file from the webpage and place the ecmwfapi directory so
that is in your PYTHONPATH or it can also be a subdirectory of the directory where get_era5.py is located.

If you have conda you  can also install by
conda install -c conda-forge ecmwf-api-client
