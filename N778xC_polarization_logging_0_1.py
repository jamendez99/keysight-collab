#!/usr/bin/env python
# coding: utf-8

## N778xC Polarization Logging

import time
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa
from datetime import datetime

rm = visa.ResourceManager()

## Connect to Polarization Synthesizer

## Setup Polarization Controller Sequence
polsyn_points = '100000'  #Integer value from 0 to 1000000
polsyn_avg = '1us' # '100us' # '1us'
polsyn_rate = '0.1MHz' # '10Hz' #'0.5MHz'
polsyn_wave = '1550e-6'
polsyn_loop = '1'

## file path
file_coarse = 'C:/Users/Public/N778xC_SOP_coarse.txt'
sop_file = open(file_coarse , 'w')
sop_file.write('Avg: {} Rate: {} {}'.format(polsyn_avg,polsyn_rate,chr(10)))
sop_file.write('time, Power (W), S1, S2, S3 {}'.format(chr(10)))
sop_file.close()

try: 

    ## Open Connection
    polsyn = rm.open_resource('TCPIP0::100.65.27.149::inst0::INSTR')
    polsyn.timeout = 10000
    ## Reset Power Meter
    polsyn.write('*RST')
    complete = polsyn.query('*OPC?')
    polsyn.write('PCON:SWIT 1') ## Polarization Controller Switch
    complete = polsyn.query('*OPC?')
    ##Query ID
    myid = polsyn.query('*IDN?').strip()
    print('N778xC ID: ' + myid)
    
    ## Non Transient file and Transient file w/ time stamps
    
    ## Setup Logging
    
    ## Wavelength
    polsyn.write(':POLarimeter:WAVelength {}'.format(polsyn_wave))
    mywave = polsyn.query(':POLarimeter:WAVelength?').strip()
    print('wave: {}'.format(mywave))
    ## Points
    polsyn.write(':POLarimeter:SWEep:SAMPles {}'.format(polsyn_points))
    mypoints = polsyn.query(':POLarimeter:SWEep:SAMPles?').strip()
    print('points: {}'.format(mypoints))
    polsyn.write(':POLarimeter:SWEep:SRATe {},{}'.format(polsyn_rate,polsyn_avg))
    myrate = polsyn.query(':POLarimeter:SWEep:SRATe?').strip()
    print('rate: {}'.format(myrate))
    
    ## Define Sweep Mode
    polsyn.write(':POLarimeter:SWEep:LOOP 1')
    myloop = polsyn.query(':POLarimeter:SWEep:LOOP?').strip()
    print('loop: {}'.format(myloop))
    
    for i in range(0,10):
    
        ## Start Logging
        polsyn.write('POLarimeter:SWEep:STARt SOP')
        
        stat = ''
        while True:
            if stat == 'READY,DATA_AVAILABLE':
                break
            else:
                ## Query Status
                stat = polsyn.query('POLarimeter:SWEep:STATe?').strip()
                print('stat: {}'.format(stat))
                mylogpoints = polsyn.query(':POLarimeter:SWEep:SAMPles:CURRent?').strip()
                print('log points: {}'.format(mylogpoints))
                time.sleep(0.1)
            
        ## Query Data
        start = time.time()
        mysop = polsyn.query_binary_values(':POLarimeter:SWEep:GET? NORM',datatype='f', is_big_endian=False, chunk_size = 10000000) #100000000
        mypower = polsyn.query_binary_values(':POLarimeter:FUNCtion:RESult?',datatype='f', is_big_endian=False, chunk_size = 10000000)
        xfer_time = time.time() - start
        print('xfer time: {}'.format(str(xfer_time)))
        
        mysop = np.array(mysop)
        mysop0 = mysop[0::3]
        mysop1 = mysop[1::3]
        mysop2 = mysop[2::3]
        mypower = np.array(mypower)
        
        #write coarse and transient polarization files
   
        start = time.time()
        now = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        sop_file = open(file_coarse, 'a')
        sop_file.write('{},{},{},{},{}{}'.format(now,mypower[0],mysop[0],mysop[1],mysop[2],chr(10)))  ## Write 1st data point to coarse file
        sop_file.close()  
        
        # Check for SOP variation
        sop_thresh = 5  ##Poincare Sphere Deviation
        angle = []
        a = [mysop[0],mysop[1],mysop[2]]
        
        # for i in range(1,len(mypower)):
        #     b = [mysop[3*i],mysop[3*i+1],mysop[3*i+2]]
        #     ab = (180/np.pi)*np.arccos((a[0]*b[0]+a[1]*b[1]+a[2]*b[2])/((np.sqrt(a[0]**2+a[1]**2+a[2]**2))*(np.sqrt(b[0]**2+b[1]**2+b[2]**2))))
        #     angle.append(ab)
        
        maga = np.sqrt(a[0]**2+a[1]**2+a[2]**2)
        magb = np.sqrt(mysop0**2+mysop1**2+mysop2**2)
        angle = (180/np.pi) * np.arccos((a[0]*mysop0 + a[1]*mysop1 + a[2]*mysop2) / (maga*magb))
        angle = np.nan_to_num(angle)
        angle_max = np.amax(angle)
        print ('angle max: {}'.format(angle_max))
        
        if angle_max > sop_thresh:
            file_transient = 'C:/Users/Public/N778xC_SOP_transient_{}.txt'.format(now)
            sop_file_transient = open(file_transient , 'w')
            sop_file_transient.write('Power (W), Angle (deg), S1, S2, S3 {}'.format(chr(10)))
            for j in range(0,len(mypower)):
                sop_file_transient.write('{},{},{},{},{}{}'.format(mypower[j],angle[j],mysop[3*j],mysop[3*j+1],mysop[3*j+2],chr(10)))  ## transient SOP
            sop_file_transient.close()

        file_time = time.time() - start
        print('file time: {}'.format(str(file_time)))

    ## Close Instruments
    polsyn.close()

except Exception as err:
    print ('Exception: ' + str(err))
    
finally:
    #perform clean up operations
    print ('complete')



