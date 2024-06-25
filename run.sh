#!/usr/bin/env bash
BASEDIR=$(dirname "$0")
echo "Executing App in '$BASEDIR'"
PORT=5000
source $BASEDIR/env/bin/activate
python $BASEDIR/webtftp.py $PORT
