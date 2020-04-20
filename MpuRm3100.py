import time
import math
import mpu6050
from rm3100  import RM3100
import threading



class IMU (threading.Thread):
    def __init__(self, SSN, DRDY):
        threading.Thread.__init__(self)
        self.SSN = SSN
        self.DRDY = DRDY
        self.rm3100 = RM3100(self.SSN,self.DRDY)
        self.Readings = None
        # Sensor initialization
        self.mpu = mpu6050.MPU6050()
        self.mpu.dmpInitialize()
        self.mpu.setDMPEnabled(True)

        # get expected DMP packet size for later comparison
        self.packetSize = self.mpu.dmpGetFIFOPacketSize() 

    def run(self):
        while True:
            # Get INT_STATUS byte
            self.mpuIntStatus = self.mpu.getIntStatus()

            if self.mpuIntStatus >= 2: # check for DMP data ready interrupt (this should happen frequently) 
                # get current FIFO count
                fifoCount = self.mpu.getFIFOCount()

                # check for overflow (this should never happen unless our code is too inefficient)
                if fifoCount == 1024:
                    self.mpu.resetFIFO()

                fifoCount = self.mpu.getFIFOCount()

                while fifoCount < self.packetSize:
                    fifoCount = self.mpu.getFIFOCount()

                result = self.mpu.getFIFOBytes(self.packetSize)
                q = self.mpu.dmpGetQuaternion(result)
                g = self.mpu.dmpGetGravity(q)
                ypr = self.mpu.dmpGetYawPitchRoll(q, g)
                mag = self.rm3100.readMag()

                pitch = ypr['pitch']
                roll = ypr['roll']

                if mag !=None:
                    CMx = mag['x']*math.cos(pitch) + mag['z']*math.sin(pitch)
                    CMy = mag['x']*math.sin(roll)*math.sin(pitch) + mag['y']*math.cos(roll)- mag['z']*math.sin(roll)*math.cos(pitch)

                    MAG_Heading = -(math.atan2(CMy,CMx) * 180 / math.pi)+180

                    self.Readings ={'Roll':roll,'Pitch':pitch,'Yaw':MAG_Heading}
                else:
                    self.Readings = None

                #print(MAG_Heading)

                # track FIFO count here in case there is > 1 packet available
                # (this lets us immediately read more without waiting for an interrupt)        
                fifoCount -= self.packetSize
