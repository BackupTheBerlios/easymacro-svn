from datetime import *
from StringIO import StringIO
import os, re, sys, time

import emacro

SEPERATOR = ', '

def editText(data):
    text = data.replace('\r\n',' ').replace('\n',' ')
    for i, item in enumerate(text.split(SEPERATOR)):
        if i > 0: print SEPERATOR
        sys.stdout.write(item)

