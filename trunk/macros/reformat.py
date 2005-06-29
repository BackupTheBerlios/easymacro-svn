from datetime import *
from StringIO import StringIO
import os, re, sys, time

import emacro

RIGHT_MARGIN = 72


# TODO: reformat email quoting

# reformat WESTERN-EUROPEAN text into paragraphs under RIGHT_MARGIN

def p(s):
    sys.stdout.write(s)


def find_margin(fp):
    """ Look into the first 2 lines of the data to determine the format.
        Find the left margin of first line and second line. (Default 0)
        Find the prefix marker 
            (either'//' or '#' possibly with a trailing space.)
    """
    marker0, marker1 = '',''
    margin0, margin1 = '',''
    try:
        # first line
        line = fp.next().rstrip()
        margin0 = line[:len(line)-len(line.lstrip())]
        margin1 = margin0
        marker0 = line.lstrip()[:3]
        marker1 = marker0
        # second line
        line = fp.next().rstrip()
        margin1 = line[:len(line)-len(line.lstrip())]
        marker1 = line.lstrip()[:3]
    except StopIteration:
        pass
        
    if marker0.startswith('//') and marker1.startswith('//'):
        marker = marker0[2:3].isspace() and marker0[:3] or marker0[:2]
    elif marker0.startswith('#') and marker1.startswith('#'):
        marker = marker0[1:2].isspace() and marker0[:2] or marker0[:1]
    else:
        marker = ''    
        
    fp.seek(0)
    return margin0, margin1, marker
    
    
def gen_word(fp, marker):
    marker = marker.strip()
    for line in fp:
        line = line.strip()
        if not line:
            yield '\n'
        if line.startswith(marker):
            line = line[len(marker):].lstrip()    
        words = line.split()
        for word in words:
            yield word


def editLines(fp):
    margin0, margin1, marker = find_margin(fp)
    pad0 = margin0+marker
    pad1 = margin1+marker
    print >>sys.stderr, len(margin0), len(margin1), 'm[%s]' % marker
    
    p(pad0)
    cursor = len(pad0)
    newline = True
        
    for word in gen_word(fp, marker):
        # a paragraph break?
        if word == '\n':
            p('\n\n')
            p(pad0)
            cursor = len(pad0)
            newline = True
            continue
        # flow into next line?
        if not newline and cursor + 1 + len(word) > RIGHT_MARGIN:
            p('\n')
            p(pad1)
            cursor = len(pad1)
            newline = True
        # continue on the same line
        if not newline:
            p(' ')
            cursor += 1
        p(word)
        cursor += len(word)
        newline = False

    if not newline:
        p('\n')
