#!/usr/bin/env python

"""
    Copyright parkyeri
    Author: Onur YALAZI yalazi@parkyeri.com

    Simple script to basic analyze raw data provided from loadtest of rtsp clients

"""
import sys
import os

logfile = sys.argv[1]
datadir = os.path.dirname(logfile) + "/data"
datafile = datadir + "/" + os.path.basename(logfile)

print datafile

bitrate= 320 * 8                    # bitrate of the video
buffersize = 2 * 1024 * 1024 * 8    # 2M in bits
buffer = 0

skippedbytes = 0
lasttime = 0
try:
    os.mkdir(datadir)
except:
    pass

def calculate_buffer(time, byte):
    global buffer
    global problemcount
    global skippedbytes

    if time == 0:
        diff = 0
        consumed = 0
    else:
        diff = time - lasttime
        consumed = byte / bitrate

    buffer = buffer + byte + skippedbytes - consumed
    skippedbytes = 0

    if buffer >  buffersize:
        skippedbytes = buffer - buffersize
        buffer = buffersize

    problem = False
    if buffer == 0:
        problem = True
        problemcount += 1

    return (problem, skippedbytes)

log = open(logfile, "r")
plotdata = open("%s" % (datafile,), "w")

packages = 0

totalbyte = 0
minbyte = 1000000
maxbyte = 0
averagebyte = 0

mintime = 1000000000
maxtime = 0
averagetime = 0

buferrortime = 0
problemcount = 0

firstline = log.readline()
for line in log:
    data = line.split()

    if data[0] in ['success', 'elapsed', "MultiFramedRTPSource::doGetNextFrame1():"] :
        continue

    try:
        time = float(data[0])
        byte = int(data[3].replace('b', ''))
    except:
        continue

    bd = calculate_buffer(time, byte)

    packages += 1
    totalbyte += byte

    mintime = min(mintime, time)
    maxtime = max(maxtime, time)

    minbyte = min(minbyte, byte)
    maxbyte = max(maxbyte, byte)

    plotdata.write("%s %d %d\n" % (time, byte, buffer))

averagebyte = totalbyte / packages

print "Package count: %d minbyte: %d maxbyte: %d averagebyte: %d totalbyte: %d\n" % (packages, minbyte, maxbyte, averagebyte, totalbyte )
print "Problem count: %d\n" % (problemcount,)
