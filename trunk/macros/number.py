from datetime import *
from StringIO import StringIO
import os, re, sys, time

import emacro

def editLines(fp):
    for i, line in enumerate(fp):
        print '%5d %s' % (i+1, line),


