import base64
import emacro

def editText(text):
    data = base64.decodestring(text)
    
    # assume it is utf-8 encoded text.
    print data.decode('utf-8','replace').encode('latin-1','replace')
    
    # if it is binary, it is better to use Python string_escape codec.
    #print data.encode('string_escape'),
