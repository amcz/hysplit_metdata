#!/bin/sh
# Example bash script for retrieving ERA5 global data
# Author: Alice Crawford   Organization: NOAA/OAR/ARL 

# example for downloading and converting global ERA5 data
# on pressure levels.


# python call
MDL="python"

#Location of get_era5_cds.py
PDL=$HOME/hysplit_metdata
year=2017

#directory to write files to.
outdir='./'

# possible values are 2,4, and 8.
# determines how many files are retrieved per day.
# 8 retrieves 8 files in 3 hour increments.
# smaller files are usually retrieved faster with less download errors.
splitnum=8

for month in '01'
do
     for day  in   $(seq 1  31)
     do
       # retrieves daily surface data files with all variables
       $MDL ${PDL}/get_era5_cds.py  --2da  -y $year -m $month  -d $day --dir $outdir  -g 
       for tm in $(seq 1 $splitnum)
       do
          # retrieve pressure level data in 3 hour increments (1-8). 
          $MDL ${PDL}/get_era5_cds.py  --3d   -y $year -m $month  -d $day --dir $outdir  --split $splitnum -g -q$tm
       done
     done
done

mv new_era52arl.cfg era52arl.cfg

#-----------------------------------------
# convert data to ARL format

# In practice you may want to run the following 
# in a separate script, after you have confirmed that
# all the data downloaded properly.
#-----------------------------------------

#location of era52arl executable
MDL=$HOME/hysplit/data2arl/era52arl/
monthname='Jan'
for month in '01'
do
     for day  in   {01..31}
     do
     dailyfile=ERA5_${year}${month}${day}.ARL
     for tm in $(seq 1 $splitnum)
       do
       echo '---------------------------------------------------------------------------------'
       echo $MDL/era52arl -i${outdir}ERA5_$year.${monthname}${day}.3dpl.T${tm}.grib -a${outdir}ERA5_${year}.${monthname}${day}.2dpl.all.grib
       $MDL/era52arl -i${outdir}ERA5_$year.${monthname}${day}.3dpl.T${tm}.grib -a${outdir}ERA5_${year}.${monthname}${day}.2dpl.all.grib
       # if you want to keep separate ARL files
       mv DATA.ARL ERA5_${year}${month}${day}.T${tm}.ARL
       # if you want to create a daily ARL file.
       cat DATA.ARL >> $dailyfile 
       echo 'DONE ---------------------------------------------------------------------------------'
       done
     done
done


