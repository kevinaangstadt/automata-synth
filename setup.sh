#!/bin/bash

sudo apt-get update
sudo apt-get install -y build-essential git

git submodule update --init

sudo pip2 install -r requirements.txt