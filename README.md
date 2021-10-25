# hpc_utilisation

Python program to check the utilisation of HPC jobs using the PBS schedular.

## Usage

If you run the program with no args you will get brief usage information:

    $ ./check_utilisation.py 
    usage: check_utilisation.py  running|finished|all  [-h] [-u USER] [-e EMAIL]
    check_utilisation.py: error: the following arguments are required: state

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


## The User Database

In the Python code the `users_db_name` is a small sqlite database that just contains user information.
The schema is:

    $ echo '.schema' | sqlite3 users_ldap_public.db
    CREATE TABLE IF NOT EXISTS "users" ( 'id' INTEGER NOT NULL, 'uts_id' TEXT NOT NULL, 'uts_email' TEXT, 'name' TEXT, PRIMARY KEY('id'));

You may wish to modify the code to pull such information from another source.

Mike Lake
eResearch UTS

