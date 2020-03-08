#!/bin/bash

# os-level dependencies
sudo apt-get update
sudo apt-get install -y ant build-essential default-jdk-headless git \
                        python-minimal python-pip

# download sub-repos
git submodule update --init

# install python packages
sudo pip2 install --upgrade pip
sudo pip2 install -r requirements.txt

# build cpachecker
cd cpachecker
ant
cd ..