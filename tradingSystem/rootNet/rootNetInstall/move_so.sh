#!/bin/bash

sudo cp LinuxDataCollect.so /usr/local/lib/python3.8/dist-packages/CTSlib-1.209_py38.egg/CTSlib/

cd /usr/lib/x86_64-linux-gnu/
sudo ln -s libcrypto.so.1.1 libcrypto.so.6
sudo ln -s libssl.so.1.1 libssl.so.6
