from datetime import *
from StringIO import StringIO
import os, re, sys, time

import emacro

def editLines(fp):
    lines = fp.readlines()
    lines.sort()
    sys.stdout.writelines(lines)



