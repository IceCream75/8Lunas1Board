import board
import adafruit_tca9548a

i2c = board.I2C()

tca = adafruit_tca9548a.TCA9548A(i2c)
for channel in range(8):
    if tca[channel].try_lock():
        addresses = tca[channel].scan()
        # for address in addresses:
        #     if address !=112:
        #         print("Channel ", channel, " -> ", hex(address))
        print("Channel {}:".format(channel), [hex(address) for address in addresses if address != 0x70])
        tca[channel].unlock()