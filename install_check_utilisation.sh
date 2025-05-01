#!/bin/bash

# Installs the check_utilisation.py Python script and its dependencies.
#
# Usage: ./install_check_utilisation.sh

# Set here the location of where the script will be installed to.
# The "pbs" directory will be installed under here as well.
# Do not use a trailing slash here.
dest="/opt/eresearch/hpc_utilisation"

# Nothing else below here needs to be changed.

# The name of the script to modify and install.
script=check_utilisation.py

function create_venv {
    # Create a Python virtual env.
    # /opt/eresearch/virtualenvs needs to already exist and be writable by the user of this script.
    # chown -R mlake:mlake /opt/eresearch/virtualenvs/hpc_utilisation/
    pushd /opt/eresearch/virtualenvs
    python3.8 -m venv hpc_utilisation --prompt HPC_Utilisation
    source /opt/eresearch/virtualenvs/hpc_utilisation/bin/activate
    python -m pip install --upgrade pip
    pip install pip-review
    pip install docopt
    popd
}

# Check the public users database is up-to-date with the private one
# by doing a quick check of the number of entries.  If you are not using 
# this db then comment out this section.
num1=$(echo 'select count(id) from users;' | sqlite3 users_ldap.db)
num2=$(echo 'select count(id) from users;' | sqlite3 users_ldap_public.db)

if [ $num1 -ne $num2 ]; then
    echo "Number of users in each database does not match ($num1 & $num2) so updating public database..."
    ./users_ldap_public_create.sh
else
    echo "Number of users in each database is the same. Good."
fi

# Replace settings with UTS specific values.
cat $script | \
sed "s/^from_email = 'YourEmail@example.com'/from_email = 'Mike.Lake@uts.edu.au'/" | \
sed "s/^mail_server = 'postoffice.example.com'/mail_server = 'postoffice.uts.edu.au'/" > tmp.py

# Now do the install.
create_venv

sudo mkdir -p ${dest}
sudo chgrp mlake ${dest}
sudo chmod 775 ${dest}

#mkdir -p ${dest}/pbs
#cp pbs/pbs.py ${dest}/pbs
#cp pbs/_pbs.so ${dest}/pbs
#cp pbs/pbsutils.py ${dest}/pbs

mv tmp.py ${dest}/check_utilisation.py
cp users_ldap_public.db ${dest}
# This will allow any user to run the script.
chmod ugo+x ${dest}/check_utilisation.py
chmod o-x ${dest}/check_utilisation.py
rm -f tmp.py

