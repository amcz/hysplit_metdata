# hysplit_metdata

Code to download ERA5 meteorological data from ECMWF that will suitable for converting to ARL format for ingestion into HYSPLIT.

Must have ecmwfapi installed. 
[https://software.ecmwf.int/wiki/display/WEBAPI/Accessing+ECMWF+data+servers+in+batch]

The api key must be stored in the $HOME/.ecmwfapirc file.
The api key can be found at [https://api.ecmwf.int/v1/key/]

For instructions on creating an ecmwf account and retrieving a key see
[https://software/ecmwf.int/wiki/display/WEBAPI/ACESS_ECMWF+Public+Datasets]

grib files can be input into the era52arl fortran utility program to create a meteorological file that can be used
as input into HYSPLIT. 

This python program aids in retrieving  meteorological variables from the ERA5 dataset which HYSPLIT needs.

for command line options run with --help

writes a file called get_era5_message.txt 
writes a file called new_api2arl.cfg



