#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script checks the utilisation of HPC jobs.

'''
This script checks the utilisation of HPC jobs.
Run the program with -h or --help to get help on usage.

Note to installers:
1. This program should be installed on just the login node under /opt/eresearch/
2. The public version of the users database needs to be updated every time the
   main database is updated.

Notes:
Cannot use job key 'euser' from pbs_connect(pbs_server):
  At first I was using job['euser'] from the jobs returned from PBS to get the user
  running the job. It turns out that this key is only available to PBS admin users
  and not ordinary users. If you do a "qstat -f job_id" of a job as a PBS admin and
  as a user you will see that a few attributes are missing to users.
  You need to use 'job_owner' as a key. The attribute job['euser'] is like u999777
  while j['job_owner'] is u999777@hpcnode1 where the last part is the login node name.

Author: Mike Lake

License

Copyright 2021 Mike Lake

HPC Utilisation is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

HPC Utilisation is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with Foobar. 
If not, see <https://www.gnu.org/licenses/>. 

Releases

  2021-04-29 First release.
  2021-11-01 Use docopt arg parsing instead or argparse. Had to add a virtualenv for this.

'''

# TODO 
# We can invoke a specific python interpeter explicitly like this:
# 
#  $ source /opt/eresearch/virtualenvs/hpc_utilisation/bin/activate
#  #!/usr/bin/env python3
# 
# or invoke it like this directly:
#  #!/opt/eresearch/virtualenvs/hpc_utilisation/bin/python3
#
# or invoke `activate_this.py` like this:
## Load python from this virtual environment and unload the system python.
#activate_this_file = "/opt/eresearch/virtualenvs/hpc_utilisation/bin/activate_this.py"
#with open(activate_this_file) as f:
#    #exec(f.read(), dict(__file__=activate_this_file))
#    #exec(f.read(), {'__file__':activate_this_file})
#    exec(open(activate_this_file).read(), {'__file__': activate_this_file})
#    exec(compile(open(activate_this_file, "rb").read(), activate_this_file, 'exec'), dict(__file__=activate_this_file))

import sys, os, re
import pwd
import datetime
from docopt import docopt

# Append what ever pbs directory is under the directory that this script is located
# in. This ensures that we use /opt/eresearch/pbs for the version used by users and
# whatever pbs is under this script if its a development version.
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), 'pbs'))
#sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), '/shared/homes/mlake/git/hpc_utilisation/pbs'))
#sys.path.append(os.path.abspath("pbs"))

import pbs
from pbsutils import get_jobs, job_attributes_reformat
from sqlite3 import dbapi2 as sqlite
import smtplib

#####################
# Set parameters here
#####################

# You need to set the hostname of the PBS Server
pbs_server = 'hpcnode0'

# Name of the users database. The "public" one has some fields removed. This is because
# this script and the database is available to users under /usr/local/bin/.
# Do not use the full path here. It needs to reside in the same directory as this script.
users_db_name = 'users_ldap_public.db'

# Target utilisation in percent. Anything below this will be tagged with "CHECK".
target = 80

# Number of past days to search for finished jobs from PBS history.
# This must be an integer from 1 upwards. Usually 7 would be suitable.
past_days = 5

# Filename for the HTML output file.
html_output = 'check_utilisation.html'

# This line must be set to your email address.
from_email = 'Mike.Lake@uts.edu.au'

# This will be None unless set via the command line.
recipient_email = None

# Your login nodes mail server.
mail_server = 'postoffice.uts.edu.au'

# The programs usage comes from this string being parsed by docopt.
usage_doc = '''
Check Your HPC Utilisation

Usage: 
  check_utilisation.py running  [-e <email>] [-u <user> ]
  check_utilisation.py finished [-e <email>] [-u <user> ]
  check_utilisation.py all      [-e <email>] [-u <user> ]
  check_utilisation.py -h | --help

Options:
  -e <email>    Email a copy of this report to yourself.
  -u <user>     Only show jobs for this user.

For further help contact the author: Mike.Lake@uts.edu.au
'''

prefix = '''
<p>Hi</p>

<p>The HPC is occasionally very busy and it is better for all users if we try to improve the
throughpout of jobs. Sometimes there are jobs that are requesting more CPU cores (ncpus) than
the jobs are capable of using. When you ask for 8 cores and only use 1 core, 7 cores lay idle.
Those cores could have been used by other researchers.
As an example, a simple python program is single threaded and can only ever use one core.</p>

<p>In the table below you will see your job(s). Consider the CPU and TIME "Utilisation" columns.
For each job those values should be close to 100%. Consider them like your high school reports :-)
A description of these fields can be found under the table.</p>

</p>If you are going to start a job then please consider how many cores (ncpus) your job
really can utilise. During your run use "<code>qstat -f job_id</code>" and after the run
"<code>qstat -fx job_id</code>" to see if your job used the cores that you requested.
The same can be done for memory and walltime. Just ask for a bit more than what
you think your job requires.</p>

<p>If you have any questions just email me and I'll try to assist.</p>
'''

postfix = '''
<p>What is "cpu%" ? <br>
The PBS scheduler polls all jobs every few minutes and calculates an integer
value called "cpupercent" at each polling cycle. This is a moving weighted average
of CPU usage for the cycle, given as the average percentage usage of one CPU.
For example, a value of 50 means that during a certain period, the job used 50
percent of one CPU. A value of 300 means that during the period, the job used
an average of three CPUs. You can find the cpupercent used from the
<code>qstat</code> command.
</p>

<p>What is "CPU Utilisation %" ? <br>
This is what I have calculated. It's the cpupercent / ncpus requested.<br>
If you ask for 1 core and use it fully then this will be close to 100%. <br>
If you ask for 3 cores and use all of those then this will be 300%/3 = 100% again. <br>
If you ask for 3 cores and use 1 core it will be about 33%. You do not get a pass mark :-)
</p>
'''

########################
# Functions defined here
########################

def getKey(item):
    # You can change this to job_id, resources_time_left etc.
    return item['job_owner']

def getKey2(item, string='job_owner'):
    # Usage: jobs = sorted(jobs, key=getKey(istring='job_owner'))
    #return item['resources_time_left']
    return item[string]

def print_table_start():
    '''
    This prints the start of the table of usage to the screen and
    also to the HTML output file. The format will be like this:

    Job ID  Job Owner  Job Name  Select Statement ncpus  cpu%  cputime  walltime  CPU Util  TIME Util  Comment
                                                  used         (hours)   (hours) (percent)  (percent)
    '''

    # Append tuples of (heading, field width, units)
    heading = []
    heading.append(('Job ID',            9, ' '))
    heading.append(('Job Owner',        11, ' '))
    heading.append(('Job Name',         17, ' '))
    heading.append(('Select Statement', 22, ' '))
    #heading.append(('ncpus',             6, ' '))     # TODO space or
    heading.append(('ncpus',             6, 'used'))   # TODO text 'used'
    heading.append(('cpu%',              6, ' '))
    heading.append(('cputime',           9, '(hours)'))
    heading.append(('walltime',         10, '(hours)'))
    heading.append(('CPU Util',         10, '(percent)'))
    heading.append(('TIME Util',        11, '(percent)'))
    heading.append(('Comment',           9, ' '))

    # Print table heading on one line.
    for item in heading:
        print(item[0].rjust(item[1]), end='')
    print('')

    # Print units for each table header on the next line.
    for item in heading:
        print(item[2].rjust(item[1]), end='')
    print('')

    html="<table border=1 cellpadding=4>\n<tr>\n"

    for item in heading:
        if item[0] == 'CPU Util':
            html = html + "<th>CPU<br>Utilisation</th>\n"
        elif item[0] == 'TIME Util':
            html = html + "<th>TIME<br>Utilisation</th>\n"
        else:
            html = html + "<th>%s</th>\n" % item[0]

    html = html + "</tr>\n"

    return html

def print_table_end():

    # Get a formatted date and time for use in the HTML report.
    date_time = datetime.datetime.now().strftime('%Y-%m-%d at %I:%M %p')
    # print() take care of converting each element to a string.
    html = '</table>\n'
    # Create a string being the basename of the program iand then append its args.
    # We slice sys.argv as we don't as its first element which is the full path
    # to the program.
    program_name = os.path.basename(sys.argv[0])
    invocation = program_name + ' ' + ' '.join([str(s) for s in sys.argv[1:]])
    html = html + "<p>HPC Utilisation Report created on %s from program:</br>\n" % date_time
    html = html + "&nbsp;&nbsp;<code>%s</code></p>\n" % invocation
    return html

def print_jobs(jobs, fh):

    for job in jobs:
        # print(job['job_id'])
        # 136087.hpcnode0 did not have a cpu_percent value
        # comment = Not Running: Insufficient amount of resource: ncpus  and terminated.
        row = []

        ###################################
        # Calculate a CPU utilisation value
        ###################################
        # A queued job or an array parent job wil not have these attributes set
        # so we just assign cpu_utilisation to be zero.
        try:
            cpu_utilisation = float(job['resources_used_cpupercent']) / int(job['resources_used_ncpus'])
        except:
            cpu_utilisation = 0.0

        ####################################
        # Calculate a time utilisation value
        ####################################

        (cpu_hours, cpu_mins, cpu_secs) = job['resources_used_cput'].split(':')
        (wall_hours, wall_mins, wall_secs) = job['resources_used_walltime'].split(':')

        # Now we change these hours and mins into decimal hours.
        cpu_hours = float(cpu_hours) + float(cpu_mins)/60.0 + float(cpu_secs)/3660.0
        wall_hours = float(wall_hours) + float(wall_mins)/60.0 + float(wall_secs)/3600.0
        # Note: if a job has just started the walltime might be zero and the
        # calculated wall_hours will be 0. In this case set it to be a small
        # nominal value such as 0.1 hours.
        if wall_hours == 0:
            wall_hours = 0.1

        # Here we have to cast ncpus to a float so we can perform math operations
        # with the other floats. Note: A queued job or an array parent job will
        # not have these attributes set.
        try:
            ncpus = float(job['resources_used_ncpus'])
        except:
            ncpus = 0

        # If ncpus is zero or wall hours is zero (likely, if a job is queued) we
        # will get a divide-by-zero. In this case set time_utilisation to zero.
        # We should not get this though as in this script we remove queued jobs.
        try:
            time_utilisation = float(100.0*cpu_hours/ncpus/wall_hours)
        except:
            time_utilisation = 0

        # The following are still strings so we can use rjust() for formatting.
        # Nor do we need to format them for HTML output.
        print(job['job_id'].rjust(9), end='');                      row.append(job['job_id'])
        print(job['job_owner'].rjust(11), end='');                  row.append(job['job_owner'])
        print(job['job_name'][0:15].rjust(17), end='');             row.append(job['job_name'])
        print(job['resource_list_select'][0:20].rjust(22), end=''); row.append(job['resource_list_select'][0:20])
        print(job['resources_used_ncpus'].rjust(6), end='');        row.append(job['resources_used_ncpus'])
        print(job['resources_used_cpupercent'].rjust(6), end='');   row.append(job['resources_used_cpupercent'])

        # These vars are floats.
        s = '{:9.1f}'.format(cpu_hours);           print(s, end=''); row.append(s)
        s = '{:10.1f}'.format(wall_hours);         print(s, end=''); row.append(s)
        s = '{:9.1f}%'.format(cpu_utilisation);    print(s, end=''); row.append(s)
        s = '{:10.1f}%'.format(time_utilisation);  print(s, end=''); row.append(s)

        if cpu_utilisation > target and time_utilisation > target:
            # Both CPU utilisation and TIME utilisation are more than our target.
            comment='<span style="color:green;">Good</span>'
            print ("  Good");
        else:
            comment='<span style="color:red;">CHECK !</span>'
            print ("  CHECK !")

        row.append(comment)

        fh.write('<tr>\n')
        for item in row:
            fh.write('  <td>%s</td>\n' % item)
        fh.write('</tr>\n')

def get_user_email(users_db_path, user_id):
    '''
    Given a user_id return their email from the database of users.
    If the user is not in the database return None for the email.
    '''

    # Strip off the leading 'u' from the user ID as the database does not contain this.
    user_id = user_id.lstrip('u')
    try:
        con = sqlite.connect(users_db_path)
    except:
        print ("Error: Can\'t connect to the database.")
        sys.exit()

    con.row_factory = sqlite.Row
    cur = con.cursor()
    cur.execute('SELECT uts_email FROM users where uts_id="%s"' % user_id)
    row = cur.fetchone()
    cur.close
    con.close

    # We returned row will be a tuple (email,) if the user exists, otherwise
    # the row will be None.
    if row is not None:
        email = row[0]
    else:
        email = None

    return email

def send_email(from_email, recipient_email, message_body):
    '''
    This takes a "from" email, a "recipient" to send the email to, and
    a string "message_body" which has to be a filename of the file
    containing the body of the message to send.
    The email will be a HTML formatted email because the message body
    is a HTML file.
    '''

    # Mail header for a HTML email. Do not forget that newline!
    mail_header = """From: <%s>
To: <%s>
Subject: HPC Utilisation Report
MIME-Version: 1.0
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7BIT
Content-Disposition: inline

""" % (from_email, recipient_email)

    # Open and read in the file that contains the HTML formatted body of the message.
    fh = open(message_body, 'r')
    message_body = fh.read()
    fh.close()

    # The full message to send is the mail header plus the message body.
    message = mail_header + message_body
    if recipient_email is not None:
        session = smtplib.SMTP(mail_server, 25)
        print ('Sending to %s' % recipient_email)
        try:
            result = session.sendmail(from_email, recipient_email, message)
            print("Sent OK\n")
        except:
            print("Error sending email.\n")

        session.quit()

def main():

    ##################################################
    # Check program args and access to required files.
    ##################################################
    args = docopt(usage_doc, argv=None, help=True, version=None, options_first=False)
 
    if args['-u']: 
        user_id = args['-u']
    else:
        user_id = None

    #sys.exit(0)

    # Check that we can access the HPC user database.
    dirpath = os.path.dirname(sys.argv[0])
    users_db_path = os.path.join(dirpath, users_db_name)
    if not os.path.exists(users_db_path):
        print ("The user database {} can\'t be found." .format(users_db_path))
        print ("This program needs to be run from the same directory as the user database.")
        sys.exit()

    ##########################################################
    # Connect to the PBS server and get the reqested job data.
    # We also get some times which we need.
    ##########################################################

    time_past  = datetime.datetime.now() - datetime.timedelta(days=past_days)
    epoch_past = int(datetime.datetime.timestamp(time_past))
    time_start = datetime.datetime.fromtimestamp(epoch_past)

    print("\nChecking utilisation for jobs after", time_start.strftime('%Y-%m-%d %H:%M %p'))
    if user_id is not None:
        print("Jobs limited to user", user_id)

    conn = pbs.pbs_connect(pbs_server)

    if args['running']:
    # if state == 'running':
        # This will get just current jobs; queued, running, and exiting.
        # We have added the 't' to also include current array jobs.
        jobs = get_jobs(conn, extend='t')
        total = len(jobs)
        if user_id is not None:
            # Limit the jobs to just this user.
            # We take the j['job_owner'] which is like u999777@hpcnode01 and
            # split it on the @ then take the first part.
            jobs = [j for j in jobs if j['job_owner'].split('@')[0] == user_id]

        # Only keep in the list jobs that are running.
        # This will also remove array parent jobs as they are state 'B".
        jobs = [j for j in jobs if j['job_state'] == 'R']
        print('Found %d running jobs out of %d total jobs.' % (len(jobs), total))
    elif args['finished']:
    # elif state == 'finished':
        # This will get ALL jobs, current and finished.
        jobs = get_jobs(conn, extend='xt')
        total = len(jobs)
        if user_id is not None:
            jobs = [j for j in jobs if j['job_owner'].split('@')[0] == user_id]

        # Only keep in the list jobs that are finished.
        jobs = [j for j in jobs if j['job_state'] == 'F']
        print('Found %d finished jobs out of %d total jobs in PBS history.' % (len(jobs), total))

        # Only keep in the list jobs that finished in the last n days.
        # Some jobs appear to be missing an stime and etime so we cannot use the line below.
        #   jobs = [j for j in jobs if int(j['etime']) > epoch_past]
        # This should work but does not because sometimes there is an etime but its ''.
        # Then the int of '' fails.
        #  jobs = [j for j in jobs if int(j.get('etime', 0)) > epoch_past]
        # So we will use the for loop below.
        jobs_tmp = []
        for i in range(len(jobs)):
            if 'etime' in jobs[i] and jobs[i]['etime']:
                if int(jobs[i]['etime']) > epoch_past:
                    jobs_tmp.append(jobs[i])

        jobs = jobs_tmp
        print('Found %d finished jobs from last %d days.' % (len(jobs), past_days))
    elif args['all']:
    #elif state == 'all':
        # This will get ALL jobs, current and finished.
        jobs = get_jobs(conn, extend='xt')
        total = len(jobs)
        if user_id is not None:
            jobs = [j for j in jobs if j['job_owner'].split('@')[0] == user_id]

        # Create two lists; jobs that are running and those that are finished.
        jobs_running  = [j for j in jobs if j['job_state'] == 'R']
        jobs_finished = [j for j in jobs if j['job_state'] == 'F']
        print('Found %d running jobs and %d finished jobs, out of %d total jobs in PBS history.' % \
            (len(jobs_running), len(jobs_finished), total))

        # Only keep in the finished list those finished in the last n days.
        jobs_tmp = []
        for i in range(len(jobs_finished)):
            if 'etime' in jobs[i] and jobs[i]['etime']:
                if int(jobs[i]['etime']) > epoch_past:
                    jobs_tmp.append(jobs[i])
        jobs_finished = jobs_tmp
        print('Found %d finished jobs from last %d days.' % (len(jobs_finished), past_days))

    else:
        # We should never get here.
        print("Invalid state %s" % state)
        sys.exit()

    pbs.pbs_disconnect(conn)

    ######################################################
    # Print the job data to the screen and as HTML output.
    ######################################################

    jobs = job_attributes_reformat(jobs)

    # Sort by attribute.
    # The sorted() function accepts a key function as an argument and calls it
    # on each element prior to make comparison with other elements.
    jobs = sorted(jobs, key=getKey)

    # Write the jobs to a HTML formatted output file.
    try:
        fh = open(html_output, 'w')
    except:
        print("I cannot create your HTML report. You are probably are running this script")
        print("from a localtion where you do not have permission to write to. Try running")
        print("this script from your home directory.")
        sys.exit()
    fh.write(prefix)

    if args['running']:
    # if state == 'running':
        fh.write("<p>Running Jobs</p>")
        fh.write(print_table_start())
        print_jobs(jobs, fh)
        fh.write(print_table_end())
    elif args['finished']:
    # elif state == 'finished':
        fh.write("<p>Finished Jobs</p>")
        fh.write(print_table_start())
        print_jobs(jobs, fh)
        fh.write(print_table_end())
    elif args['all']:
    # elif state == 'all':
        # Write the running jobs.
        fh.write("<a name='finished'/>")
        fh.write("<p><b>Finished Jobs</b> - Go to list of <a href='#running'>running jobs</a></p>")
        print('\nFINISHED JOBS')
        fh.write(print_table_start())
        print_jobs(jobs_finished, fh)
        fh.write(print_table_end())
        # Write the finished jobs.
        fh.write("<a name='running'/>")
        fh.write("<p><b>Running Jobs</b> - Go to list of <a href='#finished'>finished jobs</a></p>")
        print('\nRUNNING JOBS')
        fh.write(print_table_start())
        print_jobs(jobs_running, fh)
        fh.write(print_table_end())
    else:
        # We should never get here.
        print("Invalid state %s" % state)

    fh.write(postfix)
    fh.close()
    print('\nWrote report %s ' % html_output)

    ###########################################################
    # Show additional information underneath the table of jobs.
    ###########################################################

    # Get the login id of the user that is running this program.
    # We can use either os.getuid() or os.geteuid() for effective uid.
    this_user = pwd.getpwuid( os.getuid() ).pw_name

    # For debugging you can uncomment this and add in a user
    # that has currently running jobs.
    this_user = 'u950654'

    # Get the UTS email of the user that is running this program.
    # Note that for admins with a local account this will be None.
    this_user_email = get_user_email(users_db_path, this_user)

    # This gets how this program was invoked as a string.
    invocation = ' '.join([str(s) for s in sys.argv])

    # Now print this information to the screen.
    print('\nTo rerun this, and email this report to yourself, run this command:')
    if this_user_email is not None:
        # We have an email for this user from the user database.
        print('  %s -e %s' % (invocation, this_user_email))
    else:
        # We do not have an email, as this user was not found in the user database.
        # This means they are running this and logged in with a local account i.e.
        # they are an admin user.
        # The admin user can email themselves.
        print('  %s -e your_email' % invocation)
        if user_id is not None:
            # The admin user can email this specific user.
            user_id_email = get_user_email(users_db_path, user_id)
            print('  %s -e %s' % (invocation, user_id_email))
    print("")

    ####################################################
    # Email a copy of the data as a HTML formatted file.
    ####################################################

    recipient_email = "Mike.Lake@uts.edu.au"
    this_user_email = "Mike.Lake@uts.edu.au"
    if recipient_email is not None:
        # An optional email address has been provided.
        if this_user_email is not None:
            # We have an email for this user from the user database.
            if this_user_email == recipient_email:
                send_email(from_email, this_user_email, html_output)
            else:
                print("The email was not sent. You can only send email to %s" % this_user_email)
        else:
            # The user running this script is an admin.
            print("Sent email to admin %s" % recipient_email)
            send_email(from_email, recipient_email, html_output)

if __name__ == '__main__':
    main()

