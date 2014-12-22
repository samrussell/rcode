#!/usr/bin/python

import math
import pprint
import numpy
import random
import os
import json
import struct
import time

def makegaloisfield(fieldsize, generator):

  # generate tables

  #generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
  #fieldsize = 256

  table = [[0 for y in xrange(fieldsize)] for x in xrange(fieldsize)]

  for a in xrange(fieldsize):
    # break up a into its parts
    x = 0
    tempa = a
    parts = []
    while tempa != 0:
      if tempa & 1:
        # add bit to parts
        parts.append(x)
      x = x + 1
      tempa = tempa >> 1
    #print "number %d" % a
    #print parts
    
    for b in xrange(fieldsize):
      if a==0 or b==0:
        table[a][b] = 0
        continue
      # shift b by everything in parts
      shifts = [b << x for x in parts]
      # reduce list
      product = reduce(lambda x, y:x^y, shifts)
      # now divide modulo generator
      # loop while the product is longer (bitwise) than the generator
      while int(math.log(product, 2)) >= int(math.log(generator, 2)):
        generatorlen = int(math.log(generator, 2))
        productlen = int(math.log(product, 2))
        shift = productlen - generatorlen
        shiftedgenerator = generator << shift
        # xor shifted generator against product
        product = product ^ (generator << shift)
      # product is what we want, put into matrix
      table[a][b] = product

  inverses = [0 for x in xrange(fieldsize)]

  for a in xrange(fieldsize):
    if a == 0:
      continue
    inverse = [x for x, y in enumerate(table[a]) if y == 1]
    if len(inverse) != 1:
      raise Exception("inverse of %d is %s?!" % (a, inverse))
    inverses[a] = inverse[0]
  return {"table" : table, "inverses" : inverses}

class GF256:
  
  def __init__(self):
    self.generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
    self.fieldsize = 256
    gf = makegaloisfield(self.fieldsize, self.generator)
    self.table = gf["table"]
    self.inverses = gf["inverses"]

  def __init__(self, data):
    self.generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
    self.fieldsize = 256
    gf = json.loads(data)
    self.table = gf["table"]
    self.inverses = gf["inverses"]

class GFnum:

  def __init__(self, num, gf):
    self.num = num
    self.gf = gf

  def __add__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return GFnum(self.num ^ other, self.gf)
  def __sub__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return GFnum(self.num ^ other, self.gf)
  def __mul__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return GFnum(self.gf.table[self.num][other], self.gf)
  def __div__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    otherinverse = self.gf.inverses[other]
    return GFnum(self.gf.table[self.num][otherinverse], self.gf)
  def __repr__(self):
    return str(self.num)

def make2dgf(a, gf):
  return [[GFnum(ord(y) if isinstance(y, str) else int(y), gf) for y in x] for x in a]

def eliminate(rows, gf):
  # rows is a list of vectors in numpy.matrix
  # start at the top
  for i in xrange(len(rows)):
    # print everything so we know what's happening
    #print "About to work with row %d" % i
    #print rows
    # find the rows that have leading zeros
    candidaterows = set([x for x, y in enumerate(rows)])
    for index, row in enumerate(rows):
      for x in xrange(i):
        if int(row.item(x).num) != 0:
          candidaterows.remove(index)
          break
    # find a row where there's something in column i
    goodrows = [x for x in candidaterows if rows[x].item(i).num != 0]
    if goodrows == None:
      # this means we fail encoding, should throw a fit i guess
      raise Exception("Couldn't decode coefficient %d" % i)
    # start with the highest column and baleet from all the others
    rownum = goodrows[0]
    #print "using row %d" % rownum
    row = rownum
    # divide first item so it's 1 (multiply by inverse)
    value = rows[rownum].item(i)
    inverse = gf.inverses[value.num]
    #print "inverse is %d" % inverse
    rows[rownum] = rows[rownum] * inverse
    # subtract this row from all other rows
    for delnum in xrange(len(rows)):
      if delnum != rownum:
        # find the value of the item at that column
        delvalue = rows[delnum].item(i)
        # multiply to clear it out
        eliminator = rows[rownum] * delvalue
        rows[delnum] = rows[delnum] - eliminator
    #print "decoding, rows:"
    #print rows

  return rows

# this should live inside Decoder i guess
def eliminatev2(rows, gf):
  # rows is a list of vectors in numpy.matrix
  # start at the top
  for i in xrange(len(rows)):
    # print everything so we know what's happening
    #print "About to work with row %d" % i
    #print rows
    # find the rows that have leading zeros
    print "Working with row %d" % (i+1)
    candidaterows = set([x for x, y in enumerate(rows)])
    for index, row in enumerate(rows):
      for x in xrange(i):
        if int(row[x].num) != 0:
          candidaterows.remove(index)
          break
    # find a row where there's something in column i
    goodrows = [x for x in candidaterows if rows[x][i].num != 0]
    if goodrows == None:
      # this means we fail encoding, should throw a fit i guess
      raise Exception("Couldn't decode coefficient %d" % i)
    # start with the highest column and baleet from all the others
    rownum = goodrows[0]
    #print "using row %d" % rownum
    row = rownum
    # divide first item so it's 1 (multiply by inverse)
    value = rows[rownum][i]
    inverse = gf.inverses[value.num]
    #print "inverse is %d" % inverse
    #rows[rownum] = rows[rownum] * inverse
    # do this by hand
    rows[rownum] = [x*inverse for x in rows[rownum]]
    # subtract this row from all other rows
    for delnum in xrange(len(rows)):
      if delnum != rownum:
        # find the value of the item at that column
        delvalue = rows[delnum][i]
        if delvalue.num == 0:
          continue
        # multiply to clear it out
        #eliminator = rows[rownum] * delvalue
        #rows[delnum] = rows[delnum] - eliminator
        # do this by hand
        #eliminator = [x * delvalue for x in rows[rownum]]
        rows[delnum] = [rows[delnum][x] - (rows[rownum][x] * delvalue) for x in xrange(len(rows[delnum]))]
  return rows

class Encoder:

  def __init__(self, gf):
    self.keys = None
    self.numpyrows = None
    self.numpieces = 0
    self.gf = None
    self.length = 0
    self.piecelength = 0
    self.gf = gf

  def prime(self, message, numpieces):
    self.numpieces = numpieces
    # divide message into pieces
    self.length = len(message)
    piecelength = self.length / self.numpieces
    # this length/piece detection is broken, watchout!
    if self.length % self.numpieces > 0:
      piecelength = piecelength + 1
      extrachars = (piecelength * numpieces) - self.length
      # pad for now with ?
      message = message + ''.join(['?' for x in xrange(extrachars)])
    pieces = [message[i*piecelength:i*piecelength+piecelength] for i in xrange(numpieces)]
    # turn into matrix rows
    rows = []
    for i in xrange(numpieces):
      row = [1 if x == i else 0 for x in xrange(numpieces)] + [ord(x) for x in pieces[i]]
      #print len(row)
      rows.append(row)
    self.numpyrows = numpy.matrix(make2dgf(rows, self.gf))
  
  def generatepacket(self):
    seedvals = os.urandom(4)
    seed = struct.unpack("!L", seedvals)[0]
    seedlist = [ord(x) for x in seedvals]
    random.seed(seed)
    key = numpy.matrix([[GFnum(random.randint(2,254), self.gf) for x in xrange(self.numpieces)]])
    message = key * self.numpyrows
    # take off the front and put on the seed
    messageaslist = message.tolist()[0][self.numpieces:]
    messagelist = seedlist + messageaslist
    # also return normal list instead of numpy array (double-copies yay)
    return messagelist

class Encoderv2:

  def __init__(self, gf):
    self.keys = None
    self.numpyrows = None
    self.numpieces = 0
    self.gf = None
    self.length = 0
    self.piecelength = 0
    self.gf = gf

  def prime(self, message, numpieces):
    self.numpieces = numpieces
    # divide message into pieces
    self.length = len(message)
    piecelength = self.length / self.numpieces
    self.piecelength = piecelength
    # this length/piece detection is broken, watchout!
    if self.length % self.numpieces > 0:
      piecelength = piecelength + 1
      extrachars = (piecelength * numpieces) - self.length
      # pad for now with ?
      message = message + ''.join(['?' for x in xrange(extrachars)])
    pieces = [message[i*piecelength:i*piecelength+piecelength] for i in xrange(numpieces)]
    # turn into matrix rows
    rows = []
    for i in xrange(numpieces):
      row = [1 if x == i else 0 for x in xrange(numpieces)] + [ord(x) for x in pieces[i]]
      #print len(row)
      rows.append(row)
    self.rows = rows
    #self.numpyrows = numpy.matrix(make2dgf(rows, self.gf))
  
  def generatepacket(self):
    seedvals = os.urandom(4)
    seed = struct.unpack("!L", seedvals)[0]
    seedlist = [ord(x) for x in seedvals]
    random.seed(seed)
    #key = numpy.matrix([[GFnum(random.randint(2,254), self.gf) for x in xrange(self.numpieces)]])
    key = [random.randint(2,254) for x in xrange(self.numpieces)]
    #message = key * self.numpyrows
    # do the multiplication by hand
    message = []
    for i in xrange(len(self.rows[0])):
      mtotal = 0
      for j in xrange(self.numpieces):
        num = self.rows[j][i]
        keybit = key[j]
        m = self.gf.table[num][keybit]
        mtotal = mtotal ^ m
      message.append(mtotal)
    # cast as GFnum to make things a bit easier for now
    messagegf = [GFnum(x, self.gf) for x in message]
    # take off the front and put on the seed
    messageaslist = messagegf[self.numpieces:]

    messagelist = seedlist + messageaslist
    # also return normal list instead of numpy array (double-copies yay)
    return messagelist

class Decoder:

  def __init__(self, gf):
    self.gf = gf

  def decode(self, messages, numpieces):
    # regenerate coefficients from seed
    rowstodecode = []
    for row in messages:
      seed = (row[0] << 24) + (row[1] << 16) + (row[2] << 8) + row[3]
      random.seed(seed)
      coefs = [GFnum(random.randint(2, 254), self.gf) for x in xrange(numpieces)]
      rowtodecode = numpy.matrix(coefs + row[4:])
      rowstodecode.append(rowtodecode)

    # solve
    rows = eliminate(rowstodecode, self.gf)
    # need to decode
    # test for identity (will code later)
    # assume that it is solved and in correct order
    answers = [x.tolist()[0][numpieces:] for x in rows]
    #print answers
    output = ''.join([''.join([chr(b.num) for b in a]) for a in answers])
    return output
    #print output

class Decoderv2:

  def __init__(self, gf):
    self.gf = gf

  def decode(self, messages, numpieces):
    # regenerate coefficients from seed
    rowstodecode = []
    for row in messages:
      seed = (row[0] << 24) + (row[1] << 16) + (row[2] << 8) + row[3]
      random.seed(seed)
      coefs = [GFnum(random.randint(2, 254), self.gf) for x in xrange(numpieces)]
      rowtodecode = coefs + row[4:]
      rowstodecode.append(rowtodecode)

    # solve
    rows = eliminatev2(rowstodecode, self.gf)
    # need to decode
    # test for identity (will code later)
    # assume that it is solved and in correct order
    answers = [x[numpieces:] for x in rows]
    #print answers
    output = ''.join([''.join([chr(b.num) for b in a]) for a in answers])
    return output
    #print output

def testencode():
  # 80 character string
  plaintext = "big string with lots of characters. i am telling a story about stuff and thingsa"
  # 1170 characters of lorem ipsum
  loremipsum = open('loremipsum.txt').read()
  gf = GF256(open('gf256.json').read())
  print "Encoding"
  t0 = time.clock()
  e = Encoder(gf)
  numpieces = 100
  e.prime(loremipsum, numpieces)
  #e.prime(plaintext, numpieces)
  rows = []
  for i in xrange(numpieces):
    print "Generating piece %d" % (i+1)
    rows.append(e.generatepacket())
  t1 = time.clock()
  print "Time for encode: %fs" % (t1-t0)
  #print rows
  print "Decoding"
  d = Decoder(gf)
  posttext = d.decode(rows, numpieces)
  t2 = time.clock()
  print posttext
  print "Time for decode: %fs" % (t2-t1)

def testencodev2():
  # 80 character string
  plaintext = "big string with lots of characters. i am telling a story about stuff and thingsa"
  # 1170 characters of lorem ipsum
  loremipsum = open('loremipsum.txt').read()
  gf = GF256(open('gf256.json').read())
  print "Encoding (v2)"
  t0 = time.clock()
  e = Encoderv2(gf)
  numpieces = 100
  e.prime(loremipsum, numpieces)
  #e.prime(plaintext, numpieces)
  rows = []
  for i in xrange(numpieces):
    print "Generating piece %d" % (i+1)
    rows.append(e.generatepacket())
  t1 = time.clock()
  print "Time for encode: %fs" % (t1-t0)
  #print rows
  print "Decoding"
  d = Decoderv2(gf)
  posttext = d.decode(rows, numpieces)
  t2 = time.clock()
  print posttext
  print "Time for decode: %fs" % (t2-t1)


def testeliminate():
  gf = GF256(open('gf256.json').read())
  message = numpy.matrix(make2dgf([[1, 0, 0, 0, 'G', 'a', 'r', 'y'], [0, 1, 0, 0, ' ', 'c', 'o', 'd'], [0, 0, 1, 0, 'i', 'n', 'g', ' '], [0, 0, 0, 1, 'F', 'T', 'W', '!']], gf))
  key1 = numpy.matrix([[GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf)]])
  key2 = numpy.matrix([[GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf)]])
  key3 = numpy.matrix([[GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf)]])
  key4 = numpy.matrix([[GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf), GFnum(random.randint(2,254), gf)]])
  m1 = key1 * message
  m2 = key2 * message
  m3 = key3 * message
  m4 = key4 * message
  rows = eliminate([m1, m2, m3, m4], gf)
  print rows

def main():
  # just generate stuff and print
  generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
  fieldsize = 256
  gf256 = makegaloisfield(fieldsize, generator)

  print gf256["table"]
  print gf256["inverses"]

if __name__ == "__main__":
  main()

