#!/usr/bin/env python3

import fstimer.fslogger
import fstimer.timer

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def main():
    pytimer = fstimer.timer.PyTimer()
    Gtk.main()

if __name__ == '__main__':
    main()
