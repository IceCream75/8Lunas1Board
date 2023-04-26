import time
from smbus import SMBus

# Timeout Limits for various functions
TFL_MAX_READS           = 20   # readData() sets SERIAL error
MAX_BYTES_BEFORE_HEADER = 20   # getData() sets HEADER error
MAX_ATTEMPTS_TO_MEASURE = 20

address = 0x10        # TFLuna I2C device address
                      # Range: 0x08 to 0x77
tflPort = 1           # Raspberry Pi I2C port number
                      # 4 = /dev/i2c-4, GPIO 8/9, pins 24/21
                      # 1 = /dev/i2c-1, SDA/SCL, pins 3/5

# - - -  Register Names, Hex Address Numbers  - - -
# - - - -  and whether Read, Write or both  - - - -
TFL_DIST_LO        = 0x00  # R centimeters
TFL_DIST_HI        = 0x01  # R
TFL_FLUX_LO        = 0x02  # R arbitray units
TFL_FLUX_HI        = 0x03  # R
TFL_TEMP_LO        = 0x04  # R degrees Celsius
TFL_TEMP_HI        = 0x05  # R
TFL_TICK_LO        = 0x06  # R milliseconds
TFL_TICK_HI        = 0x07  # R
TFL_ERR_LO         = 0x08  # R
TFL_ERR_HI         = 0x09  # R
TFL_VER_REV        = 0x0A  # R revision
TFL_VER_MIN        = 0x0B  # R minor release
TFL_VER_MAJ        = 0x0C  # R major release

TFL_PROD_CODE      = 0x10  # R - 14 byte serial number

TFL_SAVE_SETTINGS  = 0x20  # W -- Write 0x01 to save
TFL_SOFT_RESET     = 0x21  # W -- Write 0x02 to reboot.
                     # Lidar not accessible during few seconds,
                     # then register value resets automatically
TFL_SET_I2C_ADDR   = 0x22  # W/R -- Range 0x08,0x77.
                     # Must save and reboot to take effect.
TFL_SET_MODE       = 0x23  # W/R -- 0-continuous, 1-trigger
TFL_TRIGGER        = 0x24  # W  --  1-trigger once
TFL_DISABLE        = 0x25  # W/R -- 0-enable, 1-disable
TFL_FPS_LO         = 0x26  # W/R -- lo byte
TFL_FPS_HI         = 0x27  # W/R -- hi byte
TFL_SET_LO_PWR     = 0x28  # W/R -- 0-normal, 1-low power
TFL_HARD_RESET     = 0x29  # W  --  1-restore factory settings

# - -   Error Status Condition definitions - -
TFL_READY         =  0  # no error
TFL_SERIAL        =  1  # serial timeout
TFL_HEADER        =  2  # no header found
TFL_CHECKSUM      =  3  # checksum doesn't match
TFL_TIMEOUT       =  4  # I2C timeout
TFL_PASS          =  5  # reply from some system commands
TFL_FAIL          =  6  #           "
TFL_I2CREAD       =  7
TFL_I2CWRITE      =  8
TFL_I2CLENGTH     =  9
TFL_WEAK          = 10  # Signal Strength ≤ 100
TFL_STRONG        = 11  # Signal Strength saturation
TFL_FLOOD         = 12  # Ambient Light saturation
TFL_MEASURE       = 13
TFL_INVALID       = 14  # Invalid operation sent to sendCommand()



class TFLuna:
    def __init__(self, bs, channel, addr = 0x10, port=1):
        self.status = 0            # error status code
        self.dist =   0            # distance to target
        self.flux =   0            # signal quality or intensity
        self.temp =   0            # internal chip temperature

        self.bus=bs
        self.address = addr    # re-assign device address
        self.tflPort = port    # re-assign port number

        self.channel = channel
        try:
            self.bus.write_quick(self.address)                       #  Short test transaction
        
            self.bus.write_byte_data(self.address, TFL_SET_MODE, 1)  # Set device to single-shot/trigger mode
            print(f'TFLuna on channel {channel} initialized !')
            self.init = True
        except Exception as e:
            print(f'Error creating TFLuna on channel {channel}: {str(e)}')
            self.init = False
    
    def getData(self):
        #  1. Get data from the device.
        # Trigger a one-shot data sample
        self.bus.write_byte_data(self.address, TFL_TRIGGER, 1)
        #  Read the first six registers
        frame = self.bus.read_i2c_block_data(self.address, 0, 6)

        #  2. Shift data from read array into the three variables
        self.dist = frame[0] + (frame[1] << 8)
        self.flux = frame[2] + (frame[3] << 8)
        self.temp =(frame[4] + (frame[5] << 8)) / 100 # temp is in hundredths Celsius

        #  3.  Evaluate Abnormal Data Values
        if(self.dist == -1):
            self.status = TFL_WEAK
            return False
        elif(self.flux < 100):         # Signal strength < 100
            self.status = TFL_WEAK
            return False
        elif(self.flux > 0x8000):      # Ambient light too strong
            self.status = TFL_FLOOD
            return False
        elif(self.flux == 0xFFFF):     # Signal saturation
            self.status = TFL_STRONG
            return False

        self.status = TFL_READY
        return True


    def saveSettings(self):
        self.bus.write_byte_data(self.address, TFL_SAVE_SETTINGS, 1)
        time.sleep(1)

    #reboot
    def softReset(self):
        self.bus.write_byte_data(self.address, TFL_SOFT_RESET, 2)
        time.sleep(1)

    # Factory reset
    def hardReset(self):
        self.bus.write_byte_data(self.address, TFL_HARD_RESET, 1)

    #  Range: [0x08, 0x77]
    def setI2Caddr(addrNew):
        print("Changing address - Before : " + hex(bus.read_byte_data(self.address, TFL_SET_I2C_ADDR)))
        self.bus.write_byte_data(self.address, TFL_SET_I2C_ADDR, addrNew)
        print("Changing address - After  : " + hex(bus.read_byte_data(self.address, TFL_SET_I2C_ADDR)))
        saveSettings()
        softReset()

    #  Turn on LiDAR
    def setEnable(self):
        self.bus.write_byte_data(self.address, TFL_DISABLE, 0)
        saveSettings()
        softReset()

    #  Turn off LiDAR
    def setDisable(self):
        self.bus.write_byte_data(self.address, TFL_DISABLE, 1)
        saveSettings()
        softReset()

    #  Continuous ranging mode
    def setModeCont(self):
        self.bus.write_byte_data(self.address, TFL_SET_MODE, 0)
        saveSettings()
        softReset()

    #  Sample range only once when triggered
    def setModeTrig(self):
        self.bus.write_byte_data(self.address, TFL_SET_MODE, 1)
        saveSettings()
        softReset()

    def getMode(self):
        mode = self.bus.read_byte_data(self.address, TFL_SET_MODE)
        if mode == 0: return 'continuous'
        else:         return 'trigger'

    #  Trigger device to sample one time.
    def setTrigger(self):
        self.bus.write_byte_data(self.address, TFL_TRIGGER, 1)

    #  Write `fps` (frames per second) to device
    def setFrameRate(fps):
        self.bus.write_word_data(self.address, TFL_FPS_LO, (fps))
        saveSettings()
        softReset()

    #  Return two-byte Frame Rate (frames per second) value
    def getFrameRate(self):
        fps = self.bus.read_word_data(self.address, TFL_FPS_LO)
        return fps

    #  Return two-byte value of milliseconds since last reset.
    def getTime(self):
        t = self.bus.read_word_data(self.address, TFL_TICK_LO)
        return t

    #  Return serial number
    def getProdCode(self):
        prodcode = ''
        for i in range(14):
            prodcode += chr(bus.read_byte_data(self.address, TFL_PROD_CODE + i))
        return prodcode

    #  Return firmware version
    def getFirmwareVersion(self):
        version = ''
        version =\
            str(bus.read_byte_data(self.address, TFL_VER_MAJ)) + '.' +\
            str(bus.read_byte_data(self.address, TFL_VER_MIN)) + '.' +\
            str(bus.read_byte_data(self.address, TFL_VER_REV))
        return version

    #  Called by either 'printFrame()' or 'printReply()'
    #  Print status condition either 'READY' or error type
    def printStatus(self):
        print(self.channel, end=" - ")
        print("Status: ", end= '')
        if(self.status == TFL_READY):       print("READY", end= '')
        elif(self.status == TFL_SERIAL):    print("SERIAL", end= '')
        elif(self.status == TFL_HEADER):    print("HEADER", end= '')
        elif(self.status == TFL_CHECKSUM):  print("CHECKSUM", end= '')
        elif(self.status == TFL_TIMEOUT):   print("TIMEOUT", end= '')
        elif(self.status == TFL_PASS):      print("PASS", end= '')
        elif(self.status == TFL_FAIL):      print("FAIL", end= '')
        elif(self.status == TFL_I2CREAD):   print("I2C-READ", end= '')
        elif(self.status == TFL_I2CWRITE):  print("I2C-WRITE", end= '')
        elif(self.status == TFL_I2CLENGTH): print("I2C-LENGTH", end= '')
        elif(self.status == TFL_WEAK):      print("Signal weak", end= '')
        elif(self.status == TFL_STRONG):    print("Signal saturation", end= '')
        elif(self.status == TFL_FLOOD):     print("Ambient light saturation", end= '')
        else:                          print("OTHER", end= '')
        print()


    '''
    for i in range(len(cmndData)):
        print(f" {cmndData[i]:0{2}X}", end='')
    print()
    '''

    # # If this module is executed by itself
    # if __name__ == "__main__":
    #     print("tfli2c - This Python module supports the Benewake" +\
    #            " TFLuna Lidar device in I2C mode.")

