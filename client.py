#!/usr/bin/python

import socket
import sys
import struct
import gf256
import numpy

def main():
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  address = ('localhost', 8479)

  #message = "1234567890 gary message sausag"
  infile = open('input.bin', 'r')
  message = infile.read()
  infile.close()
  print "Message length: %d" % len(message)

  gf = gf256.GF256(open('gf256.json').read())
  e = gf256.Encoder(gf)
  numpieces = 40
  e.prime(message, numpieces)

  for i in range(numpieces):
    gen = e.generatepacket()
    print "Sending data"  # % gen
    packet = ''.join([chr(x.num) for x in gen.tolist()[0]])
    output = struct.pack("!HHH14s", len(packet), numpieces, len(packet)-numpieces, '') + packet
    # send
    sock.sendto(output, address)


if __name__ == "__main__":
  main()

