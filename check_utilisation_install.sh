#!/bin/bash

# Installs the check_utilisation.py Python script and its dependencies.
# TODO This would be placed in /usr/local/bin so it can be run by users 
# but it is still being worked on so its not installed for now.
#
# Usage: bash ./check_utilisation_install.sh

dest="/opt/eresearch"

# Check the public users database is up-to-date with the private one.
num1=$(echo 'select count(id) from users;' | sqlite3 users_ldap.db)
num2=$(echo 'select count(id) from users;' | sqlite3 users_ldap_public.db)

if [ $num1 -ne $num2 ]; then
    echo "Number of users in each database does not match ($num1 & $num2) so updating public database..."
    ./users_ldap_public_create.sh
else
    echo "Number of users in each database is the same."
fi

# Now do the install.

#mkdir -p ${dest}/pbs
#cp pbs/pbs.py ${dest}/pbs
#cp pbs/_pbs.so ${dest}/pbs
#cp pbs/pbsutils.py ${dest}/pbs
#cp check_utilisation.py ${dest}
#cp users_ldap_public.db ${dest}
#chmod ugo+x ${dest}/check_utilisation.py

