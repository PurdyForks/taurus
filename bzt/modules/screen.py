# coding=utf-8
"""
Copyright 2015 BlazeMeter Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from Tkinter import Tk, Text
import Tkinter
import logging
import re
import six
import tkFont
import math

from urwid import BaseScreen

from bzt import ManualShutdown


class DummyScreen(BaseScreen):
    """
    Null-object for Screen on non-tty output
    """

    def __init__(self, cols, rows):
        super(DummyScreen, self).__init__()
        self.size = (cols, rows)
        self.ansi_escape = re.compile(r'\x1b[^m]*m')

    def get_cols_rows(self):
        """
        Dummy cols and rows

        :return:
        """
        return self.size

    def draw_screen(self, size, canvas):
        """

        :param size:
        :type canvas: urwid.Canvas
        """
        data = ""
        for char in canvas.content():
            line = ""
            for part in char:
                if isinstance(part[2], str):
                    line += part[2]
                else:
                    line += part[2].decode()
            data += "%s│\n" % line
        data = self.ansi_escape.sub('', data)
        logging.info("Screen %sx%s chars:\n%s", size[0], size[1], data)


class GUIScreen(BaseScreen):
    """
    :type root: Tk
    """

    def __init__(self):
        super(GUIScreen, self).__init__()
        self.root = None
        self.size = (146, 50)
        self.title = "Taurus Status"

    def get_cols_rows(self):
        """
        Dummy cols and rows

        :return:
        """
        return self.size

    def _start(self):
        super(GUIScreen, self)._start()
        self.root = Tk()
        self.root.geometry("%sx%s" % (self.size[0] * 7, self.size[1] * 15))
        self.root.bind("<Configure>", self.resize)
        self.root.protocol("WM_DELETE_WINDOW", self.closed_window)
        self.text = Text(self.root, font="TkFixedFont", wrap=Tkinter.NONE, state=Tkinter.DISABLED,
                         background="black", foreground="light gray")
        self.text.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=Tkinter.YES)
        self.__prepare_tags()

    def _stop(self):
        if self.root:
            self.root.destroy()
        super(GUIScreen, self)._stop()

    def resize(self, event):
        font = tkFont.Font(self.root, self.text.cget("font"))
        (cwdth, chght) = (font.measure(' '), font.metrics("linespace"))
        logging.debug("Font: %s", (cwdth, chght))

        width = int(math.floor((self.text.winfo_width() - float(cwdth) / 2) / float(cwdth)))
        height = int(math.floor(self.text.winfo_height() / float(chght)))
        self.size = (width, height)
        self.root.title(self.title + " %sx%s" % self.size)

    def closed_window(self):
        self.root.destroy()
        self.root = None

    def draw_screen(self, size, canvas):
        """

        :param size:
        :type canvas: urwid.Canvas
        """
        if not self.root:
            raise ManualShutdown("GUI window was closed")

        # enable changes
        self.text.config(state=Tkinter.NORMAL)
        self.text.delete("1.0", Tkinter.END)

        for idx, row in enumerate(canvas.content()):
            pos = 0
            for part in row:
                if isinstance(part[2], str):
                    txt = part[2]
                else:
                    txt = part[2].decode()

                try:
                    strlen = len(txt.decode("utf-8"))
                except UnicodeDecodeError:
                    strlen = len(txt)

                self.text.insert(Tkinter.END, txt)
                if part[0] is not None:
                    self.text.tag_add(part[0], "%s.%s" % (idx + 1, pos), "%s.%s" % (idx + 1, pos + strlen))
                pos += strlen

            self.text.insert(Tkinter.END, "\n")

        # disable changes
        self.text.config(state=Tkinter.DISABLED)
        self.root.update()

    def __translate_tcl_color(self, style):
        if style == 'default':
            return None
        elif style == "light magenta":
            return "magenta"
        elif style == "light red":
            return "red"
        elif style == "brown":
            return "dark orange"
        else:
            return style

    def __prepare_tags(self):
        for name, style in six.iteritems(self._palette):
            # NOTE: not sure which index use, used [0]
            bgc = self.__translate_tcl_color(style[0].background)
            fgc = self.__translate_tcl_color(style[0].foreground)
            self.text.tag_configure(name, background=bgc, foreground=fgc)
