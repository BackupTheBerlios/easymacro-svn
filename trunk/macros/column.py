from datetime import *
from StringIO import StringIO
import os, re, sys, time

import emacro

#SEPERATOR = '( *)\|'
SEPERATOR = '( *)='
pattern = re.compile(SEPERATOR)

def _p(s):
    sys.stdout.write(s)
    
def gen_parts(s, rx):
    cur = 0
    for m in rx.finditer(s): 
        try:
            end = m.end(1)
        except IndexError:
            end = m.end()
        yield s[cur:end]
        cur = end
    yield s[cur:]
    
    
def editLines(fp):
    # pass 1: find the maximum length for every column
    maxcol = [0] * 1000 # HACK
    for line in fp:
        for i, part in enumerate(gen_parts(line,pattern)):
            part = part.strip()
            if maxcol[i] < len(part):
                maxcol[i] = len(part)
               
    fp.seek(0)      

    # pass 2: format the columns according to maxcol
    for line in fp:
        for i, part in enumerate(gen_parts(line,pattern)):
            part = part.strip()
            _p(part.ljust(maxcol[i]))
        _p('\n')







