* streamtest:
    This is a port of live555 source code to be used as a raw data grabber from rtsp stream requests
* analyze.py:
    This is a processor for the output of streamtest. To generate some level of data and plot data file.
* hlsclient.py:
    Preliminary hls request file. It's not ready yet. But will be processed to give same or alike raw data as the streamtest.


To conduct a test you should first compile live555 source code with these steps:
    cd streamtest/loadtestwork
    ./genMakefiles linux
    make

After the compile you will have a binary called loadtest in the streamtest/loadtestwork/testProgs directory.
This binary is a simple binary just making a rtsp request to the rtsp url provided as the first parameter.
It will stream the url and dump the received data into the void and give insightfull data about the bandwidth
usage of the every data burst. To analyze the data the output should be redirected to a file via shell redirection
like:

    ./loadtest <url> 2>&1 > url.loadtest.raw.data

Then looking and analyzing this raw.data you may gather information about the bandwidth usage of the streaming.
A few lines from a raw data is as follows:


    success 0
    1367487360635475.000000 :: data 652b bw 0.000000kb/s avg 17.051465kb/s
    1367487360635517.000000 :: data 168b bw 31250.000000kb/s avg 21.442079kb/s
    1367487360635577.000000 :: data 26b bw 3385.416667kb/s avg 22.117508kb/s
    1367487360736042.000000 :: data 9b bw 0.699871kb/s avg 16.728703kb/s
    1367487360736090.000000 :: data 9b bw 1464.843750kb/s avg 16.902763kb/s
    1367487360736129.000000 :: data 3038b bw 608573.717949kb/s avg 76.328866kb/s
    1367487360736159.000000 :: data 9b bw 2343.750000kb/s avg 76.499173kb/s
    .....

    1367488109239567.000000 :: data 12460b bw 1008.586748kb/s avg 1595.762013kb/s
    1367488109239653.000000 :: data 10652b bw 967659.883721kb/s avg 1595.872951kb/s
    1367488109240014.000000 :: data 458b bw 9911.703601kb/s avg 1595.876960kb/s
    1367488109240037.000000 :: data 447b bw 151834.239130kb/s avg 1595.881574kb/s
    1367488109240177.000000 :: data 465b bw 25948.660714kb/s avg 1595.886126kb/s
    1367488109240201.000000 :: data 468b bw 152343.750000kb/s avg 1595.890957kb/s
    1367488109240223.000000 :: data 443b bw 157315.340909kb/s avg 1595.895532kb/s
    success 10
    elapsed time 7.4895e+08



The rows are in order: Timestamp :: data bytes <received bytes for the burst> bw <bursts approximate bw> avg <average bandwidth>

As it's seen with the data, from the start average bandwidth used is very low figures and increases to the level of kbits/s rate
of the stream like 1600kbit/s at the end. This means this user has no any glitches because she has enough and constant bw.

After dumping this data to a file you may get some insightful data from it with the analyze.py script. Well raw data is in itself
really insightfull but very huge. So it may be hard to analyze it by hand.

Sample usage of the analyze.py:


```
python analyze.py ../vps433/logs/log.vps433.vpshispeed.com.test\:test1-userspervm\:75.testno\:75.log
../vps433/logs/data/log.vps433.vpshispeed.com.test:test1-userspervm:75.testno:75.log
Package count: 248650 minbyte: 9 maxbyte: 99971 averagebyte: 2896 totalbyte: 720122724

Problem count: 0
```

These figures are self explanatory but lets go over them:
The first line of the output is a plot data file which you may create a graphics with gnuplot.
The second line gives information about data bursts count, min, max and average sizes of them and the total data size received.

The scripts creates a buffer of 2mb and assumpts the client consumes from the buffer constantly to view or listen to the streaming.
So it prints out if any under buffer situations accour. In a normal client whenever the buffer is full the client would stop receiving data
and resume whenever the buffer is freed. But this script just adds up the overflowing to the next burst data as it is received in the next burst.
And looking into buffer figures prints out how many times the buffer is consumed faster than the data received.

For graphics. You may use the plot.file and gnuplot to create a png of the figures. From the file generated with analyze.py as follows:

Fist edit the last two lines of the plot.file with the output png path and the input log file.


```
gnuplot plotfile
```


After this command you will have a fancy graphics with the bursts as lines.

Sources:

* live555: http://www.live555.com/
* hlsclient.py: http://nneonneo.blogspot.com/2010/08/http-live-streaming-client.html
* analyze.py is supplied as is from Parkyeri.
