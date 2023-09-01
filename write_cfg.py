# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#from ecmwfapi import ECMWFDataServer
#import cdsapi
#from ecmwfapi import ECMWFDataServer
#from calendar import monthrange
#from calendar import month_name
from optparse import OptionParser
import sys
import datetime
import string
import numpy as np
import era5utils

"""
MAIN PROGRAM: writes an cfg file for conversion utility
PRGRMMR: Alice Crawford    ORG: CICS-MD  DATE:2017-10-16

PYTHON 3.x

"""


##Parse command line arguments and set defaults#####
parser = OptionParser()
parser.add_option("-t", type="str" , dest="levtype", default='ml',
                  help="ml for model levels, pl for pressure levels")


#If no retrieval options are set then retrieve 2d data and 2d data in one file.
(options, args) = parser.parse_args()
levtype = options.levtype

param2da = ['T02M', 'V10M', 'U10M', 'PRSS','PBLH', 'CAPE','SHGT']
tm=1
print('Level type', levtype)
if levtype=='pl':
   levs = era5utils.pressure_levels()
   param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'RELH' , 'HGTS' ]
   rstr = 'reanalysis-era5-pressure-levels'
   estr='pl'
elif levtype=='ml':
   levs = era5utils.model_levels_default()
   param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'SPHU', 'HGTS','LNSP']
   rstr = 'reanalysis-era5-complete'
   estr='ml'
elif levtype=='enda':
   param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'RELH' , 'HGTS' ]
   rstr = 'reanalysis-era5-complete'
   estr='enda'

era5utils.write_cfg(param3d, param2da, levs, tm=tm, levtype=levtype)

