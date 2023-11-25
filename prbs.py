#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
taps = {    'prbs7'   : (2,1),
            'prbs127' : (5,6),
            'prbs511' : (4,8),
            'prbs1023': (6,9)}

def getNextSeq(length:int, fb:list, seq:int) -> tuple[int, int]:
    '''
    Inputs:
        length: int # length of the
        fb: list of ints # which bits in the sequence to xor
        seq: int # current bit sequence
    Outputs:
        next: int # next bit sequence
        output: int # output (LSB)
    '''

    for j in range(len(fb)):
        if j == 0:
            xor = (seq >> fb[j]) & 1
        else:
            xor ^= (seq >> fb[j]) & 1

    next = (seq << 1)
    if xor:
        next |= 1
    else:
        next &= ~(0)

    zeros = 0
    for i in range(length):
        zeros += (1 << i)

    next &= zeros

    output = (seq >> (length-1)) & 1

    return next, output


def PRBS(length:int, phase:int, seed:int=1) -> list[int]:
    '''
    Inputs:
        length: int # Represents number of bits for the PRBS
        phase: int # Represents how delayed the PRBS sequence is
        seed: int # Start of sequence
    Outpus:
        sequence: list of ints # list of bit numbers from the generated PRBS
    '''

    if length == 2:
        fb = [0,1]
    elif length == 3:
        fb = [1,2]
    elif length == 4:
        fb = [2,3]
    elif length == 5:
        fb = [2,4]
    elif length == 6:
        fb = [4,5]
    elif length == 7:
        fb = [5,6]
    elif length == 8:
        fb = [3,4,5,7]
    elif length == 9:
        fb = [4,8]
    elif length == 10:
        fb = [6,9]
    elif length == 11:
        fb = [8,10]
    elif length == 12:
        fb = [3,9,10,11]
    elif length == 13:
        fb = [7,10,11,12]
    elif length == 14:
        fb = [1,11,12,13]
    elif length == 15:
        fb = [13,14]
    elif length == 16:
        fb = [3,12,14,15]

    start = seed

    for i in range(phase):
        start, temp = getNextSeq(length, fb, start)

    sequence = []
    seq = start

    for i in range(2**length-1):
        seq, output = getNextSeq(length, fb, seq)

        sequence.append(output)

    return sequence


def autocorrelation(seq:list[int], n:int) -> int:
    '''
    Inputs:
        seq: list of ints # the bit sequence
        n: int # Shift when determining autocorrelation
    Outputs:
        auto: int # the autocorrelation
    '''

    N = len(seq)
    auto = 0

    for i in range(N):
        auto += seq[i] * seq[(i-n) % N]

    return auto


def xcorr(signal:list[float], seq:list[int]) -> list[float]:
    '''
    Inputs:
        signal: list of floats # recorded signal
        seq: list of ints # corresponding sequence
    Outpus:
        x = list of floats # cross-correlation results
    '''

    N = len(seq)
    x = []

    for i in range(len(seq)):
        sum = 0

        for j in range(len(seq)):
            sum += signal[j] * seq[(j-i) % N]

        x.append(sum)

    return x

# generate PRBS bit sequence
def generate_prbs(seed=0b1, prbsType='prbs7'):
    output = []

    shiftReg = seed
    # print(shiftReg)
    bitlen = 0
    mask = 0
    if prbsType=='prbs7':
        bitlen = 3
        mask = 0b111
    if prbsType=='prbs127':
        bitlen=7
        mask = 0b1111111
    if prbsType=='prbs511':
        bitlen = 9
        mask = 0b111111111
    if prbsType=='prbs1023':
        bitlen= 10
        mask = 0b1111111111

    # print(prbsType)
    for x in range(2**bitlen - 1):
        msb = (shiftReg >> (bitlen-1)) & 0x1 # grab MSB
        # print(msb)
        output.append(msb) # append MSB as output
        xor = ((shiftReg >> taps[prbsType][0]) & 0x1) ^ ((shiftReg >> taps[prbsType][1]) & 0x1) # grab tapped bits to xor
        shiftReg = (shiftReg << 1) | xor # shift left and append xor bit
        shiftReg &= mask # mask to maintain fixed bit length size

    # print(shiftReg == seed)
    return output


if __name__ == '__main__':
    length = 3
    phase = 0

    sequence = PRBS(length, phase)
    print(sequence)