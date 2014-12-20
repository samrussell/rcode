#!/usr/bin/python

import math
import pprint
import numpy

def makegaloisfield(fieldsize, generator):

  # generate tables

  #generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
  #fieldsize = 256

  table = [[0 for y in range(fieldsize)] for x in range(fieldsize)]

  for a in range(fieldsize):
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
    
    for b in range(fieldsize):
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

  inverses = [0 for x in range(fieldsize)]

  for a in range(fieldsize):
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

class GFnum:

  def __init__(self, num, gf):
    self.num = num
    self.gf = gf

  def __add__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return self.num ^ other
  def __sub__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return self.num ^ other
  def __mul__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    return self.gf.table[self.number][other]
  def __div__(self, other):
    if isinstance(other, GFnum):
      other = other.num
    otherinverse = self.gf.inverses[other]
    return self.gf.table[self.number][otherinverse]
  def __repr__(self):
    return str(self.num)

def main():
  # just generate stuff and print
  generator = 0b100011011 # x^8 + x^4 + x^3 + x + 1 = 100011011
  fieldsize = 256
  gf256 = makegaloisfield(fieldsize, generator)

  print gf256["table"]
  print gf256["inverses"]

if __name__ == "__main__":
  main()

