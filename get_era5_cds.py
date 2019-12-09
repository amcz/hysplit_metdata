# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#from ecmwfapi import ECMWFDataServer
import cdsapi
from calendar import monthrange
from calendar import month_name
from optparse import OptionParser
import sys
import datetime
import string

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

def getvars(means=False, tm=1, levtype='pl'):
    instant=True
    if tm==1: amult = '0.00028'  #1/3600 s
    if tm==3: amult = '9.26e-5'
    sname={}
    #3d fields. pressure levels. Instantaneous.
    #REQUIRED
    ##Last two numbers in list are (parameterCategory and parameterNumber)
    ##In the grib2 file for the model levels, these are used to identify the
    ##variable.
    ##For the pressure levels the indicatorOfParameter (second in the list) is used.
    sname['TEMP'] = ['t', '130', '1.0', '130.128', 'temperature','0','0']    #units K
    sname['UWND'] = ["u", '131', '1.0', '131.128', 'u_component_of_wind','2','2']    #units m/s
    sname['VWND'] = ["v", '132', '1.0', '132.128', 'v_component_of_wind','2','3']    #units m/s
    sname['WWND'] = ["w", '135', '0.01','135.128','vertical_velocity', '2','8']   #units Pa/s. convert to hPa/s for HYSPLIT
    sname['RELH'] = ["r", '157', '1.0', '157.128','relative_humidity']    #units %
    sname['HGTS'] = ["z", '129', '0.102','129.128','geopotential','3','4']  #units m^2 / s^2. Divide by 9.8m/s^2 to get meters.
    #sname['SPHU']= "q"     #units kg / kg category 1, number 0. multiplier is 1   #specific humidity. redundant since have RELH

    #3d fields. model levels
    sname['SPHU'] = ['q', '133','1.0','133.128','specific_humidity', '1', '0'] #units kg/kg
    sname['ZWND'] = ['etadot', '77','1.0','133.128', '-1', '-1'] #eta-coordinate vertical velocity units s^-1
    sname['LNSP'] = ['lnsp', '152','1.0','152.128', '', '3', '25'] #log pressure

    #2D/surface analyses fields. 
    #REQUIRED
    sname['T02M'] = ['2t', '167', '1.0', '167.128','2m_temperature']  #units K         #Analysis (needed) ERA5
    sname['U10M'] = ['10u','165', '1.0', '165.128','10m_u_component_of_wind']  #units m/s       #Analysis (needed) ERA5
    sname['V10M'] = ['10v','166', '1.0', '166.128','10m_v_component_of_wind']  #units m/s       #Analysis (needed) ERA5
    #OPTIONAL
    sname['PRSS'] = ['sp' ,'134', '0.01','134.128', 'surface_pressure'] #Instantaneous. Units Pa        #multiplier of 0.01 for hPa.
    sname['TCLD'] = ['tcc','164', '1.0', '164.128','total_cloud_cover']  #total cloud cover 0-1  
 
    #2m dew point temperature  : Units K : level_indicator 1 , gds_grid_type 0
    sname['DP2M'] = ['2d', '168', '1.0','168.128','2m_dewpoint_temperature']   
    sname['SHGT'] = ["z" , '129', '0.102','129.128','geopotential'] #geopotential height  
    sname['CAPE'] = ["cape" , '59', '1.0','59.128',  #Instantaneous. convective potential energy : units  J/kg 
                     'convective_available_potential_energy']
    sname['PBLH'] = ["blh" , '159', '1.0','159.128','boundary_layer_height'] #boundary layer height : units m 
    #Turbulent surface stresses are instantaneous.
    #These are same as Momentum fluxes.
    #Can use these in place of USTR
    sname['UMOF'] = ['iews','229', '1.0','229',   #units of N/m2  eastward turbulent surface stress     
                     'instantaneous_eastward_turbulent_surface_stress']
    sname['VMOF'] = ['inss','230', '1.0','230',  #units of N/m2  northward turbulent surface stress     
                     'instantaneous_northward_turbulent_surface_stress']

    sname['XXXX'] = ['boundary_layer_dissipation']
    #2D/surface forecast fields. 
    #OPTIONAL
    sname['TPP1'] = ['tp','228','1.0','228.128','total_precipitation']       #Accumulated precipitation. units of m. multiplier is 1.        
    sname['TPP3'] = ['tp','228','1.0','228.128','total_precipitation']       #Accumulated precipitation. units of m. multiplier is 1.        
    sname['RGHS'] = ['fsr','244','1.0', "244.128",'forecast_surface_roughness']   #forecast surface roughnes : units m

    #It looks like the means are not output every hour so do not use them.
    #if means:
    #    sname['SHTF'] = ['msshf','146', '1.0', '33.235'] #units W/m^2 (surface sensible heat flux)      
    #    sname['LTHF'] = ['mslhf','34', '1.0', '34.235']  #latent heat flux. same as sshf            
    #Also having trouble getting accumulated sshf to convert.
    #sname['SHTF'] = ['sshf','146', amult,'146.128', 'surface_sensible_heat_flux'] #units J/m^2 (surface sensible heat flux) (divide by 3600 to get W/m^2)     
    sname['LTHF'] = ['slhf','147', amult,'147.128','surface_latent_heat_flux'] #same as sshf            
    if instant:
        #instaneous fluxes may be more desireable since use instanteous winds.
        sname['SHTF'] =\
                      ['ishf','231','1.0','231.128',
                       'instantaneous_surface_sensible_heat_flux'] #instantaneous SHTF. units W/m^2.

    sname['DSWF'] = ['ssrd','169', amult,'169.128',
                     'surface_solar_radiation_downwards']  #Accumulated. units J/m^2         
    sname['USTR'] = ['zust','3', '1.0','3.228','friction_velocity']      #units of m/s (multiplier should be 1)      


    ###"The accumulations in the short forecasts (from 06 and 18 UTC) of ERA5 are treated differently 
    ###compared with those in ERA-INTERIM (where they
    ###were from the beginning of the forecast to the forecast step). 
    ###In the short forecasts of ERA5, the accumulations are since the previous post processing (archiving)
    ###so for: HRES - accumulations are in the hour ending at the forecast step.
    ###mean rate parameters in ERA5 are similar to accumulations except that the quantities 
    ###are averaged instead of accumulated over the period so the units
    ### include "per second"
    ### step for forecast are 1 through 18
    return sname

def write_cfg(tparamlist, dparamlist, levs, tm=1, levtype='pl', cfgname = 'new_era52arl.cfg', means=False):
    """writes a .cfg file which is used by the fortran conversion program era52arl to
       read the grib files and convert them into a meteorological file that HYSPLTI can use.
    """
    #Key is HYSPLIT name
    #value is list of [ERA5 short name, ERA5 indicatorOfParamter, unit conversion]
    #unit conversion converts from units of the ERA5 to units that HYSPLIT expects.
    #the short name and indicatorOfParameter can be found by doing a grib_dump
    #or tables in the ERA5 documentation - 
    #https://software.ecmwf.int/wiki/display/CKB/ERA5+data+documentation#ERA5datadocumentaion-Paramterlistings
    print(dparamlist)
    if levtype=='pl' or levtype=='enda':
       aaa=1
       bbb=1
    elif levtype=='ml':
       aaa=5
       bbb=6
       
    if levtype == 'ml':
        cfgname = levtype + cfgname
    sname=getvars(means=means, tm=tm, levtype=levtype)

    numatm = str(len(tparamlist))
    atmgrb = ''
    atmcat = ''
    atmnum = ''
    atmcnv = ''
    atmarl = ''
    for atm in tparamlist:
        atmgrb += "'" + sname[atm][0] + "', " 
        atmcat +=  sname[atm][aaa] + ", " 
        atmnum +=  sname[atm][bbb] + ", " 
        atmcnv +=  sname[atm][2] + ", " 
        atmarl += "'" + atm + "', "

    numsfc = str(len(dparamlist))
    sfcgrb = ''
    sfccat = ''
    sfccnv = ''
    sfcarl = ''
    for sfc in dparamlist:
        sfcgrb += "'" + sname[sfc][0] + "', " 
        sfccat +=  sname[sfc][1] + ", " 
        sfccnv +=  sname[sfc][2] + ", " 
        sfcarl += "'" + sfc + "', " 

    numlev = str(len(levs))
    levstr = str.join(', ', list(map(str, levs)))

    with open(cfgname, "w") as fid:
         #the -2 removes the last space and comma from the string.
         fid.write('&SETUP\n') 
         fid.write('numatm = ' + numatm +  ',\n') 
         fid.write('atmgrb = ' + atmgrb[:-2] + '\n')
         fid.write('atmcat = '  + atmcat[:-2] + '\n')
         fid.write('atmnum = ' + atmnum[:-2] + '\n')
         fid.write('atmcnv = ' + atmcnv[:-2] + '\n')
         fid.write('atmarl = ' + atmarl[:-2] + '\n')

         fid.write('numsfc = ' + numsfc +  ',\n') 
         fid.write('sfcgrb = ' + sfcgrb[:-2] + '\n')
         fid.write('sfccat = ' + sfccat[:-2] + '\n')
         fid.write('sfcnum = ' + sfccat[:-2] + '\n')
         fid.write('sfccnv = ' + sfccnv[:-2] + '\n')
         fid.write('sfcarl = ' + sfcarl[:-2] + '\n')
         fid.write('numlev = ' + numlev  + '\n')
         fid.write('plev = ' + levstr.strip()  + '\n')
         fid.write('/\n')


def createparamstr(paramlist, means=True, levtype='pl'):
    """contains a dictionary of codes for the parameters to be retrieved. Input a list of string descriptors of the
       parameters. Output is a string of codes which can be used in the server.retrieve() function.
       4 letter codes used for dictionary keys correspond to codes used by fortran ecmwf2arl converter. 
    """
    param=getvars(means=means) 
    paramstr = ''
    i=0
    knum=4
    if levtype=='pl': knum=4
    if levtype=='ml': knum=0
    if levtype=='enda': knum=3
    for key in paramlist:
        if key in list(param.keys()):
            if i == 0:
               paramstr += param[key][knum] 
            else:
               paramstr += '/' + param[key][knum] 
            i+=1
        else:
            print("No code for " , key , " available.") 
    return paramstr

def grib2arlscript(scriptname, shfiles, day, tstr, hname='ERA5'):
   """writes a line in a shell script to run era51arl. $MDL is the location of the era52arl program.
   """
   fid = open(scriptname , 'a')
   checkens = ['e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9']
   for files in shfiles:
       inputstr = []
       inputstr.append('${MDL}/era52arl')
       inputstr.append('-i' + files[0])
       inputstr.append('-a' + files[1])         #analysis file with 2d fields
       try:
          inputstr.append('-f' + files[2]) #file with forecast fields.
       except:
          pass
       for arg in inputstr:
           fid.write(arg + ' ')
       fid.write('\n')
       tempname = tstr + '.ARL'
       hname2 = hname
       for ens in checkens:
           if ens in files[0]:
              hname2 = hname + '_' + ens  
       fname = hname2 + day.strftime("_%Y%m%d.ARL")
       fid.write('mv DATA.ARL ' +  tempname + '\n')
       fid.write('mv ERA52ARL.MESSAGE MESSAGE.'  +fname + '.' + tstr + ' \n')
       if tstr=='T1':
          fid.write('cat ' + tempname + ' > ' +fname + '\n')
       else:
          fid.write('cat ' + tempname + ' >> ' +fname + '\n')
       fid.write('rm ' + tempname + '\n')
       fid.write('\n')

   fid.close()

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
parser.add_option("--check", action="store_false" , dest="run" , default='true', 
                  help = "If set then simply echo command. Do not retrieve\
                          data. Will create the cfg file." )
parser.add_option("--extra", action="store_true" , dest="extra" , default='False', 
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
parser.add_option("--test", action="store_true" , dest="test" , default='False', 
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
    levstart = 60
    ##HYSPLIT cannot currently handle more than 74 levels due to
    ##limitations in the length of the header file.   
    levstart = 64   
    
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
       param3d = ['TEMP' , 'UWND', 'VWND' , 'WWND' , 'RELH' , 'HGTS' ]
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
        print( 'RETRIEVING 3d ' + levtype + ' '.join(param3d) )
        levs = list(map(str, levs))
        print('Retrieve levels ' , levs)
        paramstr = createparamstr(param3d, means=means, levtype=levtype)
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
            server.retrieve(rstr,
                    {
                    'class'    : 'ea',
                    'levtype'  : 'ml',    
                    'expver'   : 'l',
                    'stream'   : 'oper',
                    'type'     : 'an',
                    'param'    : paramstr,
                    'origin'   : "all",
                    'levelist' :  levs,
                    'date'     : datestr,
                    'time'     : wtime,
                    'grid'     : grid,
                    'area'     : area,
                    'format'   : 'grib'
                    },
                     file3d + estr + tstr)
        if options.run and levtype=='enda':
            paramstr = createparamstr(param3d, means=means, levtype='enda')
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
    param2da = ['T02M', 'V10M', 'U10M', 'PRSS','PBLH', 'CAPE']
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
            paramstr = createparamstr(param2da, means=means, levtype='pl')
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
            paramstr = createparamstr(param2da, means=means, levtype='enda')
            print('Retrieving ensemble')
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
        paramstr = createparamstr(param2df, means=means,levtype='pl')
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
       grib2arlscript(sname, shfiles, startdate, 'T'+str(iii)) 
    iii+=1


#param2da.extend(param2df)
#write a cfg file for the converter.
tm=1
if stream=='enda': tm=3
if options.retrieve2df and not options.retrieve2da:
   param2da.extend(param2df)
if levtype=='ml': levs=cfglevs
write_cfg(param3d, param2da, levs, tm=tm, levtype=levtype)

#Notes on the server.retrieve function.
#Seperate lists with a /
#indicate a range by value/to/value/by/step
#type : an = analysis , fc = forecast
#levtype: pl, ml, sfc, pt, pv  (pressure level, model level, mean sea level, potential temperature, potential vorticity)

#An area and grid keyword are available 
#Area : four values : North West South East
#Grid : two values  : West-East   North-South increments
#could use 'format' : 'netcdf' if want netcdf files.

