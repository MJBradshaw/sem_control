# program to run the Amray SEM v1.15
# Written by Mark Bradshaw

"""
This program was written to act as the scan generator, monitor and recorder
for a scanning electron microscope. It is written in python and depends on TKinter
for GUI construction, matplotlib for data visualization, and a wrapper for the
NIDAQ 6.9 driver for communication with the DAQPAD-1200 used as the analog interface.
"""

import tkinter as Tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

import PIL

import threading

# for testing
from numpy import arange, sin, pi, zeros, linspace, rint, int16, uint8, dstack, resize, floor, divide, tile, atleast_3d
from numpy.random import rand

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm

from time import sleep

#for performance testing
import time

import pyNIDAQ as pyNIDAQ

"""************************ Global Variables ***********"""
CONT_SCAN = 0    # Flag to tell the scan generator to run continuosly in run mode, or once in record mode
MAP_UPDATE = 1   # Draw image to the screen or not

XResolution = 1024
YResolution = 1024
DataMap = zeros((XResolution, YResolution), dtype=int16)
ImgMap = zeros((XResolution, YResolution), dtype=uint8)

# DAQPAD-1200 configuration
XChannel = 0    # Analog out channel of DAQ
YChannel = 1    # Analog out channel of DAQ
SigChannel = 0    # Signal intensity IN channel of DAQ 

DATALOCK = threading.Lock()


"""***********   Scan Generator   ****************"""
class ScanGenerator(threading.Thread):

    def run(self):
        global XResolution, YResolution, DataMap, XChannel, YChannel, CONT_SCAN

        
        YVals = rint(linspace(-2048, 2047, YResolution)).astype(int16)
        XVals = rint(linspace(-2048, 2047, XResolution)).astype(int16)

        # CONT_SCAN == -1 means run continiously
        # CONT_SCAN == 1 means raster over the field once
        # Currently the scan is generated point by point. Future revisions will use the DAQPAD waveform generator and buffers
        while (CONT_SCAN == -1 or CONT_SCAN == 1):
            for j in range(YResolution): # For every horizontal line in the field
                if (CONT_SCAN == 0): break
                for i in range(XResolution): # For every pixel along horizontal line j
                    if (CONT_SCAN == 0): break

                    # Write out the analog signal
                    pyNIDAQ.pyAO_Write(1, XChannel, XVals[i])
                    pyNIDAQ.pyAO_Write(1, YChannel, YVals[j])
                    
                    # Read the signal in for RunDwellTime 
                    #temp = pyNIDAQ.pyAI_Read(1, SigChannel, 1)
                    temp = pyNIDAQ.pyAI_Read(1, SigChannel, 10)
                    DATALOCK.acquire()
                    DataMap[j, i] = temp
                    DATALOCK.release()
            
            if (CONT_SCAN == 1):
                DATALOCK.acquire()
                CONT_SCAN = 0
                DATALOCK.release()
            sleep(0.01)
                    
        print("scan thread terminating")
        return # Thread will terminate when it returns


class App:


    """************************* Button function declarations"""""""""""""""""""""

    def __init__(self, master):

        #self.scangen = ScanGenerator()        

        self.RunDwellTime = 1
        self.RecDwellTime = 10
        
        buttonframe = ttk.Frame(root, padding="3 3 12 12")
        buttonframe.grid(column=0, row=0, sticky=(Tk.N, Tk.W, Tk.E, Tk.S))
        buttonframe.columnconfigure(0, weight=1)
        buttonframe.rowconfigure(0, weight=0)
        buttonframe['borderwidth'] = 2
        buttonframe['relief'] = 'sunken'

        ttk.Button(buttonframe, text="Scan 1", command= lambda:self.SetRunScan(1)).grid(column=0, row=0, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="Scan 2", command= lambda:self.SetRunScan(2)).grid(column=0, row=1, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="Scan 3", command= lambda:self.SetRunScan(3)).grid(column=0, row=2, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="Scan 4", command= lambda:self.SetRunScan(4)).grid(column=0, row=3, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="RUN", command= lambda:self.run_button_press()).grid(column=0, row=4, sticky=(Tk.N, Tk.W))

        #ttk.Button(buttonframe, text="Rec Scan1", command= lambda:self.SetRecScan(1)).grid(column=0, row=5, sticky=(Tk.N, Tk.W))
        #ttk.Button(buttonframe, text="Rec Scan2", command= lambda:self.SetRecScan(2)).grid(column=0, row=6, sticky=(Tk.N, Tk.W))
        #ttk.Button(buttonframe, text="Rec Scan3", command= lambda:self.SetRecScan(3)).grid(column=0, row=7, sticky=(Tk.N, Tk.W))
        #ttk.Button(buttonframe, text="Rec Scan4", command= lambda:self.SetRecScan(4)).grid(column=0, row=8, sticky=(Tk.N, Tk.W))
        #ttk.Button(buttonframe, text="RECORD", command= lambda:self.rec_button_press()).grid(column=0, row=9, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="IMG ON/OFF", command= lambda:self.toggle_map_update()).grid(column=0, row=9, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="SAVE", command= lambda:self.save_image()).grid(column=0, row=10, sticky=(Tk.N, Tk.W))
        ttk.Button(buttonframe, text="QUIT", command= lambda:self.quit()).grid(column=0, row=11, sticky=(Tk.N, Tk.W))
        
        for child in buttonframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        imageframe = ttk.Frame(root, padding="3 3 12 12")
        imageframe.grid(column=2, row=0, sticky=(Tk.N, Tk.W, Tk.E, Tk.S))
        imageframe.columnconfigure(0, weight=0)
        imageframe.rowconfigure(0, weight=0)        

        self.fig = plt.figure(figsize=(8.2,8.2), frameon=True)
        self.ax = self.fig.add_axes([0,0,1,1])
        self.ax.axis('off')
        self.im = self.ax.imshow(dstack([ImgMap, ImgMap, ImgMap]), interpolation='nearest', cmap = cm.Greys_r, vmin=0, vmax=256)
        self.canvas = FigureCanvasTkAgg(self.fig, master=imageframe)
        self.canvas.get_tk_widget().grid(column=0, row=0, sticky=(Tk.N, Tk.W, Tk.E, Tk.S))
        self.update_map()
        
    def SetRunScan(self,i):
        """Set the scan parameters to a predefined value from a list of scan rates.
        """
        global XResolution, YResolution, DataMap, ImgMap, CONT_SCAN
        
        if i == 1:
            CONT_SCAN = 0
            try:
                while self.scangen.isAlive():
                    sleep(1)
            except AttributeError:
                pass
            RunDwellTime = 1
            XResolution = 128
            YResolution = 128
            print(XResolution, YResolution)
            ImgMap = zeros((XResolution, YResolution), dtype=uint8)
            DataMap = zeros((XResolution, YResolution), dtype=int16)
            print('Run scan rate 1 selected')
            CONT_SCAN = -1
            self.scangen = ScanGenerator()
            self.scangen.start()

        elif i == 2:
            CONT_SCAN = 0
            try:
                while self.scangen.isAlive():
                    sleep(1)
            except AttributeError:
                pass
            RunDwellTime = 5
            XResolution = 256
            YResolution = 256
            print(XResolution, YResolution)
            ImgMap = zeros((XResolution, YResolution), dtype=uint8)
            DataMap = zeros((XResolution, YResolution), dtype=int16)
            print('Run scan rate 2 selected')
            CONT_SCAN = -1
            self.scangen = ScanGenerator()
            self.scangen.start()

        elif i == 3:
            CONT_SCAN = 0
            try:
                while self.scangen.isAlive():
                    sleep(1)
            except AttributeError:
                pass
            RunDwellTime = 5
            XResolution = 512
            YResolution = 512
            print(XResolution, YResolution)
            ImgMap = zeros((XResolution, YResolution), dtype=uint8)
            DataMap = zeros((XResolution, YResolution), dtype=int16)
            print('Run scan rate 3 selected')
            CONT_SCAN = -1
            self.scangen = ScanGenerator()
            self.scangen.start()

        elif i == 4:
            CONT_SCAN = 0
            try:
                while self.scangen.isAlive():
                    sleep(1)
            except AttributeError:
                pass
            RunDwellTime = 5
            XResolution = 1024
            YResolution = 1024
            print(XResolution, YResolution)
            ImgMap = zeros((XResolution, YResolution), dtype=uint8)
            DataMap = zeros((XResolution, YResolution), dtype=int16)
            print('Run scan rate 4 selected')
            CONT_SCAN = -1
            self.scangen = ScanGenerator()
            self.scangen.start()
        else:
            print('Invalid Run scan rate selected')

    def SetRecScan(self,i):
        """Set the scan parameters to a predefined value from a list of scan rates.
        """
        #global XResolution, YResolution, DataMap

        if i == 1:
            RecDwellTime = 10
            XResolution = 1024
            YResolution = 1024
            print(XResolution, YResolution)
            self.ax.set_xlim(0, XResolution)
            self.ax.set_ylim(YResolution, 0)
            print('Rec scan rate 1 selected')
        elif i == 2:
            RecDwellTime = 20
            XResolution = 1024
            YResolution = 1024
            print(XResolution, YResolution)
            self.ax.set_xlim(0, XResolution)
            self.ax.set_ylim(YResolution, 0)
            print('Rec scan rate 2 selected')
        elif i == 3:
            RecDwellTime = 10
            XResolution = 2048
            YResolution = 2048
            print(XResolution, YResolution)
            self.ax.set_xlim(0, XResolution)
            self.ax.set_ylim(YResolution, 0)
            print('Rec scan rate 3 selected')
        elif i == 4:
            RecDwellTime = 20
            XResolution = 2048
            YResolution = 2048
            print(XResolution, YResolution)
            self.ax.set_xlim(0, XResolution)
            self.ax.set_ylim(YResolution, 0)
            print('Rec scan rate 4 selected')
        else:
            print('Invalid Rec scan rate selected')

    def run_button_press(self):
        global CONT_SCAN
        DATALOCK.acquire()
        if (CONT_SCAN == 0):
            CONT_SCAN = -1
            sleep(0.5)
            self.scangen = ScanGenerator()
            self.scangen.start()
            print("Contscan = ", CONT_SCAN)
        elif (CONT_SCAN == -1):
            CONT_SCAN = 0
        DATALOCK.release()

    def rec_button_press(self):
        global CONT_SCAN
        DATALOCK.acquire()
        if (CONT_SCAN == 0):
            CONT_SCAN = 1
            sleep(0.5)
            self.scangen = ScanGenerator()
            self.scangen.start()
            print("Contscan = ", CONT_SCAN)
        elif (CONT_SCAN == -1):
            CONT_SCAN = 0
            sleep(1)
            CONT_SCAN = 1
            self.scangen = ScanGenerator()
            self.scangen.start()
        DATALOCK.release()

    def toggle_map_update(self):
        global MAP_UPDATE
        if MAP_UPDATE:
            MAP_UPDATE = 0
        else:
            MAP_UPDATE = 1

    def update_map(self):
        global ImgMap
        if MAP_UPDATE:
            starttime = time.time()
            divide((DataMap+2048), 16, ImgMap)
            self.im.set_data(dstack([ImgMap, ImgMap, ImgMap]))
            self.canvas.draw()
            endtime = time.time()
            deltatime = starttime - endtime
            print("idle event")
            print("draw time: ", deltatime)
        root.after(1000, self.update_map)

    def save_image(self):
        image = PIL.Image.fromarray(DataMap)
        image.save("Test.tif", "tiff")

    def quit(self):
        global CONT_SCAN
        CONT_SCAN = 0
        try:
            while self.scangen.isAlive():
                sleep(1)
        except AttributeError:
            pass
        root.quit()


                
    """""""""""""""""""""""""""""""""" Window Construction """""""""""""""""""""""""""""""""
        
root = Tk.Tk()
root.title("SEM control v1.0")

app = App(root)

root.mainloop()
root.destroy()
