rcode
=====

Sam Russell, December 2014

Rcode is a fountain code that uses linear equations to generate packets. The principles are as follows:

- A message can be represented by an n by l matrix. This can be split into n vectors of length l, and can also be represented as a set of n linear equations. This matrix can be manipulated to produce large numbers of vectors of length l, such that any n of these can be combined, and, using gauss-jordan elimination, the original n by l matrix, and therefore the message, can be reconstructed
- The bytes in the message can be intepreted as members of GF(2^8), ensuring addition and multiplication operations behave correctly due to belonging to a number field

Overhead is introduced by the inclusion of the coefficients with each packet (such that breaking up a message into more than 100 pieces is prohibitive for 1400-byte UDP payloads, giving a theoretical upper bound of 140KB per message.

The code itself is not well optimised, and could run significantly faster were it not written in python, if unnecessary memory copies were removed, and if the packet-generation and message-decoding code was improved to replace the series of operations with single matrix multiplications.

It would be interesting also to look at whether interpreting the message components as members of GF(2^4) instead of GF(2^8) would be useful in reducing overhead, at a risk of increasing the chance of generating linearly dependent vectors.
