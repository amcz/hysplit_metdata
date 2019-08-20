#!/bin/sh
# Example bash script for retrieving ERA5 for a small area.
# Author: Alice Crawford   Organization: NOAA/OAR/ARL 

# Example for downloading and converting ERA5 data on pressure levels
# for a relatively small area.

# python call
MDL="python"

#Location of get_era5_cds.py
PDL=$HOME/hysplit_metdata
year=2017

#small area to retrieve
# upper left lat/ upper left lon / lower right lat / lower right lon
# NORTH/WEST/SOUTH/EAST
area="50/-85/30/-70"

#directory to write files to.
outdir='./'

for month in '01'
do
     for day  in   $(seq 1  31)
     do
              echo "RETRIEVING  month $month day $day"
              # retrieves pressure level files
              $MDL ${PDL}/get_era5_cds.py  --3d   -y $year -m $month  -d $day --dir $outdir  -g  --area $area
              # retrieves surface data files with all variables
              $MDL ${PDL}/get_era5_cds.py  --2da  -y $year -m $month  -d $day --dir $outdir  -g  --area $area
     done
done

# use the cfg file created for the conversion.
mv new_era52arl.cfg era52arl.cfg

#-----------------------------------------
# convert data to ARL format

# In practice you may want to run the following 
# in a separate script, after you have confirmed that
# all the data downloaded properly.
#-----------------------------------------

MDL=$HOME/hysplit/data2arl/era52arl/
monthname='Jan'
for month in '01'
do
     for day  in  {01..31}
     do
       echo '---------------------------------------------------------------------------------'
       echo $MDL/era52arl -i${outdir}ERA5_$year.${monthname}${day}.3dplgrib -a${outdir}ERA5_${year}.${monthname}${day}.2dpl.all.grib
       $MDL/era52arl -i${outdir}ERA5_$year.${monthname}${day}.3dplgrib -a${outdir}ERA5_${year}.${monthname}${day}.2dpl.all.grib
       mv DATA.ARL ERA5_${year}${month}${day}.ARL
       echo 'DONE ---------------------------------------------------------------------------------'
     done
done

