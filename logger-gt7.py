import socket
import sys
import struct
import os
import datetime
# pip3 install salsa20
from salsa20 import Salsa20_xor
import os
#https://github.com/Nenkai/PDTools/blob/master/SimulatorInterface/SimulatorInterface.cs
SendDelaySeconds = 10
ReceivePort = 33740
SendPort = 33739
port = ReceivePort
if len(sys.argv) == 2:
    # Get "IP address of Server" and also the "port number" from
    ip = sys.argv[1]
else:
    print("Run like : python3 gt7racedata.py <playstation-ip>")
    exit(1)


###edits


data_type_spec = {
    'FLOAT':{
        'struct_decrypt':'f',
        'bytes':4
    },
    'BYTE':{
        'struct_decrypt':'B',
        'bytes':1
    },
    'INT':{
        'struct_decrypt':'i',
        'bytes':4
    },
    'SHORT':{
        'struct_decrypt':'H',
        'bytes':2
    }
}
packet_data_struct = [
    (0x04,3,"FLOAT","POSITION"),
    (0x10,3,"FLOAT","VELOCITY"),
    (0x1C,3,"FLOAT","ROTATION"),
    (0x28,1,"FLOAT","ROTATION_NORTH"),
    (0x2C,3,"FLOAT","VELOCITY_ANGULAR"),
    (0x38,1,"FLOAT","RIDE_HEIGHT"),
    (0x3C,1,"FLOAT","RPM"),
    (0x40,8,"BYTE","IV"),
    (0x48,1,"FLOAT","UNKNOWN_0x48"),
    (0x4C,1,"FLOAT","SPEED"),
    (0x50,1,"FLOAT","TURBO_BOOST"),
    (0x54,1,"FLOAT","OIL_PRESSURE"),
    (0x58,1,"FLOAT","UNKNOWN_0x58"),
    (0x5C,1,"FLOAT","UNKNOWN_0x58"),
    (0x60,4,"FLOAT","TYRES_TEMP"),
    (0x70,1,"INT","TICK"),
    (0x74,2,"SHORT","LAPS"),
    (0x78,1,"INT","BEST_LAPTIME"),
    (0x7C,1,"INT","LAST_LAPTIME"),
    (0x80,1,"INT","DAYTIME_PROGRESSION"),
    (0x84,2,"SHORT","RACE_POSITION"),
    (0x88,4,"SHORT","ALERTS"),
    (0x8F,1,"BYTE", "GEAR"),
    (0x90,1,"BYTE", "THROTTLE"),
    (0x91,1,"BYTE", "BRAKE"),
    (0x94,4,"FLOAT","WHEELS_SPEED"),
    (0xA4,4,"FLOAT","TYRES_RADIUS"),
    (0xB4,4,"FLOAT","TYRE_SUSPENSION_TRAVEL"),
    (0xC4,4,"FLOAT","UNKNOWN"),
    (0xD4,32,"BYTE","UNKNOWN_RESRVED"),
    (0xF4,1,"FLOAT","CLUCH"),
    (0xF8,1,"FLOAT","CLUCH_ENGAGEMENT"),
    (0xFC,1,"FLOAT","CLUCH_RPM"),
    (0x100,1,"FLOAT","UNKNOWN_GEAR"),
    (0x104,8,"FLOAT","UNKNOWN_GEAR_RATIO"),
    (0x124,1,"INT","CAR_CODE")
]
###
# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = ('0.0.0.0', port)
s.bind(server_address)
s.settimeout(10)
#https://github.com/Nenkai/PDTools/blob/master/PDTools.Crypto/SimulationInterface/SimulatorInterfaceCryptorGT7.cs
def salsa20_dec(dat):
  KEY = b'Simulator Interface Packet GT7 ver 0.0'
  oiv = dat[0x40:0x44]
  iv1 = int.from_bytes(oiv, byteorder='little') # Seed IV is always located there
  iv2 = iv1 ^ 0xDEADBEAF #// Notice DEADBEAF, not DEADBEEF
  """
  print("OIV: %d bytes" % len(oiv))
  print(' '.join(format(x, '02x') for x in oiv))
  print("IV1: %d bytes" % len(iv1.to_bytes(4, 'big')))
  print(' '.join(format(x, '02x') for x in iv1.to_bytes(4, 'big')))
  print("IV2: %d bytes" % len(iv2.to_bytes(4, 'big')))
  print(' '.join(format(x, '02x') for x in iv2.to_bytes(4, 'big')))
  """
  IV = bytearray()
  IV.extend(iv2.to_bytes(4, 'little'))
  IV.extend(iv1.to_bytes(4, 'little'))
  #print("IV: %d bytes" % len(IV))
  #print(' '.join(format(x, '02x') for x in IV))
  """
  // Magic should be "G7S0" when decrypted
  SpanReader sr = new SpanReader(data);
  int magic = sr.ReadInt32();
  if (magic != 0x47375330) // 0S7G - G7S0
  """
  ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])#.decode()
  #check magic number
  magic = int.from_bytes(ddata[0:4], byteorder='little')
  if magic != 0x47375330:
    return bytearray(b'')
  return ddata
def send_hb(s):
  #send HB
  send_data = 'A'
  s.sendto(send_data.encode('utf-8'), (ip, SendPort))
  print('send heartbeat')
send_hb(s)
print("Ctrl+C to exit the program")
pknt = 0


timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace('-', '').replace(':', '')
logpath = f"log/gt7/{timestamp}"

os.makedirs(logpath, exist_ok=True)
lapfn = os.path.join(logpath, 'lap.txt')
lastLap = None
fout = None
lapTime = 0
startTime = None

while True:
  try:
    data, address = s.recvfrom(4096)
    pknt = pknt + 1
    ddata = salsa20_dec(data)
    if len(ddata) > 0:
      #https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketGT7.cs
      #RPM: 15th 4byte ints
        packet_data = {}
        for start, size, type, name in packet_data_struct:
            end = start + size * (data_type_spec[type]['bytes'])
            unpacker=data_type_spec[type]['struct_decrypt'] * size
            data_decrypted= struct.unpack(unpacker, ddata[start:end])
            packet_data[name]= data_decrypted
    #Here we can print as user friendly

    speed = float(packet_data["SPEED"][0])*2.25
    x, y, z = packet_data["POSITION"]
    rpm = packet_data["RPM"][0]
    lap = packet_data["LAPS"][0]
    dayTime = packet_data["DAYTIME_PROGRESSION"][0]
    gas = packet_data["THROTTLE"][0]
    brake = packet_data["BRAKE"][0]
    gear = packet_data["GEAR"][0] >> 4

    if pknt > 100:
      send_hb(s)
      pknt = 0


    if lastLap != lap:

        print(f"starting lap {lap}")

        if fout:
            fout.flush()
            fout.close()

        # open a new logger file

        fout = open(os.path.join(logpath, f'lap-{lap}.txt'), "w")
        header = ['lapTime', 'speed_Mph', 'gas', 'brake', 'steer', 'gear', 'x', 'y', 'z']
        fout.write( "\t".join(header) + "\n")

        # clear the lap
        startTime = dayTime
        lastLap = lap


    if fout:
        lapTime = dayTime - startTime
        data = [ str(lapTime), str(speed), str(gas), str(brake), str(0), str(gear), str(x), str(y), str(z)]
        fout.write( "\t".join(data) + "\n")
        fout.flush()

  except Exception as e:
    print(e)
    send_hb(s)
    pknt = 0
    if fout:
        fout.close()
    pass