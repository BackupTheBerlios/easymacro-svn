"""Usage: python emacro.py edit_module args
"""

# emacro.py                         select script to run 
# emacro.py -e|--edit               invoke to edit scripts   

# emacro.py edit_module             invoke the module to edit the input stream
# emacro.py -c|--clip edit_module   invoke the module to edit the clipboard

import fnmatch
from optparse import *
from StringIO import StringIO
import os.path
import sys
import traceback

# import win32 extension to access clipboard
try:
  import win32clipboard
  import win32con
except:
  pass  


########################################################################
# Windows clipboard

def _getWinClipboardText(): 
    """ Get text from win32 clipboard """
    win32clipboard.OpenClipboard() 
    try:
#       d=win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) 
        d=win32clipboard.GetClipboardData(win32con.CF_TEXT) 
    except TypeError:
        # format not available?
        d=''
    win32clipboard.CloseClipboard() 
    
    # 2005-05-25: hack! Why GetClipboardData() return data with null character???
    # truncate anything after \0
    try: d = d[:d.index(chr(0))]    
    except ValueError: pass
    
    return d 
 
 
#def setWinClipboardText(aString, aType=win32con.CF_UNICODETEXT): 
def _setWinClipboardText(aString, aType=win32con.CF_TEXT): 
    """ Paste text into win32 clipboard """
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    
#    n=win32clipboard.RegisterClipboardFormat('EmSoftBoxSelectW')
#    print >>sys.stderr, '--',n, win32clipboard.GetClipboardFormatName(n)
    
#    win32clipboard.SetClipboardData(n,aString) 
    win32clipboard.SetClipboardData(aType,aString) 
    win32clipboard.CloseClipboard() 


getClipboardText = _getWinClipboardText
setClipboardText = _setWinClipboardText


class ClipboardWriter(object):
    """ File like object to collect output to clipboard """
    def __init__(self):
        self.buf = StringIO()
        
    def write(self, s):
        self.buf.write(s)    
        
    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def setClipboard(self):
        setClipboardText(self.buf.getvalue())


def getLineBreak(line):
    if line[-2:] == '\r\n': 
        return '\r\n'
    elif line[-1:] in ['\r', '\n']:
        return line[-1:]
    else:
        return ''    


########################################################################
# Macros directory

DEF_MACROSPATH = 'macros'
macros_path = DEF_MACROSPATH    # should be relative to this script directory
base_path = '.'


def init_macropath():
    global base_path, macros_path
    m = sys.modules['__main__']
    if hasattr(m,'__file__'):
        base_path = os.path.dirname(m.__file__)
        macros_path = os.path.join(base_path, DEF_MACROSPATH)
    else:
        macros_path = os.path.join('.', DEF_MACROSPATH)
        

def listMacro():
    # join '.' so that the base macros path can be substracted easiler later
    base = os.path.join(macros_path,'.')
    
    paths = []
    for dirpath, dirnames, filenames in os.walk(base):
        # remove base portion from dirpath
        dirpath = dirpath[len(base)+1:]
        filenames = fnmatch.filter(filenames, '*.py')
        filenames = [os.path.normpath(os.path.join(dirpath,f)) for f in filenames]
        paths.extend(filenames)
    paths.sort()
    
    return paths
    
    
def getMacroPath(basename):
    # the .py extension in basename is optional
    if not basename.endswith('.py'):
        basename = basename + '.py'
    pathname = os.path.join(macros_path, basename)
    print 'getMacroPath='+pathname
    return pathname


def getMacroTemplate():
    fp = file(os.path.join(base_path,'macro_template.py'))
    try:
        return fp.read()
    finally:
        fp.close()        


########################################################################
# default editing



def myExcepthook(type, value, tb):
    out = StringIO()
    traceback.print_exception(type, value, tb, file=out)
    import Tkinter
    root = Tkinter.Tk() 
    root.withdraw()
    import tkMessageBox
    tkMessageBox.showerror(
            str(type),
            out.getvalue(),
            parent=None
        )
    
        
def edit(code_dict, data):
    if code_dict.has_key('editLine'):
        for line in StringIO(data):
            code_dict['editLine'](line)
            
    elif code_dict.has_key('editLines'):        
        code_dict['editLines'](StringIO(data))
        
    elif code_dict.has_key('editText'):        
        code_dict['editText'](data)
        
    else:
        raise NotImplementedError('Requires one of editLine, editLines or editText')   
    

optparser = OptionParser()
optparser.add_option("-s", "--std", help="Use stdin and stdout instead of clipboard", action='store_true', default=False)
optparser.add_option("-e", "--edit", help="invoke the script editor", action='store_true', default=False)


def stdin_read():
    buf = StringIO()
    for line in sys.stdin:
        buf.write(line)
    return buf.getvalue()
    

def main(argv):
    
    init_macropath()
    sys.path.append(macros_path)
    
    options, args = optparser.parse_args()
    
    if options.edit:
        filename = len(args) > 0 and args[0] or None
        import select_macro
        select_macro.run(filename)
        sys.exit(0)
    
    sys.excepthook = myExcepthook
            
    if len(args) > 0:
        edit_module = args[0]
    else:
        import select_macro
        filename = select_macro.SelectMacro().run()
        if not filename:
            sys.exit(-1)
        if filename.endswith('.py'):
            filename = filename[:-3]
        edit_module = filename.replace(os.sep,'.')
        if not edit_module:
            sys.exit(-1)
            
    mod = __import__(edit_module)
        
    if options.std:
        data = stdin_read()
        edit(mod.__dict__,data)        

    else:
        # data in clipboard
        data = getClipboardText()
        sys.stdout = ClipboardWriter()
        try:
            edit(mod.__dict__,data)
        finally:
            sys.stdout.setClipboard()
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    import emacro
    emacro.main(sys.argv)
