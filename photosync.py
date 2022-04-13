from __future__ import print_function

import os
import sys
import shutil
import time
import re
import logging
import ConfigParser
import traceback
import webbrowser


import Tkinter as tk #from tkinter import Tk, Label, Message, Button
#from PIL import ImageTk, Image
import tkFileDialog
import tkMessageBox
import tkFont
import ttk


# Geometry constants
WIDTH = 500
HEIGHT = 400
WLEFT = 100
WLOGO = 64
HSPACE = 40
HSSPACE = 28
HMSPACE = 22
HBUTTON = 40
WBUTTON = 100
MARGINE = (WLEFT - WLOGO) // 2

LABEL_FONT = (None, 10, tkFont.NORMAL)
BUTTON_FONT = LABEL_FONT
TITLE_FONT = (None, 10, tkFont.BOLD)
TIP_FONT = (None, 9, tkFont.NORMAL)
PHASES_FONT_SIZE = 10


class Dialogue(object):
    last_conf = dict()
    root = tk.Tk()

    y = MARGINE

    @classmethod
    def mainloop(cls):
        logging.info('Start mainloop')
        cls.root.mainloop()
        logging.info('Finish')

    @classmethod
    def cancel(cls):
        answer = tkMessageBox.askyesno(
            title='Quit',
            message='Are you sure?'
        )
        if answer:
            logging.info('Quit by user')
            # destroy
            cls.root.quit()

    @classmethod
    def show_error(self, *args):
        err = traceback.format_exception(*args)
        logging.info('Exception %s', ''.join(err))
        tkMessageBox.showerror('Exception', ''.join(err))


    @classmethod
    def next(cls):
        pass#cls.change_phase(1)

    @classmethod
    def prev(cls):
        pass#cls.change_phase(-1)


    @classmethod
    def add_left_pane(cls):
        frame = tk.Frame(height=HEIGHT-MARGINE*2, width=2, bd=1, relief=tk.SUNKEN)
        frame.place(x=WLEFT, y=MARGINE)

    """
    @classmethod
    def add_next(cls):
        cls.next_btn = tk.Button(cls.root, text=cls.next_button_label(), command=cls.next, font=BUTTON_FONT)
        cls.next_btn.place(x=WLEFT + MARGINE + WBUTTON, y=HEIGHT - MARGINE, anchor=tk.SW)
        cls.run_fields_check()
    """


    @classmethod
    def add_prev(cls):
        btn = tk.Button(cls.root, text=" < Previous ", command=cls.prev, font=BUTTON_FONT)
        btn.place(x=WLEFT + MARGINE, y=HEIGHT - MARGINE, anchor=tk.SW)

    @classmethod
    def add_title(cls, text):
#        label = tk.Label(self.root, text=text, font=TITLE_FONT)
        label = tk.Message(cls.root, text=text, width=WIDTH-WLEFT-MARGINE*2, font=TITLE_FONT)
        label.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HSPACE

    @classmethod
    def add_cancel(cls):
        btn = tk.Button(cls.root, text=" Cancel ", command=cls.cancel, font=BUTTON_FONT)
        btn.place(x=WIDTH - MARGINE, y=HEIGHT - MARGINE, anchor=tk.SE)

    @classmethod
    def add_pick_folder(cls, prompt, variable, tip=None):
        def pick_callback():
            cls.pick_folder(variable)

        label = tk.Label(cls.root, text=prompt, font=LABEL_FONT)
        label.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HSPACE

        #vcmd = (cls.root.register(cls.validate), '%P')
        entry = tk.Entry(cls.root, textvariable=variable, width=38, font=LABEL_FONT,
                         validate="key")#, validatecommand=vcmd)
        entry.place(x=WLEFT + MARGINE, y=Dialogue.y, anchor=tk.W)

        button = tk.Button(cls.root, text="Choose", command=pick_callback, font=BUTTON_FONT)
        button.place(x=WIDTH - MARGINE, y=cls.y, anchor=tk.E)

        if tip is not None:
            Dialogue.y += HMSPACE
            message = tk.Message(cls.root, width=WIDTH - WLEFT - MARGINE * 2 - 70, text=tip, font=LABEL_FONT)
            message.place(x=WLEFT + MARGINE, y=Dialogue.y)
            #label = tk.Label(self.root, text=tip, font=TIP_FONT)
            #label.place(x=WLEFT + MARGINE, y=Dialogue.y)
            Dialogue.y += HSPACE
        else:
            Dialogue.y += HSPACE

    @classmethod
    def add_input(cls, prompt, width, variable, tip=None):
        label = tk.Label(cls.root, text=prompt, font=LABEL_FONT)
        label.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HMSPACE

        #vcmd = (cls.root.register(cls.validate), '%P')
        entry = tk.Entry(cls.root, width=width, textvariable=variable, validate="key")#, validatecommand=vcmd)
        entry.place(x=WLEFT + MARGINE, y=Dialogue.y)
        if tip is not None:
            Dialogue.y += HMSPACE
            message = tk.Message(cls.root, text=tip, width=WIDTH - WLEFT - MARGINE * 2 - 70, font=TIP_FONT)
            message.place(x=WLEFT + MARGINE, y=Dialogue.y)
            Dialogue.y += HSPACE
        else:
            Dialogue.y += HSSPACE

    @classmethod
    def add_button(cls, text, command):
        btn = tk.Button(cls.root, text=text, command=command, font=BUTTON_FONT)
        btn.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HMSPACE

    @classmethod
    def add_checkbutton(cls, text, variable, tip=None):
        check = tk.Checkbutton(cls.root,
                               text=text,
                               variable=variable,
                               font=LABEL_FONT)

        check.place(x=WLEFT + MARGINE, y=Dialogue.y)
        if tip is not None:
            Dialogue.y += HMSPACE
            label = tk.Label(cls.root, font=TIP_FONT, text=tip)
            label.place(x=WLEFT + MARGINE, y=Dialogue.y)
            Dialogue.y += HSPACE
        else:
            Dialogue.y += HSSPACE
        return check

    @classmethod
    def add_progress(cls, text, variable, maximum):
        label = tk.Label(cls.root, text=text)
        label.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HSPACE
        bar = ttk.Progressbar(cls.root,
                               orient="horizontal",
                               length=WIDTH - WLEFT - MARGINE * 3,
                               mode="determinate",
                               variable=variable,
                               maximum=maximum)
        bar.place(x=WLEFT + MARGINE, y=Dialogue.y)
        Dialogue.y += HSPACE
        return bar

    @classmethod
    def add_message(cls, text):
        message = tk.Message(cls.root, width=WIDTH - WLEFT - MARGINE * 2, text=text, font=LABEL_FONT)
        message.place(x=WLEFT + MARGINE, y=Dialogue.y)

    @classmethod
    def init(cls):
        tk.Tk.report_callback_exception = cls.show_error
        cls.root.geometry("{}x{}".format(WIDTH, HEIGHT))
        cls.root.resizable(0, 0)
        #cls.root.iconbitmap('te_mac.icns')
        cls.root.title("PhotoSync")
        cls.root.protocol("WM_DELETE_WINDOW", cls.cancel)
        cls.operate()

    @classmethod
    def cleanup(cls):
        for c in cls.root.children.values():
            c.destroy()

    @classmethod
    def basic_widgets(cls):
        #cls.add_image()
        #cls.progress_list()
        cls.add_left_pane()
        #cls.add_next()
        #cls.add_prev()
        cls.add_cancel()

    @classmethod
    def operate(cls):
        logging.info("%s operate", cls.__name__)
        cls.cleanup()
        cls.basic_widgets()
        Dialogue.y = MARGINE
        cls.decorate()

    @classmethod
    def decorate(cls):
        pass

    @classmethod
    def pick_folder(cls, var):
        dir_name = tkFileDialog.askdirectory(initialdir=var.get(),
                                             title="Select folder")
        if dir_name == '':
            return
        var.set(dir_name)

    #@log_return
    @staticmethod
    def yesno(title, message):
        return tkMessageBox.askyesno(title, message)

    @classmethod
    def add_next(cls, text, command):
        cls.next_btn = tk.Button(cls.root, text=text, command=command, font=BUTTON_FONT)
        cls.next_btn.place(x=WLEFT + MARGINE + WBUTTON, y=HEIGHT - MARGINE, anchor=tk.SW)
        #cls.run_fields_check()


class ChooseFolders(Dialogue):

    source = tk.StringVar()
    target = tk.StringVar()
    nohash = tk.IntVar()
    nohash.set(0)
    noprotect = tk.IntVar()
    noprotect.set(1)

    @classmethod
    def decorate(cls):
        cls.add_pick_folder('Local Photos', cls.source)
        cls.add_pick_folder('External Photos', cls.target)
        cls.add_checkbutton('Do not generate hash files', cls.nohash)
        cls.add_checkbutton('Do not protect folders & files', cls.noprotect)
        cls.add_next(' Scan ', cls.scan)

    @classmethod
    def scan(cls):
        Scan.operate()


class Scan(ChooseFolders):

    current_phase = tk.IntVar()

    @classmethod
    def decorate(cls):
        cls.current_phase.set(3)
        cls.add_progress('Analysis', cls.current_phase, 10)


def usage():
    print('Usage {} [--log <file name>]'.format(sys.argv[0]))
    sys.exit(1)


def main():
    ChooseFolders.init()
    ChooseFolders.mainloop()


if __name__ == '__main__':
    main()
