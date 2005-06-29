#!/usr/bin/env python
import os
import re
import string
from StringIO import StringIO
import sys 
import traceback

from Tkinter import *
from ScrolledText import ScrolledText
import tkFont   
import tkMessageBox
import tkSimpleDialog

import emacro


root = Tk()
_system_font = tkFont.Font(family="Courier", size=9)
_frame_font = tkFont.Font(family='Helvetica', size=10, weight='bold')
_frame_color = 'white'
_frame_background = 'dark slate blue'
ico_pathname = os.path.join(emacro.base_path, 'pycon.ico')
root.wm_iconbitmap(ico_pathname )

DEFAULT_CODE_TEMPLATE = ''


def show_exc():
    """ show last exception in a message box """
    out = StringIO()
    traceback.print_exc(file=out)
    tkMessageBox.showerror(
            str(type),
            out.getvalue(),
            parent=None
        )

class RedirectOutput(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, write):
        self.write = write
        
    def writelines(self, lines):
        for line in lines:
            self.write(line)


class LabeledFrame(Frame):
    
    """ Frame with a label. """

    def __init__(self, master, label=None):
        Frame.__init__(self, master, bd=2)
        self.label = Label(self, text=label, font=_frame_font, 
            background=_frame_background, foreground=_frame_color)
        self.label.pack(side=TOP, expand=NO, fill=X)

    def setLabel(self, s):
        self.label.configure(text=s)


class ScrolledTextExt(ScrolledText):
    
    """ Extend ScrolledText with convenient methods setText and getText. """
    
    def __init__(self, master=None, **args):
        ScrolledText.__init__(self, master, **args)
        
    def setText(self, text):
        state0 = self['state']
        self['state'] = NORMAL
        try:                
            self.delete('1.0', END)
            self.insert(INSERT, text)
            self.see(END)
        finally:
            self['state'] = state0

    def getText(self):
        return self.get('1.0',END)


class ScriptBox(LabeledFrame):

    def __init__(self, master, variable=None):
        LabeledFrame.__init__(self, master, label='Script')
        self.text = ScrolledTextExt(self, width=100, font=_system_font)
        self.text.pack(fill=BOTH, expand=True)

        
class ClipboardBox(LabeledFrame):

    def __init__(self, master, text=None):
        LabeledFrame.__init__(self, master, label='Clipboard')
        self.text = ScrolledTextExt(self, height=10, font=_system_font)
        self.text.pack(fill=BOTH, expand=True)


class OutputBox(LabeledFrame):

    def __init__(self, master, variable=None):
        LabeledFrame.__init__(self, master, label='Output')
        self.text = ScrolledTextExt(self, height=10, font=_system_font)
        self.text.pack(fill=BOTH, expand=True)
        self.text.tag_config("stderr", foreground="red")
        self.text.configure(state=DISABLED)


class EditMacro(tkSimpleDialog.Dialog):

    def __init__(self, parent, filename): 
        self.filename = filename
        tkSimpleDialog.Dialog.__init__(self,parent,title='EasyMacro - Edit')
        
    def body(self, master):

        self.scriptbox = ScriptBox(master)
        self.scriptbox.pack(side=TOP, expand=True, fill=BOTH)
        
        f1 = Frame(master)
        btn = Button(f1, text='Test', underline=0, command=self.onTest)
        btn.pack(side=LEFT, expand=True, fill=X, ipady=5)
        
        btn = Button(f1, text='Save', underline=0, command=self.onSave)
        btn.pack(side=LEFT, expand=True, fill=X, ipady=5)
        
        btn = Button(f1, text='Revert', underline=0, command=self.onRevert)
        btn.pack(side=LEFT, expand=True, fill=X, ipady=5)
        
        btn = Button(f1, text='Close', underline=2, command=self.cancel)
        btn.pack(side=LEFT, expand=True, fill=X, ipady=5)
        
        f1.pack(side=TOP, fill=X)

        self.inputbox = ClipboardBox(master)
        self.inputbox.pack(side=TOP, expand=True, fill=BOTH)

        self.outputbox = OutputBox(master)
        self.outputbox.pack(side=RIGHT, expand=True, fill=BOTH)

        self.script = self.scriptbox.text
        self.output = self.outputbox.text
        self.input = self.inputbox.text

        self.bind('<Alt-t>', self.onTest)
        self.bind('<Alt-s>', self.onSave)
        self.bind('<Alt-r>', self.onRevert)
        self.bind('<Alt-o>', self.cancel)
        self.script.bind('<FocusIn>', self._setInitPos)

        if self.filename:
            self.open(self.filename)    

        cliptext = emacro.getClipboardText().replace('\r\n','\n')
        if cliptext:
            self.input.setText(cliptext)
            
        self.wm_iconbitmap(ico_pathname)

        self.body = master

        # initial_focus
        return self.script


    def _setInitPos(self, e=None):
        # HACK
        # don't like tkSimpleDialog.Dialog's default geometry.
        # since __init__  calls initial_focus.set_focus() this is 
        # the opportunity to gain control and move the dialog.
        self.geometry('+80+5')
        self.script.unbind('<FocusIn>')
        
        
    def buttonbox(self):
        # we don't use buttonbox(). 
        # However now is a good time to repack the body the way we like it.
        self.body.pack(expand=True, fill=BOTH, padx=0, pady=0)
        
        
    def stdout(self, s):
        self.output.configure(state=NORMAL)
        self.output.insert(END, s)
        self.output.configure(state=DISABLED)
        self.output.see(END)


    def stderr(self, s):
        self.output.configure(state=NORMAL)
        self.output.insert(END, s, 'stderr')
        self.output.configure(state=DISABLED)
        self.output.see(END)


    def onTest(self, event=None):
        code = self.script.getText()
        data = self.input.getText()
        try:
            # redirect output the the output box
            self.output.setText('')
            sys.stdout = RedirectOutput(self.stdout)
            sys.stderr = RedirectOutput(self.stderr)
            
            # load and execute the code
            try:
                ctx = {}
                exec code in ctx
                emacro.edit(ctx, data)
            except Exception, e:
                traceback.print_exc()
                return
        finally:
            sys.stdout = sys.__stdout__    
            sys.stderr = sys.__stderr__ 
            
                
    def open(self, filename):
        try:
            fp = file(emacro.getMacroPath(filename), 'r')
            data = fp.read()
            fp.close()
            self.script.setText(data)
            self.script.yview(0)
            self.scriptbox.setLabel(filename)
        except IOError:
            traceback.print_exc()
            return
   
        
    def onSave(self, event=None):
        try:
            data = self.script.getText()
            fp = file(emacro.getMacroPath(self.filename), 'w')
            fp.write(data)
            fp.close()
        except IOError:
            traceback.print_exc()
            return


    def onRevert(self, event=None):
        self.open(self.filename)


    def onClear(self, event=None):
        self.output.configure(state=NORMAL)
        self.output.delete('1.0', END)
        self.output.configure(state=DISABLED)



class SelectMacro:

    def __init__(self):
        self.filename = None
        #self.master = Frame(root)
        self.master = root
        self.populate()
        
    def populate(self):    
        self.master.title('EasyMacro')
        self.master.geometry('600x400')

        # label and file list
        f1 = Frame(self.master, padx=8, pady=5)
        
        l = 'Select macro at %s' % emacro.macros_path
        lbl = Label(f1, text=l, anchor=W)
        lbl.pack(side=TOP, expand=NO, fill=X, pady=3)
        self.lst = Listbox(f1, height=6)
        self.lst.pack(side=LEFT, expand=YES, fill=BOTH)
        scrollbar = Scrollbar(f1)
        self.lst.configure(yscrollcommand=(scrollbar, 'set'))
        self.lst.configure(takefocus=True)
        scrollbar.configure(command=(self.lst, 'yview'))
        scrollbar.pack(side=LEFT, fill=Y)

        filler = Frame(f1).pack(side=LEFT, padx=5)

        # buttons on the right
        f12 = Frame(f1)
        
        btn = Button(f12, text="New", underline=0, command=self.onNew)
        btn.pack(side=TOP, expand=0, fill=X, ipadx=10, pady=2)
        
        btn = Button(f12, text="Edit...", underline=0, command=self.onEdit)
        btn.pack(side=TOP, expand=0, fill=X, ipadx=10, pady=2)
        
        btn = Button(f12, text="Rename", underline=4, command=self.onRename)
        btn.pack(side=TOP, expand=0, fill=X, ipadx=10, pady=2)
        
        btn = Button(f12, text="Delete", underline=0, command=self.onDelete)
        btn.pack(side=TOP, expand=0, fill=X, ipadx=10, pady=2)
        
        btn = Button(f12, text="Refresh", underline=2, command=self.onRefresh)
        btn.pack(side=TOP, expand=0, fill=X, ipadx=10, pady=2)

        f12.pack(side=RIGHT, fill=Y)
        
        f1.pack(side=TOP, expand=True, fill=BOTH)
        
        # command line frame
        self.cmdline = StringVar()
        self.cmdline.set('yy')
        f2 = Frame(self.master, padx=8, pady=5)
        lCmdline = Entry(f2, textvariable=self.cmdline, state='readonly')
        lCmdline.pack(side=LEFT, expand=YES, fill=X) 
        filler = Label(f2, width=1).pack(side=LEFT)
        btn = Button(f2, text='Config...', underline=1, command=self.onCfg)
        btn.pack(side=RIGHT, ipadx=10)
        f2.pack(side=TOP, fill=X)

        # buttons at bottom row        
        f3 = Frame(self.master, padx=8, pady=5)
        
        btn = Button(f3, text="Run", underline=0, command=self.onRun)
        btn.pack(side=LEFT, expand=YES, fill=X)

        filler = Label(f3, width=1).pack(side=LEFT)
        
        btn = Button(f3, text="Cancel", underline=0, command=self.onCancel)
        btn.pack(side=RIGHT, expand=YES, fill=X)
        f3.pack(side=BOTTOM, fill=X)

        # event bindings
        self.lst.bind("<Double-Button-1>", self.onRun)
        self.lst.bind("<Delete>", self.onDelete)
        self.lst.bind("<Return>", self.onRun)
        self.lst.bind("<ButtonRelease>", self.onSelChanged)
        self.lst.bind("<KeyRelease>", self.onSelChanged)
        root.bind("<Alt-c>", self.onCancel)
        root.bind("<Alt-d>", self.onDelete)
        root.bind("<Alt-e>", self.onEdit)
        root.bind("<Alt-f>", self.onRefresh)
        root.bind("<Alt-m>", self.onRename)
        root.bind("<Alt-n>", self.onNew)
        root.bind("<Alt-o>", self.onCfg)
        root.bind("<Alt-r>", self.onRun)
        root.bind("<Escape>", self.onCancel)

        self.onRefresh()
        self.lst.focus_set()


    def _updateSel(self):
        sel = self.lst.curselection()
        if sel:
            self.filename = self.lst.get(sel)
        else:    
            self.filename = None


    def onSelChanged(self, e=None):
        self._updateSel()
        print self.filename    
        cmd = '%s %s %s' % (
            sys.executable,
            sys.modules['__main__'].__file__,
            self.filename,
        )
        self.cmdline.set(cmd)

            
    def onNew(self, e=None):
        newfile = tkSimpleDialog.askstring('New', 'Macro filename:')
        if not newfile:
            return
        pathname = emacro.getMacroPath(newfile)
        if os.path.exists(pathname):
            tkMessageBox.showerror('Error', 'Duplicated file "%s"!' % pathname)
            return
        
        fp = file(pathname, 'w')
        fp.write(emacro.getMacroTemplate())
        fp.close()
        self.onRefresh()
        self.setSelection(newfile)
        
        em = EditMacro(self.master, newfile)
                
        
    def onEdit(self, e=None):
        if not self.filename:
            return
        em = EditMacro(self.master, self.filename)

        
    def onRename(self, e=None):
        if not self.filename:
            return
        newfile = tkSimpleDialog.askstring('Rename', 'Rename "%s" as?' % self.filename)
        if not newfile:
            return
        try:
            os.rename(emacro.getMacroPath(self.filename), emacro.getMacroPath(newfile))
        except OSError:    
            show_exc()
        else:    
            self.onRefresh() 
            self.setSelection(newfile)

        
    def onDelete(self, e=None):
        if not self.filename:
            return
        if tkMessageBox.askokcancel('Delete', 'Delete "%s"?' % self.filename):
            pathname = emacro.getMacroPath(self.filename)
            os.remove(pathname)
            self.onRefresh()    
        
        
    def onRefresh(self, e=None):
        self.lst.delete(0, END)
        for p in emacro.listMacro():
            self.lst.insert(AtEnd(), p)
        self.lst.selection_clear(0)
        self.onSelChanged()
        
        
    def onCfg(self, e=None):
        pass                        
        
        
    def onRun(self, e=None):
        self._updateSel()
        self.master.quit()
        
                        
    def onCancel(self, e=None):
        self.filename = None
        self.master.quit()
        
                        
    def setSelection(self, basename):
        if not basename.endswith('.py'):
            basename = basename + '.py'
        self.lst.select_clear(END)
        for i in range(self.lst.size()):
            if self.lst.get(i) == basename:
                self.lst.select_set(i)   
                self.onSelChanged()
                break 


    def run(self):
        self.master.mainloop()
        try:
            self.master.destroy()
        except TclError:
            # the window may have already destroyed (e.g. click close windows)
            # treat as cancel
            return None
        return self.filename


