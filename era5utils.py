# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#from ecmwfapi import ECMWFDataServer
#from ecmwfapi import ECMWFDataServer
#from calendar import monthrange
#from calendar import month_name
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

def getvars(means=False, tm=1, levtype='pl',instant=True):

    # HYSPLIT convention is that upward sensible heat flux should be positive. 
    # Multiply by -1
    if int(tm)==1: amult = '-0.00028'  #1/3600 s
    elif int(tm)==3: amult = '-9.26e-5'
    else: 
       print('warning tm value not 1 or 3 ...... {}'.format(tm))
       amult='1'
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
    #specific humidity. redundant since have RELH
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

    #Not used.
    sname['XXXX'] = ['boundary_layer_dissipation']

    #2D/surface forecast fields. 
    #OPTIONAL
    sname['TPP1'] = ['tp','228','1.0','228.128','total_precipitation']       #Accumulated precipitation. units of m. multiplier is 1.        
    # TPP3 is for the ensemble output which is every 3 hours.
    sname['TPP3'] = ['tp','228','1.0','228.128','total_precipitation']       #Accumulated precipitation. units of m. multiplier is 1.        
    sname['RGHS'] = ['fsr','244','1.0', "244.128",'forecast_surface_roughness']   #forecast surface roughnes : units m

    #It looks like the means are not output every hour so do not use them.
    if means:
        sname['SHTF'] = ['msshf','146', '1.0', '33.235'] #units W/m^2 (surface sensible heat flux)      
        sname['LTHF'] = ['mslhf','34', '1.0', '34.235']  #latent heat flux. same as sshf            
    elif instant:
        # instaneous fluxes may be more desireable since use instanteous winds.
        sname['SHTF'] =\
                      ['ishf','231','-1.0','231.128',
                       'instantaneous_surface_sensible_heat_flux'] #instantaneous SHTF. units W/m^2.
        # no instantaneous LTHF that I can find.
        sname['LTHF'] = ['slhf','147', amult,'147.128','surface_latent_heat_flux'] #same as sshf            
    else:
    # These are currently not availalbe in enda (ensemble) stream.
    # possibly because accumulation times don't match.
        sname['SHTF'] = ['sshf','146', amult,'146.128', 'surface_sensible_heat_flux'] #units J/m^2 (surface sensible heat flux) (divide by 3600 to get W/m^2)     
    # HYSPLIT convention is that upward sensible heat flux should be positive. 
    # Multiply by -1
        sname['LTHF'] = ['slhf','147', amult,'147.128','surface_latent_heat_flux'] #same as sshf            

    sname['DSWF'] = ['ssrd','169', amult,'169.128',
                     'surface_solar_radiation_downwards']  #Accumulated. units J/m^2         
    sname['USTR'] = ['zust','3', '1.0','3.228','friction_velocity']      #units of m/s (multiplier should be 1)      


    ### The accumulations in the short forecasts (from 06 and 18 UTC) of ERA5 are treated differently 
    ### compared with those in ERA-INTERIM (where they
    ### were from the beginning of the forecast to the forecast step). 
    ### In the short forecasts of ERA5, the accumulations are since the previous post processing (archiving)
    ### so for: HRES - accumulations are in the hour ending at the forecast step.
    ### mean rate parameters in ERA5 are similar to accumulations except that the quantities 
    ### are averaged instead of accumulated over the period so the units
    ### include "per second"
    ### step for forecast are 1 through 18
    return sname


def model_levels_default():
    # Currently HYSPLIT 

    levs = list(range(137,25,-1))
    # 25 or 24 could be used for 6hPa
    levs.append(24) # 6hPa
    levs.append(23) # 5hPa
    levs.append(22) # 4hPa
    levs.append(20) # 3hPa
    levs.append(17) # 2hPa
    levs.append(14) # 1hPa
    return levs


def write_cfg(tparamlist, dparamlist, levs, tm=1, levtype='pl', cfgname = 'new_era52arl.cfg', means=False):
    """writes a .cfg file which is used by the fortran conversion program era52arl to
       read the grib files and convert them into a meteorological file that HYSPLTI can use.
    """
    # Key is HYSPLIT name
    # value is list of [ERA5 short name, ERA5 indicatorOfParamter, unit conversion]
    # unit conversion converts from units of the ERA5 to units that HYSPLIT expects.
    # the short name and indicatorOfParameter can be found by doing a grib_dump
    # or tables in the ERA5 documentation - 
    # https://software.ecmwf.int/wiki/display/CKB/ERA5+data+documentation#ERA5datadocumentaion-Paramterlistings
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


def createparamstr(paramlist, means=False, levtype='pl',instant=True):
    """contains a dictionary of codes for the parameters to be retrieved. Input a list of string descriptors of the
       parameters. Output is a string of codes which can be used in the server.retrieve() function.
       4 letter codes used for dictionary keys correspond to codes used by fortran ecmwf2arl converter. 
    """
    param=getvars(means=means,instant=instant) 
    paramstr = ''
    i=0
    knum=4
    if levtype=='pl': knum=4
    if levtype=='ml': knum=1
    if levtype=='enda': knum=3
    for key in paramlist:
        if key in list(param.keys()):
            print('------------', param[key])
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

