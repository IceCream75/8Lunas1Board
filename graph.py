from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import websockets, socket
import re
from tca9548a import TCA9548A
from smbus2 import SMBus
import sys, time
from TFLuna import TFLuna

# Define the port number to use
PORT_NUMBER = 8000

Factor = 3
canvasSize = 2000
Offset = canvasSize/2 # center will be [Offset, Offset]
RobotEdge = 50 * Factor
LunaDistanceFromEdge = RobotEdge * 0.15

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
#           tfl7                          |
#             |             .            tfl2
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

def fetch_data():
    RFL = []
    for tfl in tfls:
        if tfl.init:
            if tfl.getData():
                RFL.append(tfl.dist * Factor)
            else:
                RFL.append(0)
        else:
            RFL.append(0)

    print(RFL)
    for luna in RFL:
        luna = luna * Factor
    return RFL



server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 8000))
server_socket.listen()

client_socket, client_address = server_socket.accept()
while True:
    HTML_PAGE = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Graph</title>
    </head>
    <body>
        <canvas id="graph" width="{canvasSize}" height="{canvasSize}"></canvas>
        <script>
            var canvas = document.getElementById("graph");
            var ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            var lunas = {fetch_data()};
            var offset = {Offset};
            var RobotEdge = {RobotEdge};
            var distFromEdge = {LunaDistanceFromEdge};

            ctx.font = '24px Arial';

            ctx.beginPath();
            ctx.strokeRect(offset - RobotEdge/2, offset - RobotEdge/2, RobotEdge, RobotEdge);
            ctx.strokeStyle = "gray";
            //ctx.stroke();

            var decalage = 5
            ctx.fillText("0", offset-RobotEdge/2+distFromEdge - decalage,   offset-RobotEdge/2 - lunas[0]   + decalage);
            ctx.fillText("1", offset+RobotEdge/2-distFromEdge - decalage,   offset-RobotEdge/2 - lunas[1]   + decalage);
            ctx.fillText("2", offset+RobotEdge/2 + lunas[2] - decalage,     offset-RobotEdge/2+distFromEdge + decalage);
            ctx.fillText("3", offset+RobotEdge/2 + lunas[3] - decalage,     offset+RobotEdge/2-distFromEdge + decalage);
            ctx.fillText("4", offset+RobotEdge/2-distFromEdge - decalage,   offset+RobotEdge/2 + lunas[4]   + decalage);
            ctx.fillText("5", offset-RobotEdge/2+distFromEdge - decalage,   offset+RobotEdge/2 + lunas[5]   + decalage);
            ctx.fillText("6", offset-RobotEdge/2 - lunas[6] - decalage,     offset+RobotEdge/2-distFromEdge + decalage);
            ctx.fillText("7", offset-RobotEdge/2 - lunas[7] - decalage,     offset-RobotEdge/2+distFromEdge + decalage);
            ctx.fillText("^", offset - decalage,     offset + 2*decalage);


            ctx.moveTo(offset-RobotEdge/2+distFromEdge,   offset-RobotEdge/2 - lunas[0]  );
            ctx.lineTo(offset+RobotEdge/2-distFromEdge,   offset-RobotEdge/2 - lunas[1]  );
            ctx.moveTo(offset+RobotEdge/2 + lunas[2],     offset-RobotEdge/2+distFromEdge);
            ctx.lineTo(offset+RobotEdge/2 + lunas[3],     offset+RobotEdge/2-distFromEdge);
            ctx.moveTo(offset+RobotEdge/2-distFromEdge,   offset+RobotEdge/2 + lunas[4]  );
            ctx.lineTo(offset-RobotEdge/2+distFromEdge,   offset+RobotEdge/2 + lunas[5]  );
            ctx.moveTo(offset-RobotEdge/2 - lunas[6],     offset+RobotEdge/2-distFromEdge);
            ctx.lineTo(offset-RobotEdge/2 - lunas[7],     offset-RobotEdge/2+distFromEdge);

            ctx.lineWidth = 3;
            ctx.moveTo(0, 0);
            ctx.lineTo(canvas.width-1, 0);
            ctx.lineTo(canvas.width-1, canvas.heigth-1);
            ctx.lineTo(0, canvas.heigth-1);

            ctx.stroke();
        </script>
    </body>
    </html>
    """
    
    response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + bytes(HTML_PAGE.encode('utf-8'))
    response = response
    client_socket.sendall(response)
    time.sleep(0.1)