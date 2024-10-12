#!/bin/sh

echo "Starting window manager..."

if [ -r /etc/default/locale ]; then
  . /etc/default/locale
  export LANG LANGUAGE
fi

# Default
#. /etc/X11/Xsession

# XFCE
startxfce4
xhost +
