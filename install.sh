#!/bin/sh

mkdir /opt/samdeployer
echo "Created installation directory [OK]"
cp samdeployer /opt/samdeployer/
cp icon.png /opt/samdeployer/
cp samdeployer.desktop /usr/share/applications
echo "Created desktop entry [OK]"
ln -s /opt/samdeployer/samdeployer /usr/bin/samdeployer
echo "Linked binaries [OK]"
echo "Installed samdeployer v2.0"



