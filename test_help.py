#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This is just to test how Python help via docopt works.

Usage: 
  check_utilisation.py running
  check_utilisation.py finished 
  check_utilisation.py all
  check_utilisation.py (-h | --help)

Options:
  -e, --email <email>    Email a copy of this report to yourself.
  -u, --user  <user>     Only show jobs for this user.

Author: Mike Lake
Releases: 
  2021-04-29 First release.
'''

import sys, os
import pwd

#import argparse
from docopt import docopt

from_email = 'Mike.Lake@uts.edu.au'
state = 'all'

# Append what ever pbs directory is under the directory that this script is located
# in. This ensures that we use /opt/eresearch/pbs for the version used by users and 
# whatever pbs is under this script if its a development version.
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), 'pbs'))

def main():
    '''
    test
    '''
    #arguments = docopt(__doc__)
    args = docopt(__doc__, argv=None, help=True, version=None, options_first=False)

    '''
    # I have replaced the default help's message with a clearer one.
    parser = argparse.ArgumentParser(\
        description='Check Your HPC Utilisation', \
        usage="%(prog)s  running|finished|all  [-h] [-u USER] [-e EMAIL]", \
        epilog='Contact %s for further help.' % from_email, \
    )

    parser.add_argument('state', choices=['running','finished','all'], default='running', \
        help='Select one job state to report on.')
    parser.add_argument('-u', '--user', help='Only show jobs for this user.')
    parser.add_argument('-e', '--email', help='Email a copy of this report to yourself.')
   
    args = parser.parse_args()
    state = args.state
    user_id = args.user
    recipient_email = args.email
    '''

    print("\nChecking utilisation for jobs ")
    #print(argv)
    print(args)
    if state == 'running':
        print('Found  running jobs out of  total jobs.')
    elif state == 'finished':
        print('Found  finished jobs from last  days.')
    elif state == 'all':
        print('Found  finished jobs from last  days.') 

    else:
        # We should never get here.
        print("Invalid state %s" % state)
        sys.exit()

if __name__ == '__main__':
    main()

