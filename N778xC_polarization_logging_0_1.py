#!/usr/bin/env python
# coding: utf-8

# N778xC Polarization Logging

import time
import numpy as np
import pyvisa as visa
from datetime import datetime
import argparse

from log_utils import get_basic_logger


# default file path
DEFAULT_DIR = 'C:\\Users\\cool-sailboat\\Box\\UChicago_Keysight\\keysight_link_data\\anl_pol_longterm\\test_data\\'

LOGGING_SEVERITY = 'i'


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'runtime_hours',
        type=float,
        default=1.0,
        help="Time to run measurement, given in hours. Default is 1."
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=DEFAULT_DIR,
        help="Directory in which to store output text files. "
             f"Default is '{DEFAULT_DIR}'."
    )
    parser.add_argument(
        '-p', '--points',
        type=int,
        default=int(1e5),
        help="Number of points to accumulate for each transient run. Must be between 0 and 1e6. Default is 1e5."
    )
    parser.add_argument(
        '-a', '--average',
        type=str,
        choices=['1us', '100us'],
        default='1us',
        help="Time to average for each sample. Allowed values are '1us' and '100us'. Default is '1us'."
    )
    parser.add_argument(
        '-r', '--rate',
        type=str,
        choices=['0.1MHz', '0.5MHz', '10Hz'],
        default='0.1MHz',
        help="Rate for taking samples. Allowed values are '0.1MHz', '0.5MHz', or '10Hz'. Default is '0.1MHz'."
    )
    parser.add_argument(
        '-t', '--threshold',
        type=float,
        default=5.0,
        help="Minimum angle deviation to trigger transient storage (in degrees). Default is 5 degrees."
    )

    args = parser.parse_args()
    if args.points < 0 or args.points > int(1e6):
        raise argparse.ArgumentError(f"Invalid value '{args.points}' given for points.")
    return args.runtime_hours, args.output, args.points, args.average, args.rate, args.threshold


# get arguments
runtime, storage_dir, points_int, polsyn_avg, polsyn_rate, sop_thresh = parse_args()
polsyn_points = str(points_int)

# set up logger
logger = get_basic_logger("anl_pol_longterm", LOGGING_SEVERITY)

# Connect to Polarization Synthesizer
rm = visa.ResourceManager()

# Setup Polarization Controller Sequence
polsyn_wave = '1550e-6'

now = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
file_coarse = storage_dir + 'N778xC_SOP_coarse_{}.txt'.format(now)
logger.info(f"Writing to output file '{file_coarse}'.")

sop_file = open(file_coarse, 'w')
sop_file.write('Avg: {} Rate: {} {}'.format(polsyn_avg, polsyn_rate, chr(10)))
sop_file.write('time, Power (W), S1, S2, S3 {}'.format(chr(10)))
sop_file.close()

logger.info(f'Average: {polsyn_avg}')
logger.info(f'Rate: {polsyn_rate}')


try:
    # Open Connection
    polsyn = rm.open_resource('TCPIP0::100.65.27.149::inst0::INSTR')
    polsyn.timeout = 10000
    # Reset Power Meter
    polsyn.write('*RST')
    _ = polsyn.query('*OPC?')
    polsyn.write('PCON:SWIT 1')  # Polarization Controller Switch
    _ = polsyn.query('*OPC?')
    # Query ID
    myid = polsyn.query('*IDN?').strip()
    logger.info('N778xC ID: ' + myid)
    
    # deactivate autogain
    polsyn.write(':POLarimeter:AGFlag')
    # set manual gain
    polsyn.write(':POLarimeter:GAIN 8')

    # Non Transient file and Transient file w/ time stamps
    
    # Setup Logging
    
    # Wavelength
    polsyn.write(':POLarimeter:WAVelength {}'.format(polsyn_wave))
    mywave = polsyn.query(':POLarimeter:WAVelength?').strip()
    logger.info('wave: {}'.format(mywave))

    # Points
    polsyn.write(':POLarimeter:SWEep:SAMPles {}'.format(polsyn_points))
    mypoints = polsyn.query(':POLarimeter:SWEep:SAMPles?').strip()
    logger.info('points: {}'.format(mypoints))

    polsyn.write(':POLarimeter:SWEep:SRATe {},{}'.format(polsyn_rate, polsyn_avg))
    myrate = polsyn.query(':POLarimeter:SWEep:SRATe?').strip()
    logger.info('rate: {}'.format(myrate))
    
    # Define Sweep Mode
    polsyn.write(':POLarimeter:SWEep:LOOP 1')
    myloop = polsyn.query(':POLarimeter:SWEep:LOOP?').strip()
    logger.info('loop: {}'.format(myloop))

    runtime *= 3600  # convert from hours to seconds
    start_of_loop = time.time()
    while time.time() - start_of_loop < runtime:
    
        # Start Logging
        polsyn.write('POLarimeter:SWEep:STARt SOP')
        
        stat = ''
        while True:
            if stat == 'READY,DATA_AVAILABLE':
                break
            else:
                # Query Status
                stat = polsyn.query('POLarimeter:SWEep:STATe?').strip()
                logger.debug('stat: {}'.format(stat))
                mylogpoints = polsyn.query(':POLarimeter:SWEep:SAMPles:CURRent?').strip()
                logger.debug('log points: {}'.format(mylogpoints))
                time.sleep(0.1)
        logger.info('Data available.')
            
        # Query Data
        start = time.time()
        mysop = polsyn.query_binary_values(':POLarimeter:SWEep:GET? NORM',
                                           datatype='f',
                                           is_big_endian=False,
                                           chunk_size=10000000)  # 100000000
        mypower = polsyn.query_binary_values(':POLarimeter:FUNCtion:RESult?',
                                             datatype='f',
                                             is_big_endian=False,
                                             chunk_size=10000000)
        xfer_time = time.time() - start
        logger.debug('xfer time: {}'.format(str(xfer_time)))
        
        mysop = np.array(mysop)
        mysop0 = mysop[0::3]
        mysop1 = mysop[1::3]
        mysop2 = mysop[2::3]
        mypower = np.array(mypower)
        
        # write coarse and transient polarization files
   
        start = time.time()
        now = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        sop_file = open(file_coarse, 'a')
        sop_file.write('{},{},{},{},{}{}'.format(
            now, mypower[0], mysop[0], mysop[1], mysop[2], chr(10)))  # Write 1st data point to coarse file
        sop_file.close()  
        
        # Check for SOP variation
        a = [mysop[0], mysop[1], mysop[2]]

        # angle = []
        # for i in range(1,len(mypower)):
        #     b = [mysop[3*i],mysop[3*i+1],mysop[3*i+2]]
        #     ab = (180/np.pi)*np.arccos((a[0]*b[0]+a[1]*b[1]+a[2]*b[2])/((np.sqrt(a[0]**2+a[1]**2+a[2]**2))*(np.sqrt(b[0]**2+b[1]**2+b[2]**2))))
        #     angle.append(ab)
        
        maga = np.sqrt(a[0]**2+a[1]**2+a[2]**2)
        magb = np.sqrt(mysop0**2+mysop1**2+mysop2**2)
        angle = (180/np.pi) * np.arccos((a[0]*mysop0 + a[1]*mysop1 + a[2]*mysop2) / (maga*magb))
        angle = np.nan_to_num(angle)
        angle_max = np.amax(angle)
        logger.info('angle max: {}'.format(angle_max))
        
        if angle_max > sop_thresh:
            file_transient = storage_dir + 'N778xC_SOP_transient_{}.txt'.format(now)
            sop_file_transient = open(file_transient, 'w')
            sop_file_transient.write('Power (W), Angle (deg), S1, S2, S3 {}'.format(chr(10)))
            for j in range(len(mypower)):
                sop_file_transient.write('{},{},{},{},{}{}'.format(
                    mypower[j], angle[j], mysop[3*j], mysop[3*j+1], mysop[3*j+2], chr(10)))  # transient SOP
            sop_file_transient.close()

        file_time = time.time() - start
        logger.debug('file time: {}'.format(str(file_time)))

    # Close Instruments
    logger.info('Closing instrument connection.')
    polsyn.close()

except Exception as err:
    logger.error('Exception: ' + str(err))
    
finally:
    # perform clean up operations
    logger.info('Complete.')
