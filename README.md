# hysplit_metdata

Code to download ERA5 meteorological data from ECMWF that will suitable for converting to ARL format for ingestion into HYSPLIT.

PYTHON 3.x
Written to run on linux operating system

Must have ecmwfapi installed. 
For instructions on creating an ecmwf account and retrieving a key see <br>
[https://software.ecmwf.int/wiki/display/WEBAPI/Accessing+ECMWF+data+servers+in+batch]

The api key must be stored in the $HOME/.ecmwfapirc file. <br>
The api key can be found at [https://api.ecmwf.int/v1/key/]

grib files can be input into the era52arl fortran utility program to create a meteorological file that can be used
as input into HYSPLIT. 

This python program aids in retrieving  meteorological variables from the ERA5 dataset which HYSPLIT needs.

for command line options run with --help <br>
writes a file called new_era52arl.cfg. This file can be used as an input into the era52arl conversion program.
It should be renamed  era52arl.cfg  to be read automatically by the program.



# Installing ecmwfapi module
Instructions for installing with pip are on the web page.

You may also download the tar file from the webpage and place the ecmwfapi directory so
that is in your PYTHONPATH or it can also be a subdirectory of the directory where get_era5.py is located.

If you have conda you  can also install by
conda install -c conda-forge ecmwf-api-client
