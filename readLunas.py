from tca9548a import TCA9548A
from smbus2 import SMBus
import sys, time
from TFLuna import TFLuna


tcaAddress = 0x70 #default TCA9548A address
i2cBus = SMBus(1)
tca = TCA9548A(i2cBus = i2cBus, address = tcaAddress)
bus0 = tca.getChannel(0)
bus1 = tca.getChannel(1)
bus2 = tca.getChannel(2)
bus3 = tca.getChannel(3)
bus4 = tca.getChannel(4)
bus5 = tca.getChannel(5)
bus6 = tca.getChannel(6)
bus7 = tca.getChannel(7)
buses = [bus0, bus1, bus2, bus3, bus4, bus5, bus6, bus7]

tfl0 = TFLuna(bus0, 0)
tfl1 = TFLuna(bus1, 1)
tfl2 = TFLuna(bus2, 2)
tfl3 = TFLuna(bus3, 3)
tfl4 = TFLuna(bus4, 4)
tfl5 = TFLuna(bus5, 5)
tfl6 = TFLuna(bus6, 6)
tfl7 = TFLuna(bus7, 7)
tfls = [tfl0, tfl1, tfl2, tfl3, tfl4, tfl5, tfl6, tfl7]


#                         FRONT
#
#              ___tfl0______________tfl1___
#             |                           |
#             |                           |
#           tfl7            .            tfl2
#             |           .:::.           |
#             |         .:::::::.         |
#  LEFT       |            :::            |       RIGHT
#             |            :::            |
#             |            :::            |
#           tfl6                         tfl3
#             |                           | 
#             |__tfl5_______________tfl4__| 
# 
# 
#                         BACK


def continuousTrigger():
    tfAttempt = 0
    while tfAttempt < 3:
        try:
            while True:
                time.sleep(0.47)   # Add 47ms delay for 20Hz loop-rate
                printDistances()
        except KeyboardInterrupt:
            print('Keyboard Interrupt')
            break
        except:
            print(sys.exc_info())
            tfAttempt += 1
            print("Attempts: " + str(tfAttempt))
            time.sleep(2.0)

def printDistances():
    for tfl in tfls:
        if tfl.init:
            if tfl.getData():
                # print(f"{tfl.channel} : {tfl.dist:{4}}cm")
                print(f"{tfl.channel} : {tfl.dist:{4}}cm | Flux:{tfl.flux:{6}d} | Temp:{tfl.temp:{3}}°C")
            else:
                print(f"Error on {tfl.channel}")
                tfl.printStatus()
    print('---')

continuousTrigger()