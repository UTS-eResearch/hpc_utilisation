# HPC Utilisation Script

Python program to check the utilisation of HPC jobs using the PBS scheduler.

## Usage

If you run the program with no args you will get brief usage information:

    $ ./check_utilisation.py 
    usage: check_utilisation.py  running|finished|all  [-h] [-u USER] [-e EMAIL]
    check_utilisation.py: error: the following arguments are required: state

Running with the `-h` option will give more detailed help: `$ ./check_utilisation.py -h` 

You need to specify a "job state" to query; either "running", "finished" or "all" 
like this:

    $ ./check_utilisation.py running
    
    Checking utilisation for jobs after 2021-10-20 17:09 PM
    Found 15 running jobs out of 15 total jobs.
       Job ID  Job Owner         Job Name      Select Statement ncpus  cpu%  cputime  walltime  CPU Util  TIME Util  Comment
                                                                             (hours)   (hours) (percent)  (percent)         
       313295    u1234  PF_NEM_2019_pbs  1:ncpus=1:mpiprocs=1     1    98    766.6     769.1     98.0%      99.7%  Good
       313296    u1234  PF_NEM_2019_pbs  1:ncpus=1:mpiprocs=1     1    98    766.5     769.1     98.0%      99.7%  Good
       313300    u1234  PF_NEM_2019_pbs  1:ncpus=1:mpiprocs=1     1    98    766.6     769.1     98.0%      99.7%  Good
       313301    u1234  PF_NEM_2019_pbs  1:ncpus=1:mpiprocs=1     1    98    766.7     769.1     98.0%      99.7%  Good
       450182    u2468            STDIN  1:ncpus=10:mem=100gb    10   328      0.5       7.2     32.8%       0.7%  CHECK !
       450473    u2468             test  1:mem=150gb:ncpus=15    15   176      2.5       1.5     11.7%      11.5%  CHECK !
       450184    u2468            STDIN  1:ncpus=10:mem=100gb    10    32      0.1       6.6      3.2%       0.1%  CHECK !
       449969    u1122  EGONAV-RL-Colli  1:mem=150gb:ncpus=8:     8   345    136.4      43.4     43.1%      39.3%  CHECK !
    
    Wrote report check_utilisation.html 
    
    To rerun this, and email this report to yourself, run this command:
      ./check_utilisation.py running -e your_email

This will also have written a HTML page with the above information. You can email yourself 
a HTML formatted emailo with this information by using the `-e` option.

Running with the `-u` option will limit results to a specific user. 

## Files

    check_utilisation.py      The main pbsweb application.
    pbs/pbsutils.py           Module containing utility functions for the pbsweb application.
    pbs/swig_compile_pbs.sh   Run this to create _pbs.so
    pbs/pbs.i                 Used by swig_compile_pbs.sh

## Software Required

* PBS Professional commercial or open source. 
  You will need the file `pbs_ifl.h` from your PBS installation.
* gcc
* openssl-devel
* SWIG - Software Wrapper and Interface Generator
* Python 3.8 development packages

## Installation Notes

The `pbs_ifl.h` is not included in this code as you should use the version that
came with your PBS installation. 
Once you have found this file copy it to the location on the login
node where you will later run `swig_compile_pbs.sh` from i.e. the `pbs` directory.

The openssl-devel package provides the libs to link with in the swig compile script 
i.e. "`.. -lcrypto -lssl`".

    $ sudo yum install openssl-devel

The SWIG package (swig) needs to be installed. 
SWIG stands for Software Wrapper and Interface Generator and allows us to 
create a python module that allows python scripts to run PBS commands.
You will also need the PBS `pbs_ifl.h` file that comes with your PBS. 

    $ sudo yum install swig

Edit the shell script `swig_compile.sh` and ensure that the variables at the
top (especially `PYTHON_INCL`) are appropriate for your installation, then run the script. 

    $ cd pbs
    $ ./swig_compile_pbs.sh
    $ cd ..

There will be no output if all goes well.

The above script runs `swig` which uses the SWIG interface file `pbs.i` to
create `pbs.py` and `pbs_wrap.c`. Then it uses `gcc` to compile `pbs_wrap.c` 
to create `_pbs.so`. The swig generated `pbs.py` imports `_pbs.so` at run time.

Now edit `check_utilisation.py` and fill in the required parameters for your site 
i.e. the `from_email` and the `mail_server` settings.

Now you should be able to run the utilisation script from this directory:

    $ ./check_utilisation.py -h
    usage: check_utilisation.py  running|finished|all  [-h] [-u USER] [-e EMAIL]
    
    Check Your HPC Utilisation
    
    positional arguments:
      {running,finished,all}
                            Select one job state to report on.
    
    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  Only show jobs for this user.
      -e EMAIL, --email EMAIL
                            Email a copy of this report to yourself.

If you wish to install the script somewhere else, e.g. under `/usr/local/bin/`
then just copy the script to under `/usr/local/bin/` plus you will need the 
directory `/usr/local/bin/pbs/` containing `pbs.py`, `_pbs.so` and `pbsutils.py`. 
 
## The User Database

In the Python code the `users_db_name` is a small sqlite database that just contains user information 
for our site at UTS. This is not included with this repo. The schema is:

    $ echo '.schema' | sqlite3 users_ldap_public.db
    CREATE TABLE IF NOT EXISTS "users" ( 'id' INTEGER NOT NULL, 'uts_id' TEXT NOT NULL, 'uts_email' TEXT, 'name' TEXT, PRIMARY KEY('id'));

You will probably need to modify the code to pull such information from another source.

## License

HPC Utilisation is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software 
Foundation, either version 3 of the License, or (at your option) any later version.

HPC Utilisation is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
Data Directory Cataloger. If not, see http://www.gnu.org/licenses/.

Copyright 2021 Mike Lake        
eResearch UTS

