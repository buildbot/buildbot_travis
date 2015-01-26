# this install dependancies in current directory with the help of virtualenv
set -e
virtualenv sandbox
. sandbox/bin/activate
pip install -r requirements.txt
pip install -e ..
