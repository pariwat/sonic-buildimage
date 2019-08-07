#!/bin/bash

install() {
     # Install sonic-platform package
    device="/usr/share/sonic/device"
    platform=$(/usr/local/bin/sonic-cfggen -H -v DEVICE_METADATA.localhost.platform)

    if [ -e $device/$platform/sonic_platform-1.0-py2-none-any.whl ]; then
        pip install $device/$platform/sonic_platform-1.0-py2-none-any.whl
    fi
}

uninstall(){
    # Uninstall sonic-platform package
    pip uninstall -y sonic-platform > /dev/null 2>/dev/null
    echo "Usage: $0 {install|uninstall}"
}

case "$1" in
install | uninstall)
    $1
    ;;
*)
    echo "Usage: $0 {install|uninstall}"
    exit 1
    ;;
esac
