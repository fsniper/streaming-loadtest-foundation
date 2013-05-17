"""
Simple HTTP Live Streaming client.

References:
    http://tools.ietf.org/html/draft-pantos-http-live-streaming-08

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://sam.zoy.org/wtfpl/COPYING for more details.

Last updated: July 22, 2012
"""

import urlparse, urllib2, subprocess, os

MEDIAPLAYER=r'C:\Program Files\VideoLAN\VLC\vlc.exe'
if not os.path.exists(MEDIAPLAYER):
    MEDIAPLAYER=r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe'
MEDIAPLAYER="/usr/bin/cvlc"

MEDIAPLAYER_OPTS=['--file-caching=2000']
SUPPORTED_VERSION=3

def download_chunks(URL, chunk_size=4096):
    conn=urllib2.urlopen(URL)
    while 1:
        data=conn.read(chunk_size)
        if not data: return
        yield data

def download_file(URL):
    return ''.join(download_chunks(URL))

def validate_m3u(conn):
    ''' make sure file is an m3u, and returns the encoding to use. '''
    mime = conn.headers.get('Content-Type', '').split(';')[0].lower()
    if mime == 'application/vnd.apple.mpegurl':
        enc = 'utf8'
    elif mime == 'audio/mpegurl':
        enc = 'iso-8859-1'
    elif conn.url.endswith('.m3u8'):
        enc = 'utf8'
    elif conn.url.endswith('.m3u'):
        enc = 'iso-8859-1'
    else:
        raise Exception("Stream MIME type or file extension not recognized")
    if conn.readline().rstrip('\r\n') != '#EXTM3U':
        raise Exception("Stream is not in M3U format")
    return enc

def gen_m3u(url, skip_comments=True):
    conn = urllib2.urlopen(url)
    enc = validate_m3u(conn)
    for line in conn:
        line = line.rstrip('\r\n').decode(enc)
        if not line:
            # blank line
            continue
        elif line.startswith('#EXT'):
            # tag
            yield line
        elif line.startswith('#'):
            # comment
            if skip_comments:
                continue
            else:
                yield line
        else:
            # media file
            yield line

def parse_m3u_tag(line):
    if ':' not in line:
        return line, []
    tag, attribstr = line.split(':', 1)
    attribs = []
    last = 0
    quote = False
    for i,c in enumerate(attribstr+','):
        if c == '"':
            quote = not quote
        if quote:
            continue
        if c == ',':
            attribs.append(attribstr[last:i])
            last = i+1
    return tag, attribs

def parse_kv(attribs, known_keys=None):
    d = {}
    for item in attribs:
        k, v = item.split('=', 1)
        k=k.strip()
        v=v.strip().strip('"')
        if known_keys is not None and k not in known_keys:
            raise ValueError("unknown attribute %s"%k)
        d[k] = v
    return d

def handle_basic_m3u(url):
    seq = 1
    enc = None
    nextlen = 5
    duration = 5
    for line in gen_m3u(url):
        if line.startswith('#EXT'):
            tag, attribs = parse_m3u_tag(line)
            if tag == '#EXTINF':
                duration = float(attribs[0])
            elif tag == '#EXT-X-TARGETDURATION':
                assert len(attribs) == 1, "too many attribs in EXT-X-TARGETDURATION"
                targetduration = int(attribs[0])
                pass
            elif tag == '#EXT-X-MEDIA-SEQUENCE':
                assert len(attribs) == 1, "too many attribs in EXT-X-MEDIA-SEQUENCE"
                seq = int(attribs[0])
            elif tag == '#EXT-X-KEY':
                attribs = parse_kv(attribs, ('METHOD', 'URI', 'IV'))
                assert 'METHOD' in attribs, 'expected METHOD in EXT-X-KEY'
                if attribs['METHOD'] == 'NONE':
                    assert 'URI' not in attribs, 'EXT-X-KEY: METHOD=NONE, but URI found'
                    assert 'IV' not in attribs, 'EXT-X-KEY: METHOD=NONE, but IV found'
                    enc = None
                elif attribs['METHOD'] == 'AES-128':
                    assert 'URI' in attribs, 'EXT-X-KEY: METHOD=AES-128, but no URI found'
                    from Crypto.Cipher import AES
                    key = download_file(attribs['URI'].strip('"'))
                    assert len(key) == 16, 'EXT-X-KEY: downloaded key file has bad length'
                    if 'IV' in attribs:
                        assert attribs['IV'].lower().startswith('0x'), 'EXT-X-KEY: IV attribute has bad format'
                        iv = attribs['IV'][2:].zfill(32).decode('hex')
                        assert len(iv) == 16, 'EXT-X-KEY: IV attribute has bad length'
                    else:
                        iv = '\0'*8 + struct.pack('>Q', seq)
                    enc = AES.new(key, AES.MODE_CBC, iv)
                else:
                    assert False, 'EXT-X-KEY: METHOD=%s unknown'%attribs['METHOD']
            elif tag == '#EXT-X-PROGRAM-DATE-TIME':
                assert len(attribs) == 1, "too many attribs in EXT-X-PROGRAM-DATE-TIME"
                # TODO parse attribs[0] as ISO8601 date/time
                pass
            elif tag == '#EXT-X-ALLOW-CACHE':
                # XXX deliberately ignore
                pass
            elif tag == '#EXT-X-ENDLIST':
                assert not attribs
                yield None
                return
            elif tag == '#EXT-X-STREAM-INF':
                raise ValueError("don't know how to handle EXT-X-STREAM-INF in basic playlist")
            elif tag == '#EXT-X-DISCONTINUITY':
                assert not attribs
                print "[warn] discontinuity in stream"
            elif tag == '#EXT-X-VERSION':
                assert len(attribs) == 1
                if int(attribs[0]) > SUPPORTED_VERSION:
                    print "[warn] file version %s exceeds supported version %d; some things might be broken"%(attribs[0], SUPPORTED_VERSION)
            else:
                raise ValueError("tag %s not known"%tag)
        else:
            yield (seq, enc, duration, targetduration, line)
            seq += 1

def player_pipe(proc, queue, control):
    while 1:
        block = queue.get(block=True)
        if block is None: return
        proc.stdin.write(block)

def main():
    import sys, threading, time, Queue
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        #print "usage", sys.argv[0], "<stream URL> [dumpfile]"
        #sys.exit(1)
        sys.argv.append(raw_input("Stream URL? "))
        sys.argv.append(raw_input("Dump filename (blank to ignore)? "))

    url = sys.argv[1]
    if len(sys.argv) == 3 and sys.argv[2]:
        dumpfile = open(sys.argv[2], "wb")
    else:
        dumpfile = None
    variants = []
    variant = None
    for line in gen_m3u(url):
        if line.startswith('#EXT'):
            tag, attribs = parse_m3u_tag(line)
            if tag == '#EXT-X-STREAM-INF':
                variant = attribs
        elif variant:
            variants.append((line, variant))
            variant = None
    if len(variants) == 1:
        url = urlparse.urljoin(url, variants[0][0])
    elif len(variants) >= 2:
        print "More than one variant of the stream was provided."
        print "Select desired stream below."
        for i, (vurl, vattrs) in enumerate(variants):
            print i, vurl,
            for attr in vattrs:
                key, value = attr.split('=')
                key = key.strip()
                value = value.strip().strip('"')
                if key == 'BANDWIDTH':
                    print 'bitrate %.2f kbps'%(int(value)/1024.0),
                elif key == 'PROGRAM-ID':
                    print 'program %s'%value,
                elif key == 'CODECS':
                    print 'codec %s'%value,
                elif key == 'RESOLUTION':
                    print 'resolution %s'%value,
                else:
                    raise ValueError("unknown STREAM-INF attribute %s"%key)
            print
        choice = int(raw_input("Selection? "))
        url = urlparse.urljoin(url, variants[choice][0])

    proc = subprocess.Popen([MEDIAPLAYER]+MEDIAPLAYER_OPTS+['-'], stdin=subprocess.PIPE)
    queue = Queue.Queue(1024) # 1024 blocks of 4K each ~ 4MB buffer
    control = ['go']
    thread = threading.Thread(target=player_pipe, args=(proc, queue, control))
    thread.start()
    last_seq = -1
    targetduration = 5
    changed = 0
    try:
        while thread.isAlive():
            medialist = list(handle_basic_m3u(url))
            if None in medialist:
                # choose to start playback at the start, since this is a VOD stream
                pass
            else:
                # choose to start playback three files from the end, since this is a live stream
                medialist = medialist[-3:]
            for media in medialist:
                if media is None:
                    queue.put(None, block=True)
                    return
                seq, enc, duration, targetduration, media_url = media
                if seq > last_seq:
                    for chunk in download_chunks(urlparse.urljoin(url, media_url)):
                        if enc: chunk = enc.decrypt(chunk)
                        if dumpfile: dumpfile.write(chunk)
                        queue.put(chunk, block=True)
                    last_seq = seq
                    changed = 1
            if changed == 1:
                # initial minimum reload delay
                time.sleep(duration)
            elif changed == 0:
                # first attempt
                time.sleep(targetduration*0.5)
            elif changed == -1:
                # second attempt
                time.sleep(targetduration*1.5)
            else:
                # third attempt and beyond
                time.sleep(targetduration*3.0)
            changed -= 1
    except:
        control[0] = 'stop'
        raise

if __name__ == '__main__':
    main()
