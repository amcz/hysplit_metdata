
# hysplit_metdata

### get_era5_cds.py 
Code to download ERA5 meteorological data from ECMWF that will suitable for converting to ARL format for ingestion into HYSPLIT.
The downloaded grib files will be suitable for use with the era52arl program available with the HYSPLIT distribution.

get_era5_cds.py uses cdsapi module from Copernicus Data Service.
ERA5 is now  only available through the cdsapi.
ecmwf-api is no longer supported.

PYTHON 3.x
Written to run on linux operating system

This python program aids in retrieving  meteorological variables from the ERA5 dataset which HYSPLIT needs.
grib files can be input into the era52arl fortran utility program (provided with the HYSPLIT distrubtion) 
to create a meteorological file that can be used
as input into HYSPLIT. 

for command line options run with --help <br>
The program will write a file called new_era52arl.cfg. This file can be used as an input into the era52arl conversion program.
It should be renamed  era52arl.cfg  to be read automatically by the program.
Currently era52arl can only convert data on pressure levels.
There are plans to add capability to convert data on the model levels.

era52arl will also convert the ensemble data.

### era52arl.f
The fortran program era52arl.f is included in the data2arl directory of the HYSPLIT distribution.
Beta versions may be included here. era52arl.f requires eccodes as well as libraries included in the HYSPLIT distribution 
to compile. 

# Possible Issues

### friction velocity

"The instantaneous turbulent surface stress components (eastward and northward) and friction velocity tend to be too small"
https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation (search for friction velocity)

Users may not want to use friction velocity, HYSPLIT code USTR, grib short name zust.
This quantity is usually used in the default setting KBLS=1 to calculate stability (see https://ready.arl.noaa.gov/hysplitusersguide/S625.htm).

Using this may lead to inaccurate estimations of stability and undermixing which may be related to this issue.

To make sure HYSPLIT does not use the friction velocity from ERA5 the following can be done.

* If ustr is already in the converted file and you do not want to convert the file again. set kbls=2 in the SETUP.CFG file.

* If you have not converted the files yet.
edit the era52arl.cfg file which is input into the era52arl program and remove the ustr column. Then the conversion program will not add the friction velocity to the ARL file.

* edit the get_era5_cds.py so that USTR is not downloaded.

### heat fluxes (LTHF, SHTF)

HYSPLIT convention is that upward heat flux is positive. ERA5 uses the opposite convention.

Make sure that a conversion factor is negative in the era52arl.cfg file. 


# installing cdsapi
https://cds.climate.copernicus.eu/api-how-to
You will need to create an account with Copernicus Data Service to receive an api key.
The api key must be stored in $HOME/.cdsapirc

## get_era5.py uses the ecmwf-api which is no longer supported.

# Sample Requests

## Pressure level data
    levels = [1000,975,950,925,900,875,850,825,800,775,750,700,650,600,550,500,450,400,350,300,250,225,200,175,150,125,100,70,50,30,20,10,7,5,3,2,1]
    timestr = '00:00/01:00/02:00/03:00/04:00/05:00/06:00/07:00/08:00/09:00/10:00/11:00/12:00/13:00/14:00/15:00/16:00/17:00/18:00/19:00/20:00/21:00/22:00/23:00'
    import cdsapi
    c = cdsapi.Client()
    c.retrieve('reanalysis-era5-pressure-levels',
               {
                 'variable' : ['temperature','u_component_of_wind','v_component_of_wind','vertical_velocity','relative_humidity','geopotential'],
                 'pressure_level': list(map(str,levels)),
                 'product_type' : 'reanalysis',
                 'grid' : '0.25/0.25',
                 'time' : timestr.split('/'),
                 'year' : '2020',
                 'month': '1',
                 'day' : '1',
                 'format' : 'grib'
                 },
                 'outputname')

## Surface data
    c = cdsapi.Client()
    c.retrieve('reanalysis-era5-single-levels',
               {
                 'variable' : ['2m_temperature','10m_u_component_of_wind','10m_v_component_of_wind','surface_pressure',\
                               'boundary_layer_height','geopotential','friction_velocity'],
                 'product_type' : 'reanalysis',
                 'grid' : '0.25/0.25',
                 'time' : timestr.split('/'),
                 'year' : '2020',
                 'month': '1',
                 'day' : '1',
                 'format' : 'grib'
                 },
                 'outputname')

## Ensemble data pressure levels
    paramstr = '130.128/131.128/132.128/135.128/157.128/128.128'
    timestr = '00:00/03:00/06:00/09:00/12:00/15:00/18:00/21:00'
    levels = [1000,975,950,925,900,875,850,825,800,775,750,700,650,600,550,500,450,400,350,300,250,225,200,175,150,125,100,70,50,30,20,10,7,5,3,2,1]
    c = cdsapi.Client()
    c.retrieve('reanalysis-era5-complete',
              {
                'class' : 'ea',
                'expver' : '1',
                'dataset' : 'era5',
                'stream' : 'enda',
                'levtype' : 'pl',
                'origin' : 'all',
                'format' : 'grib',
                'grid' : '0.25/0.25',
                'date' : '2020-01-01',
                'time' : timestr,
                'param' : paramstr,
                'levelist' : str.join('/',map(str,levels)),
                'number' : '0/1/2/3/4/5/6/7/8/9'
                },
                'outputname')
                
## Ensemble data surface variables

Note that slhf (surface latent heat flux), sshf (surface sensible heat flux), and tp (total precipitation) are not
currently available for the ensemble (enda stream).

     paramstr = '167.128/166.128/165.128/134.128/159.128/59.128/129.128/'
     c = cdsapi.Client()
     c.retrieve('reanalysis-era5-complete',
              {
                'class' : 'ea',
                'expver' : '1',
                'dataset' : 'era5',
                'stream' : 'enda',
                'levtype' : 'sfc',
                'origin' : 'all',
                'format' : 'grib',
                'grid' : '0.25/0.25',
                'date' : '2020-01-01',
                'time' : timestr,
                'param' : paramstr,
                'number' : '0/1/2/3/4/5/6/7/8/9'
                },
                'outputname')


# Checking your grib file

eccodes has some useful command line tools to check what is in your grib files.
https://confluence.ecmwf.int/display/ECC/GRIB+tools

Example

    grib_dump gribfile.grib > out
    
# conversion factors

surface radition accumulated parameters (slhf, ssrd, sshf)

https://confluence.ecmwf.int/pages/viewpage.action?pageId=155337784
