# -*- coding: utf-8 -*-

"""Main module."""

import spidev
import RPi.GPIO as GPIO
import time
import math
import struct


class RM3100(object):


    RM3100_POLL_REG   = 0x00
    RM3100_CMM_REG    = 0x01
    RM3100_CCXLSB_REG = 0x04
    RM3100_CCXMSB_REG = 0x05
    RM3100_CCYLSB_REG = 0x06
    RM3100_CCYMSB_REG = 0x07
    RM3100_CCZLSB_REG = 0x08
    RM3100_CCZMSB_REG = 0x09
    RM3100_TMRC_REG   = 0x0B 
    RM3100_MX_REG     = 0x24 
    RM3100_BIST_REG   = 0x33
    RM3100_STATUS_REG = 0x34 
    RM3100_REVID_REG  = 0x36 
    RM3100POLL_MXYX = 0x70
    # CCP0          = 0x64 # 100 Cycle Count
    # CCP1          = 0x00
    CCP0          = 0xC8 # 200 Cycle Count
    CCP1          = 0x00
    # CCP0          = 0x90 # 400 Cycle Count
    # CCP1          = 0x01 

    #Other Settings
    RM3100_TMRC_600HZ = 0x92
    RM3100_TMRC_300HZ = 0x93
    RM3100_TMRC_150HZ = 0x94
    RM3100_TMRC_75HZ = 0x95
    RM3100_TMRC_37HZ = 0x96

    DEG_PER_RAD = 180.0/3.14159265358979

    rm3100_resolution = 75 #  microT/lsb, 200 cycle @ 1 avg

    def __init__(self, SSN, DRDY):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.SSN = SSN
        self.DRDY = DRDY
        GPIO.setwarnings(False)    
        GPIO.setmode(GPIO.BCM)    
        GPIO.setup(self.SSN, GPIO.OUT)
        GPIO.setup(self.DRDY, GPIO.IN) 
        print("SSN %s " % self.SSN)
        print("DRDY %s" % self.DRDY)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz=1000000
        # Default to mode 0.
        self.spi.mode = 0
        self.spi.no_cs = True
        self.spi.lsbfirst = False
        
        self.configure_the_RM3100()

    def configure_the_RM3100(self):
        self.write([self.RM3100_POLL_REG,0x00,0x00])#clear all reg
        time.sleep(0.02)
        self.write([self.RM3100_CCXLSB_REG,self.CCP1,self.CCP0,self.CCP1,self.CCP0,self.CCP1,self.CCP0])#initial Config
        time.sleep(0.02)
        self.write([self.RM3100_CMM_REG,0x79])#write to CMM
        time.sleep(0.02)
        self.write([self.RM3100_TMRC_REG,self.RM3100_TMRC_150HZ])#write to TMRC to be 150Hz
        time.sleep(0.02)

        TMRC = self.read([0x8B])
        CMM = self.read([0x81])
        print("TMRC Set To %x and CMM set To %x" % (int(TMRC[0]) , int(CMM[0])))


    def send_Poll_Read(self):
        self.write([self.RM3100_POLL_REG,self.RM3100POLL_MXYX])# send Poll Reg
        time.sleep(0.01)
        state = GPIO.input(self.DRDY)

        return state


    def readMag(self):
        state = self.send_Poll_Read()
        MagValues = []
        if state == 1:
            raw = self.read3([0xA4])

            for i in range(0, 9, 3):
                data = float(self.recast24to32(raw[i],raw[i+1],raw[i+2]))*self.rm3100_resolution
                MagValues.append(data)
            return {'x': MagValues[0], 'y': MagValues[1], 'z': MagValues[2]}
        else:
            return None

    

    def getHeading(self):
        Mag = self.readMag()
        if Mag == None:
            return None
        else:
            return -(math.atan2(Mag['y'],Mag['x']) * self.DEG_PER_RAD)+180



    def write(self,list_of_address):
        GPIO.output(self.SSN, GPIO.LOW)
        self.spi.xfer2(list_of_address)
        GPIO.output(self.SSN, GPIO.HIGH)

    def read(self,list_from_address):
        GPIO.output(self.SSN, GPIO.LOW)
        self.spi.xfer2(list_from_address)
        data = self.spi.xfer2([0])
        GPIO.output(self.SSN, GPIO.HIGH)

        return data
    

    def read3(self,list_from_address):
        GPIO.output(self.SSN, GPIO.LOW)
        self.spi.xfer2(list_from_address)
        magx2 = int(self.spi.xfer2([0])[0])
        magx1 = int(self.spi.xfer2([0])[0])
        magx0 = int(self.spi.xfer2([0])[0])
        magy2 = int(self.spi.xfer2([0])[0])
        magy1 = int(self.spi.xfer2([0])[0])
        magy0 = int(self.spi.xfer2([0])[0])
        magz2 = int(self.spi.xfer2([0])[0])
        magz1 = int(self.spi.xfer2([0])[0])
        magz0 = int(self.spi.xfer2([0])[0])
        GPIO.output(self.SSN, GPIO.HIGH)

        return [magx2,magx1,magx0,magy2,magy1,magy0,magz2,magz1,magz0]

    ###############################################################################
    def recast24to32(self,byte0,byte1,byte2):
        # pack 24 bits (3 bytes) into 32 bits byte-type
        b24 = struct.pack('xBBB',byte0,byte1,byte2)

        # unpack to unsigned long integer
        uL = struct.unpack('>L',b24)[0]

        # this is for 2's complement signed numbers - 
        #   if negative assign sign bits for 32 bit case
        if (uL & 0x00800000):
            uL = uL | 0xFF000000

        # repack as 32 bit unsigned long byte-type
        packed = struct.pack('>L', uL)
        # unpack as 32 bit signed long integer
        unpacked = struct.unpack('>l', packed)[0]

        return unpacked