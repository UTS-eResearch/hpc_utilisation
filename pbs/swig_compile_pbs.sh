#!/bin/bash

# Uses the PBS files pbs_ifl.h and pbs.i to create pbs.py, pbs_wrap.c and _pbs.so.

#############################
# Set your configuration here
#############################

conf="/etc/pbs.conf"  # PBS configuration file

# Example: If using my laptop.
PYTHON_INCL="/usr/include/python3.8"

# Example: If using Python in a virtual environment.
#PYTHON_INCL=/var/www/wsgi/virtualenvs/pbsweb/include/python3.8

SWIG_EXEC="/usr/bin/swig"

# You should not need to change anything below here.

# Make sure we have a PBS config file.
if [ ! -f $conf ]; then
   echo "Error: missing PBS configuration file $conf"
   exit 0
fi 

# The PBS config file must be sourced to provide $PBS_EXEC.
. $conf

export LD_RUN_PATH=$PBS_EXEC/lib

# Running swig creates pbs.py and pbs_wrap.c
$SWIG_EXEC -I$PBS_EXEC/include -python pbs.i

if [ $? -ne 0 ]; then
    echo 'Error: You are probably missing the file: /opt/pbs/include/pbs_ifl.h'
    exit 0
fi

# Running gcc creates _pbs.so
#gcc -shared -fPIC -I$PYTHON_INCL -I$PBS_EXEC/include pbs_wrap.c $PBS_EXEC/lib/libpbs.so \
#    -o _pbs.so -L/lib -lcrypto -lssl

# Compiling
gcc -c -shared -fpic -I$PYTHON_INCL -I$PBS_EXEC/include pbs_wrap.c -o pbs_wrap.o 

# Linking
# Not sure if we need to also add -L/lib
gcc -shared -fpic -L/opt/pbs/lib \
    $PBS_EXEC/lib/libpbs.so pbs_wrap.o \
    -lpthread -lcrypto -lssl \
    -o _pbs.so

# It does not need to be executable.
chmod ugo-x _pbs.so

