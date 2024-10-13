#!/bin/bash

start_xrdp_services() {
    # Preventing xrdp startup failure
    rm -rf /var/run/xrdp-sesman.pid
    rm -rf /var/run/xrdp.pid
    rm -rf /var/run/xrdp/xrdp-sesman.pid
    rm -rf /var/run/xrdp/xrdp.pid

    # Use exec ... to forward SIGNAL to child processes
    xrdp-sesman
    xrdp -n
    xrdp-sesrun -p rdp -s 127.0.0.1 rdp
    sudo -u rdp xhost +
}

stop_xrdp_services() {
    xrdp --kill
    xrdp-sesman --kill
    exit 0
}

trap "stop_xrdp_services" SIGKILL SIGTERM SIGHUP SIGINT EXIT

start_xrdp_services
