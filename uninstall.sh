#!/bin/sh

if [ -f /usr/bin/samdeployer ]; then
	rm /usr/bin/samdeployer
	echo "Removed binaries [OK]"
fi

if [ -d /opt/samdeployer ]; then
        rm -rf /opt/samdeployer
        echo "Removed installation directory [OK]"
fi

if [ -f /usr/share/applications/samdeployer.desktop ]; then
        rm /usr/share/applications/samdeployer.desktop
        echo "Removed desktop entry [OK]"
fi

echo "Uninstalled samdeployer v2.0"
