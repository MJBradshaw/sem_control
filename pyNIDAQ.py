# This file contains the functions needed to interact with the DAQpad-1200
# using NI-DAQ 6.9

# Mark: this is my trying to replicate the file AIonePoint.C from the NiDaq examples

import ctypes
import numpy
#nidaq = ctypes.windll.nicaiu # load the DLL
nidaq = ctypes.windll.nidaq32 # load the DLL
##############################
# Setup some typedefs and constants
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs
int16 = ctypes.c_int16
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32

# Local Variable Declarations
iStatus = int16(0)
iRetVal = int16(0)
iDevice = int16(1)
iChan = int16(1)
iGain = int16(1)
dVoltage = float64(0.0)
iReading = int16(0)
dVoltage_O = float64(0.0)
iReading_O = int16(0)
iIgnoreWarning = int16(0)
iInputMode = int16(0)
iInputRange = int16(0)
iPolarity = int16(0)
iDriveAIS = int16(0)

def CHK(err): # This is from scipy wiki
    """a simple error checking routine"""
    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
        raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))

def pyAI_Configure(pyDeviceNumber, pyChan, pyInputMode, pyInputRange, pyPolarity, pyDriveAIS):
    """Informs NI-DAQ of the input mode (single-ended or differential),
    input range, and input polarity selected for the device. Use this
    function if you have changed the jumpers affecting the analog input
    configuration from their factory settings. For devices without analog
    input configuration jumpers, this function programs the device for
    the settings you want."""

    iDevice.value = pyDeviceNumber
    iChan.value = pyChan
    iInputMode.value = pyInputMode
    iInputRange.value = pyInputRange
    iPolarity.value = pyPolarity
    iDriveAIS.value = pyDriveAIS

    CHK( nidaq.AI_Configure( iDevice, iChan, iInputMode, iInputRange, iPolarity, iDriveAIS) )
    return 1


    

#def pyAI_VRead(iDevice.value, iChan.value, iGain.value) invalid syntax
def pyAI_VRead(pyDevice, pyChan, pyGain):
    iDevice.value = pyDevice
    iChan.value = pyChan
    iGain.value = pyGain
    
    CHK( nidaq.AI_VRead(iDevice, iChan, iGain, ctypes.byref(dVoltage)) )
    
    #print(dVoltage.value)
    return dVoltage.value

def pyAI_Read(pyDevice, pyChan, pyGain):
    iDevice.value = pyDevice
    iChan.value = pyChan
    iGain.value = pyGain
    
    CHK( nidaq.AI_Read(iDevice, iChan, iGain, ctypes.byref(iReading)) )
    
    #print(dVoltage.value)
    return iReading.value

def pyAO_VWrite(pyDevice, pyChan, pyVoltage):
    iDevice.value = pyDevice
    iChan.value = pyChan
    dVoltage_O.value = pyVoltage

    CHK( nidaq.AO_VWrite(iDevice, iChan, dVoltage_O) )
    return 1

def pyAO_Write(pyDevice, pyChan, pyReading):
    iDevice.value = pyDevice
    iChan.value = pyChan
    iReading_O.value = pyReading

    CHK( nidaq.AO_Write(iDevice, iChan, iReading_O) )
    return 1




