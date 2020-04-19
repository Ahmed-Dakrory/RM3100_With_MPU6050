import time
import math
import mpu6050
from rm3100  import RM3100

rm3100 = RM3100(17,27)
DRDY = 27 #GPIO 27
SSN = 17 #GPIO 17


# Sensor initialization
mpu = mpu6050.MPU6050()
mpu.dmpInitialize()
mpu.setDMPEnabled(True)
    
# get expected DMP packet size for later comparison
packetSize = mpu.dmpGetFIFOPacketSize() 

while True:
    # Get INT_STATUS byte
    mpuIntStatus = mpu.getIntStatus()
  
    if mpuIntStatus >= 2: # check for DMP data ready interrupt (this should happen frequently) 
        # get current FIFO count
        fifoCount = mpu.getFIFOCount()
        
        # check for overflow (this should never happen unless our code is too inefficient)
        if fifoCount == 1024:
            # reset so we can continue cleanly
            mpu.resetFIFO()
            print('FIFO overflow!')
            
            
        # wait for correct available data length, should be a VERY short wait
        fifoCount = mpu.getFIFOCount()
        while fifoCount < packetSize:
            fifoCount = mpu.getFIFOCount()
        
        result = mpu.getFIFOBytes(packetSize)
        q = mpu.dmpGetQuaternion(result)
        g = mpu.dmpGetGravity(q)
        ypr = mpu.dmpGetYawPitchRoll(q, g)
        mag = rm3100.readMag()

        pitch = ypr['pitch']
        roll = ypr['roll']

        CMx = mag['x']*math.cos(pitch) + mag['z']*math.sin(pitch)
        CMy = mag['x']*math.sin(roll)*math.sin(pitch) + mag['y']*math.cos(roll)- mag['z']*math.sin(roll)*math.cos(pitch)

        MAG_Heading = -(math.atan2(CMy,CMx) * 180 / math.pi)+180

        #print(yaw +(0.6*ypr['pitch'] * 180 / math.pi)-(0.6*ypr['roll'] * 180 / math.pi)),
        #print(ypr['pitch'] * 180 / math.pi),
        print(MAG_Heading)
    
        # track FIFO count here in case there is > 1 packet available
        # (this lets us immediately read more without waiting for an interrupt)        
        fifoCount -= packetSize  