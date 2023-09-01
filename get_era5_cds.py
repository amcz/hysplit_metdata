# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#from ecmwfapi import ECMWFDataServer
import cdsapi
#from ecmwfapi import ECMWFDataServer
#from calendar import monthrange
#from calendar import month_name
from optparse import OptionParser
import sys
import datetime
import string
import era5utils

"""
MAIN PROGRAM: retrieves ecmwf ERA5 dataset using the CDS (Copernicus Data Service) API.
PRGRMMR: Alice Crawford    ORG: CICS-MD  DATE:2017-10-16

PYTHON 3.x

ABSTRACT: Retrieves ECMWF ERA5 grib files for use by HYSPLIT.

Must have cdsapi installed and an account with CDS. 
See https://cds.climate.copernicus.due/api-how-to
Your api key must be stored in the $HOME/.cdsapirc file.


grib files can be input into the era52arl fortran utility program to create a meteorological file that can be used
as input into HYSPLIT. 

This python program aids in retrieving  meteorological variables from the ERA5 dataset which HYSPLIT needs.

for command line options run with --help

writes a file called get_era5_message.txt 
writes a file called new_era52arl.cfg

if the -g option is set will write a shell script to run the era52arl utility.
            
9/10/2018 converted to python3 from python 2.7
"""


##Parse command line arguments and set defaults#####
parser = OptionParser()
parser.add_option("-y", type="int" , dest="year", default=2000,
                  help="{2000} Year to retrieve. type integer.")
parser.add_option("-m", type="int" , dest="month" , default=1,
                  help = "{1} Month to retrieve. type integer")
parser.add_option("-d", type="int" , dest="day" , default='1',
                  help = "Default is to retrieve one day split into four files. ")
parser.add_option("-f", type="int" , dest="placeholder" , default='1',
                  help = "Does not do anything.")
parser.add_option("--dir", type="string" , dest="dir" , default='./',
                  help = "{./} Directory where files are to be stored. ")
parser.add_option("-o", type="string" , dest="fname" , default='',
                  help = "Output filename stem. 3D.grib and 2D.grib will be added on. \
                  The default is to call it ERA5_YYYY.MMM where MMM is the three letter abbreviation for month. \
                  If a day range is specified then the default will be DATASET_YYYY.MMM.dd-dd.")
parser.add_option("--3d", action="store_true" , dest="retrieve3d" , default=False,
                  help = "If set then it retrieve 3d data. If none of the following are set:\
                          --3d, --2d, --2da, --2df, then will act as though --3d and --2da are set.")
parser.add_option("--2d", action="store_true" , dest="retrieve2d" , default=False, 
                  help = "If set then it will retrieve 2d analyses data." \
                  )
parser.add_option("--2da", action="store_true" , dest="retrieve2da" , default=False, 
                  help = "If set then it will retrieve all 2d data (forecast and analyses) in one file." \
                  )
parser.add_option("--2df", action="store_true" , dest="retrieve2df" , default=False, 
                  help = "If set then it will retrieve 2d forecast data separately." )
parser.add_option("-s", type="string" , dest="stream" , default='oper',
                  help = "default is oper which retrieves deterministic analyses. \
                          enda will retrieve ensemble.")
parser.add_option("-g", action="store_true" , dest="grib2arl" , default= False, 
                  help = "If set then will append lines to a shell script for converting the files to arl format.") 
parser.add_option("-l", type="int" , dest="toplevel" , default= 1, 
                  help = "Set top pressure level to be retrieved. Default is to retrieve all levels. ")
#currently will only retrieve pressure levels. no converter available for model levels yet.
#parser.add_option("-t", type="string" , dest="leveltype" , default= "pl", 
#                  help = "default is pressure levels (pl) which will retrieve grib1 file \
#                          Can also choose model levels (ml). There are 137 model levels. This will retrieve grib2 file.") 
parser.add_option("-t", type="string" , dest="leveltype" , default= "pl" ,
                  help='default is pl retrieve pressure levels. Can also use ml\
                        for model levels. Converter for model levels is\
                        currently not available.')
parser.add_option("--area", type="string" , dest="area" , default= "90/-180/-90/180", 
                  help = "choose the area to extract. Format is North/West/South/East \
                          North/West gives the upper left corner of the bounding box. \
                          South/East gives the lower right corner of the bounding box. \
                          Southern latitudes and western longiutdes are given negative numbers.") 
parser.add_option("--check", action="store_false" , dest="run" , default=True,
                  help = "If set then simply echo command. Do not retrieve\
                          data. Will create the cfg file." )
parser.add_option("--extra", action="store_true" , dest="extra" , default=False, 
                  help = "download UMOF, VMOF, TCLD, RGHS, DP2M into the \
                          surface file." )
parser.add_option("--grid", type="string" , dest="grid" , default= "0.25/0.25",
                  help="set horizontal grid resolution to be retrieved. The\
                        default is 0.25/0.25 which is highest possible\
                        resolution"  )
parser.add_option("--split", type="int" , dest="getfullday" , default=1, 
                  help = "Set number of time periods to split day into.  \
                          Default is 1 to retrieve full day in 1 file. \
                          Possible values are 1, 2, 4, and 8. \
                          8 will split the files into 3 hour increments, T1 to T8.\
                          4 will split the files into 6 hour increments, T1 to T4.\
                          2 will split the files into 12 hour increments, T1 to T2.\
                          If a non-valid value is entered, then 8 will be used.\
                          The reason for this is that full day grib files for\
                          the global or large area datasets may \
                          be too large to download." )
parser.add_option("-q", type="int" , dest="timeperiod" , default=-99, 
                  help = "Used in conjuction with --split to retrieve only one\
                          of the 3 hour time periods. \
                          Values 1-8 are valid.")
parser.add_option("--test", action="store_true" , dest="test" , default=False, 
                  help = "run tests. \
                          " )


#If no retrieval options are set then retrieve 2d data and 2d data in one file.
(options, args) = parser.parse_args()
if not(options.retrieve3d) and not(options.retrieve2d) and not(options.retrieve2da) and not(options.retrieve2df):
   options.retrieve3d=True
   options.retrieve2da=True
if options.test:
   # do not do any retrievals.
   #options.retrieve3d=False
   #options.retrieve2d=False
   #options.retrieve2da=False
   #options.retrieve2df=False
   a=1

means=False #if true retrieve mean fluxes instead of accumulated when possible.
            #some means are not available every hour so set to False.


#mid = open('recmwf.txt','w')
mfilename = 'get_era5_message.txt'

year = options.year
month = options.month
day = options.day
#monthstr = '%0*d' % (2, month)
#daystr = '%0*d' % (2, day)
dataset = 'era5'
area = options.area
grid=options.grid
startdate = datetime.datetime(year, month, day, 0)
#tpptstart = startdate - datetime.timedelta(hours=24)  #need to retrieve forecast variables from previous day.

#tppt_datestr = tpptstart.strftime('%Y-%m-%d') 
datestr = startdate.strftime('%Y-%m-%d') 
yearstr = startdate.strftime('%Y')
monthstr = startdate.strftime('%m')
daystr = startdate.strftime('%d')

###"137 hybrid sigma/pressure (model) levels in the vertical with the top level at 0.01hPa. Atmospheric data are
###available on these levels and they are also interpolated to 37 pressure, 16 potential temperature and 1 potential vorticity level(s).
##model level fields are in grib2. All other fields (including pressure levels) are in grib1 format.
#if options.leveltype == "pl":
levtype = "pl"
if options.leveltype == "ml":
    levtype = "ml"

stream = options.stream
if stream not in ['oper', 'enda']:
   print("Warning: stream" + options.stream + " is not supported. Only oper and enda streams supported")
   sys.exit()
if stream == 'enda':
   estr='enda'
   wtype="ensemble_members" 
   print("retrieving ensemble")
   precip='TPP3'  #for ensemble precip accumulated over 3 hours.
   levtype='enda'
else:
   estr=''
   wtype="reanalysis" 
   precip='TPP1'  #normally precip accumulated over 1 hour.


##Pick pressure levels to retrieve. ################################################################
##Can only pick a top level 
if levtype == "pl" or levtype=='enda':
    levs = list(range(750,1025,25)) + list(range(300,750,50)) + list(range(100,275,25)) + [1,2,3,5,7,10,20,30,50,70]
    levs = sorted(levs, reverse=True)
    if options.toplevel != 1: 
       levs = [y for y in levs if y>=options.toplevel]
       levs = sorted(levs, reverse=True)
       levstr = str(levs[0])
    else:
       levstr = ''
    for lv in levs[1:]:
       levstr += '/' + str(lv)  
#Retrieve all model levels. Modify this if need only certain model levels.
#May need level one since it has geopotential.
elif levtype=='ml':
    ##pakset header will not work with 137 levels right now.
    ##use every other level.
    #step=2
    step=1
    ##level 40 is about 24.5 km. Level 137 is 10 m
    ##level 49 is about 20 km.
    ##level 67 is about 14 km.
    ##level 80 is about 10 km.
    ##level 60 is about 16km or 100mb.
    #levstart = 60
    levstart = 1
    ##HYSPLIT cannot currently handle more than 74 levels due to
    ##limitations in the length of the header file.   
    #levstart = 64   
    
    levstr = "/".join(map(str, list(range(levstart,138,1))))
    #levstr = "/".join(map(str, list(range(1,137,1))))
    levs = list(range(levstart,138,1))
    cfglevs = list(range(levstart,138,step))
    # need to be written from bottom level (137) to top for era52arl.cfg
    cfglevs = cfglevs[::-1]
else:
    levs = []
##########################################################################################



options.dir = options.dir.replace('\"', '')
if options.dir[-1] != '/':
   options.dir += '/'

if options.fname =='':
   dstr = startdate.strftime('%Y.%b%d')
   dstr2 = startdate.strftime('%Y%b')
   f3d = dataset.upper() + '_' + dstr +  '.3d'
   f2d = dataset.upper() + '_' + dstr +  '.2d'
   ftppt = dataset.upper() + '_' + dstr +   '.2df'
else:    
   f3d = options.dir + options.fname  + '.3d'
   f2d = options.dir + options.fname  + '.2d'
   ftppt = options.dir + options.fname  + '.2df'
   
if levtype == 'ml':
   f3d += '.ml'
 
file3d = options.dir + f3d
file2d = options.dir + f2d
filetppt = options.dir + ftppt

#server = ECMWFDataServer(verbose=False)
server=cdsapi.Client()

##wtype = "4v"   ##4D variational analysis is available as well as analysis.

#wtype="an" 
#wtype="reanalysis" 

if stream == 'oper':
##need to break each day into four time periods to keep 3d grib files at around 1.6 GB
    #wtime1 =  "00:00/01:00/02:00/03:00/04:00/05:00"
    #wtime2 =  "06:00/07:00/08:00/09:00/10:00/11:00"
    #wtime3 =  "12:00/13:00/14:00/15:00/16:00/17:00"
    #wtime4 =  "18:00/19:00/20:00/21:00/22:00/23:00"

    wtime1 =  "00:00/01:00/02:00"
    wtime2 =  "03:00/04:00/05:00"
    wtime3 =  "06:00/07:00/08:00"
    wtime4 =  "09:00/10:00/11:00"
    wtime5 =  "12:00/13:00/14:00"
    wtime6 =  "15:00/16:00/17:00"
    wtime7 =  "18:00/19:00/20:00"
    wtime8 =  "21:00/22:00/23:00"
    wtimelist = [wtime1, wtime2, wtime3, wtime4,wtime5,wtime6,wtime7,wtime8]

    if options.getfullday==1:
       wtimelist = [str.join('/', wtimelist)]

    elif options.getfullday==4:
       wt1 = str.join('/', [wtime1,wtime2])  
       wt2 = str.join('/', [wtime3,wtime4])  
       wt3 = str.join('/', [wtime5,wtime6])  
       wt4 = str.join('/', [wtime7,wtime8])  
       wtimelist = [wt1,wt2, wt3, wt4]

    elif options.getfullday==2:
       wt1 = str.join('/', [wtime1,wtime2,wtime3,wtime4])  
       wt2 = str.join('/', [wtime5,wtime6,wtime7,wtime8])  
       wtimelist = [wt1,wt2]

    elif options.getfullday==24:
       wtimelist = []
       for iii in range(0,24):
           wtimelist.append(str(iii).zfill(2) + ':00')
    else:
       wtimelist = [wtime1, wtime2, wtime3, wtime4,wtime5,wtime6,wtime7,wtime8]

    #wtimelist = [wtime1]
#ensemble data only availabe every 3 hours.
elif stream == 'enda':
    wtime1 =  "00:00/03:00/06:00/09:00/12:00/15:00/18:00/21:00"
    wtimelist = [wtime1]

#print(options.getfullday)
#print(wtimelist)

#___________________This block for setting time and step for surface fields that are only 
#                   available as forecast.
##This block not needed with CDS because retrieval time is for valid date.
##The api will calculate what forecast time and step are needed.

###In order to make the forecast field files have matching time periods
###use the following times and steps.
###start at 18  on the previous day with step of 6 through 12 to get hours 0 through 05.
###hour 06 with step of 0 to 5 to get hours 6 through 11
###hour 06 with step of 6 to 11 to get hours 12 through 17
###hour 18 with step 0 through 5 to get hours 18 through 23

###NOTE - accumulated fields are 0 for step of 0. So cannot use step0.
##Always retrieve full day for the forecast fields.
#if options.getfullday:
#if stream == 'oper':
#    ptimelist = ["18:00:00/06:00:00"]
#    pstep = ["/".join(map(str,list(range(1,13))))]
#    pstart=[tppt_datestr+ '/' + datestr]

#elif stream == 'enda':  #ensemble output.
    ##use steps 3,6,9, 12.
    ##time of 18 step 3 gives forecast at 21
    ##time of 18 step 6 gives forecast at 00
    ##time of 18 step 9 gives forecast at 03
    ##time of 18 step 12 gives forecast at 06
    ##time of 06 step 3 gives forecast at 09
    ##time of 06 step 6 gives forecast at 12
    ##time of 06 step 9 gives forecast at 15
    ##time of 06 step 12 gives forecast at 18

#    ptimelist = ["18:00:00/06:00:00"]
#    pstep = ["/".join(map(str,list(range(3,15,3))))]
#    pstart=[tppt_datestr+ '/' + datestr]


#grid: 0.3/0.3: "For era5 data, the point interval on the native Gaussian grid is about 0.3 degrees. 
#You should set the horizontal resolution no higher than 0.3x0.3 degrees (about 30 km), approximating the irregular grid spacing
#on the native Gaussian grid.

f3list =[]
f2list =[]
f2flist = []

iii=1
###SPLIT retrieval into four time periods so files will be smaller.
for wtime in wtimelist:
    if options.getfullday!=1 and options.timeperiod!=-99 and options.timeperiod!=iii: 
       print('Skipping time period T', str(iii))
       iii+=1
       continue
    print("Retrieve for: " , datestr, wtime)
    #print wtime
    if options.getfullday==1:
        tstr =  '.grib'
    else:
        tstr = '.T' + str(iii) + '.grib'
    timelist = wtime.split('/')
    ###need to set the grid parameter otherwise will not be on regular grid and converter will not handle.
    ####retrieving 3d fields
    if levtype=='pl':
       param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'RELH','HGTS' ]
       rstr = 'reanalysis-era5-pressure-levels'
       estr='pl'
    elif levtype=='ml':
       param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'SPHU', 'HGTS','LNSP']
       rstr = 'reanalysis-era5-complete'
       estr='ml'
    elif levtype=='enda':
       param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'RELH' , 'HGTS' ]
       rstr = 'reanalysis-era5-complete'
       estr='enda'
    f3list.append(file3d+ estr + tstr)
    if options.retrieve3d:
        print( 'RETRIEVING 3d {} {}'.format(levtype, ' '.join(param3d)))
        levs = list(map(str, levs))
        print('Retrieve levels ' , levs)
        paramstr = era5utils.createparamstr(param3d, means=means, levtype=levtype)
        with open(mfilename, 'w') as mid: 
            mid.write('retrieving 3d data \n')
            mid.write(paramstr + '\n')
            mid.write('time ' + wtime + '\n')
            mid.write('type ' + wtype + '\n')
            mid.write('date ' + datestr + '\n')
            mid.write('-------------------\n')
        if options.run and levtype=='pl':
            server.retrieve(rstr,
                    {
                    'variable'      :  paramstr.split('/'),
                    'pressure_level':  levs,
                    'product_type'  :  wtype,
                    'year'          : yearstr,
                    'month'         : monthstr,
                    'day'           : daystr,
                    'time'          : timelist,
                    'grid'    : grid,
                    'area'    : area,
                    'format'        : 'grib'
                    },
                     file3d + estr + tstr)
        if options.run and levtype=='ml':
            rstr = 'reanalysis-era5-complete'
            #paramstr='129/130/131/132/135'
            print(paramstr)
            print(datestr)
            #wtime = '09:00:00/21:00:00'
            print(wtime)
            levs = '/'.join(levs) 
            print(levs)
            print('---------------------')
            server.retrieve(rstr,
                    {
                    'class'    : 'ea',
                    'date'     :  datestr,
                    'levtype'  : 'ml',    
                    'expver'   : '1',
                    'area'     : area,
                    'grid'    : grid,
                    'levelist' :  levs,
                    'stream'   : 'oper',
                    'type'     : 'an',
                    'param'    :  paramstr,
                    'time'     :  wtime,
                    'step'     : '0',
                    },
                     'out.grib')

            #server.retrieve('reanalysis-era5-complete', {
            #    'class': 'ea',
            #    'date': '2022-08-01',
            #    'expver': '1',
            #    'levelist': '1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80/81/82/83/84/85/86/87/88/89/90/91/92/93/94/95/96/97/98/99/100/101/102/103/104/105/106/107/108/109/110/111/112/113/114/115/116/117/118/119/120/121/122/123/124/125/126/127/128/129/130/131/132/133/134/135/136/137',
            #    'levtype': 'ml',
            #    'param': paramstr,
            #    'step': '0',
            #    'stream': 'oper',
            #    'time': wtime,
            #    'type': 'an',
            #}, 'output')















        if options.run and levtype=='enda':
            paramstr = era5utils.createparamstr(param3d, means=means, levtype='enda')
            server.retrieve(rstr,
                    {
                    'class'    : 'ea',
                    'expver'   : 'l',
                    'dataset'  : 'era5',
                    'stream'   : 'enda',
                    'type'     : 'an',
                    'levtype'  : 'pl',    #TODO is there ensemble data on ml?
                    'param'    : paramstr,
                    'origin'   : "all",
                    'levelist' :  levs,
                    'date'     : datestr,
                    'time'     : wtime,
                    'grid'     : grid,
                    'area'     : area,
                    'format'   : 'grib',
                    'number'   : '0/1/2/3/4/5/6/7/8/9'
                    },
                     file3d + estr + tstr)
                 
                 
    ##The surface variables can be retrieved in the same file with CDS.
    ##This was not the case with the ecmwf api.
    ##For CDSAPI the year month day and time are the validityDate and validityTime.
    # moved USTR to the extra variables. There is something a bit odd about it. 
    # seems to undermix - too small in the daytime.
    pextra = ['UMOF','VMOF','DP2M','TCLD','USTR']
    pextraf = ['RGHS']
    #param2da = ['T02M', 'V10M', 'U10M', 'PRSS','PBLH', 'CAPE', 'SHGT']
    # need 'SHGT' for model levels.
    param2da = ['T02M', 'V10M', 'U10M', 'PRSS','PBLH', 'CAPE','SHGT','MSLP']
    param2df = [precip, 'SHTF' , 'DSWF', 'LTHF']
   
    if options.extra:
       param2da.extend(pextra)
       param2df.extend(pextraf)
    if options.retrieve2da: 
       param2da.extend(param2df)
       estr += '.all'
    ####retrieving 2d fields
    f2list.append(file2d+estr+tstr)
    if options.retrieve2d or options.retrieve2da:
        print( 'RETRIEVING 2d ' + ' '.join(param2da) )
        ##levtype for 2d is always pl for creating paramstr purposes.
        ##levtype for 2d is always pl for creating paramstr purposes.
        #paramstr = createparamstr(param2da, means=means, levtype=levtype)
        if options.run and levtype!='enda':
            paramstr = era5utils.createparamstr(param2da, means=means, levtype='pl')
            print('Retrieving surface data')
            server.retrieve('reanalysis-era5-single-levels',
                        {
                         'product_type' : wtype,
                         'variable' : paramstr.split('/'),
                         'year'     : yearstr,
                         'month'    : monthstr,
                         'day'      : daystr,
                         'time'     : timelist,
                         'area'     : area,
                         'format'   : 'grib',
                         'grid'    :grid 
                         },
                          file2d + estr + tstr)
        if options.run and levtype=='enda':
            print( 'RETRIEVING 2d ' + ' '.join(param2da) )
            ### TESTING HERE
            #paramstr =\
            #         createparamstr(['LTHF','SHTF','TPP3'],means=True,levtype='enda',instant=False)  
            paramstr = era5utils.createparamstr(param2da, means=False, instant=True,levtype='enda')
            print('Retrieving ensemble. heat fluxes and precip not available.')
            print( paramstr )
            rstr = 'reanalysis-era5-complete'
            server.retrieve(rstr,
                    {
                    'class'    : 'ea',
                    'expver'   : 'l',
                    'dataset'  : 'era5',
                    'stream'   : 'enda',
                    'type'     : 'an',
                    'levtype'  : 'sfc',    
                    'param'    : paramstr,
                    'origin'   : "all",
                    'levelist' :  levs,
                    'date'     : datestr,
                    'time'     : wtime,
                    'grid'     : grid,
                    'area'     : area,
                    'format'   : 'grib',
                    'number'   : '0/1/2/3/4/5/6/7/8/9'
                    },
                     file2d + estr + tstr)
        with open(mfilename, 'a') as mid: 
            mid.write('retrieving 2d data \n')
            mid.write(paramstr + '\n')
            mid.write('time ' + wtime + '\n')
            mid.write('type ' + wtype + '\n')
            mid.write('date ' + datestr + '\n')
            mid.write('-------------------\n')
                 
    if options.retrieve2df:
        paramstr = era5utils.createparamstr(param2df, means=means,levtype='pl')
        if options.run:
            server.retrieve('reanalysis-era5-single-levels',
                        {
                         'product_type' : wtype,
                         'variable' : paramstr,
                         'year'     : yearstr,
                         'month'    : monthstr,
                         'day'      : daystr,
                         'time'     : timelist,
                         'area'     : area,
                         'format'   : 'grib',
                         'grid'    : grid
                         },
                          filetppt + estr + tstr)

    shfiles = list(zip(f3list, f2list)) 
    if options.grib2arl:
       sname = options.dir + dstr2 + '_ecm2arl.sh'
       era5utils.grib2arlscript(sname, shfiles, startdate, 'T'+str(iii)) 
    iii+=1


#param2da.extend(param2df)
#write a cfg file for the converter.
tm=1
if stream=='enda': tm=3
if options.retrieve2df and not options.retrieve2da:
   param2da.extend(param2df)
if levtype=='ml': levs=cfglevs
era5utils.write_cfg(param3d, param2da, levs, tm=tm, levtype=levtype)

#Notes on the server.retrieve function.
#Seperate lists with a /
#indicate a range by value/to/value/by/step
#type : an = analysis , fc = forecast
#levtype: pl, ml, sfc, pt, pv  (pressure level, model level, mean sea level, potential temperature, potential vorticity)

#An area and grid keyword are available 
#Area : four values : North West South East
#Grid : two values  : West-East   North-South increments
#could use 'format' : 'netcdf' if want netcdf files.

