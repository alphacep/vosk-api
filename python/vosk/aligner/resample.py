import os
import shutil
import subprocess
import tempfile

from contextlib import contextmanager
from .util.paths import get_binary

FFMPEG = get_binary("ffmpeg")
SOX = get_binary("sox")

def resample_ffmpeg(infile, outfile, offset=None, duration=None):
    '''
    Use FFMPEG to convert a media file to a wav file sampled at 8K
    '''
    if offset is None:
        offset = []
    else:
        offset = ['-ss', str(offset)]
    if duration is None:
        duration = []
    else:
        duration = ['-t', str(duration)]

    cmd = [
        FFMPEG,
        '-loglevel', 'panic',
        '-y',
    ] + offset + [
        '-i', infile,
    ] + duration + [
        '-ac', '1', '-ar', '8000',
        '-acodec', 'pcm_s16le',
        outfile
    ]
    return subprocess.call(cmd)

def resample_sox(infile, outfile, offset=None, duration=None):
    '''
    Use SoX to convert a media file to a wav file sampled at 8K
    '''
    if offset is None and duration is None:
        trim = []
    else:
        if offset is None:
            offset = 0
        trim = ['trim', str(offset)]
        if duration is not None:
            trim += [str(duration)]

    cmd = [
        SOX,
        '--clobber',
        '-q',
        '-V1',
        infile,
        '-b', '16',
        '-c', '1',
        '-e', 'signed-integer',
        '-r', '8000',
        '-L',
        outfile
    ] + trim
    return subprocess.call(cmd)

def resample(infile, outfile, offset=None, duration=None):
    if not os.path.isfile(infile):
        raise IOError("Not a file: %s" % infile)
    if shutil.which(FFMPEG):
        return resample_ffmpeg(infile, outfile, offset, duration)
    else:
        return resample_sox(infile, outfile, offset, duration)

@contextmanager
def resampled(infile, offset=None, duration=None):
    with tempfile.NamedTemporaryFile(suffix='.wav') as fp:
        if resample(infile, fp.name, offset, duration) != 0:
            raise RuntimeError("Unable to resample/encode '%s'" % infile)
        yield fp.name
