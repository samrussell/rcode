#!/usr/bin/python

import socket
import sys
import struct
import gf256
import numpy

messages = []
gf = gf256.GF256(open('gf256.json').read())

def main():
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  address = ('localhost', 8479)
  sock.bind(address)

  while True:
    data, addr = sock.recvfrom(1500)
    parsemessage(data)

def parsemessage(data):

  # parse message
  print "receved packet length %d" % len(data)
  print "packet number %d" % (len(messages)+1)
  if len(data) < 20:
    print "packet too short!"
    return
  # first 2 bytes is packet length
  (length, numpieces, numdata) = struct.unpack("!HHH", data[:6])
  headerlength = 20
  # sanity check - if packet length != payload + header then fail
  # this is vulnerable to wrap-around attacks
  if headerlength + length != len(data):
    print "header length + payload length don't add up!"
    return
  # make sure payload is equal to the length of the solver bits
  # plus the length of the data clues
  if 4 + numdata != length:
    print "4 + data != payload length!"
    return
  # pull everything off the end in that case
  inrow = data[20:20+length]
  # treat as byte array
  data = [ord(x) for x in inrow[:4]] + [gf256.GFnum(ord(x), gf) for x in inrow[4:]]
  #print data
  messages.append(data)
  if len(messages) >= numpieces:
    # try to decode
    print "decoding..."
    d = gf256.Decoder(gf)
    output = d.decode(messages, numpieces)
    #print output[:20]
    # write output to file
    outfile = open('output.bin', 'w')
    outfile.write(output)
    outfile.close()
    print "done"


if __name__ == "__main__":
  main()

