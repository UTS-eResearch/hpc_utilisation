#!/bin/bash

# Create a copy of the HPC users database from the current production one but
# with less fields. This database is used by the program: check_utilisation.py

# In sqlite you cannot remove columns. The way to remove a column is to copy
# the existing database to a new database, and create a new table, with just
# the fields that you want, from the old table. Then you can drop the old 
# table and rename the table you want.

# The input database we will be copying fields from and the 
# output database we will be copying fields into.
db_in="users_ldap.db"
db_out="users_ldap_public.db"

if [ ! -f $db_in ]; then
    echo "Missing input database, $db_in, so exiting."
    exit 0
fi

# Copy the full database to a new one.
cp $db_in $db_out

# Create a new table.
SQL="CREATE TABLE IF NOT EXISTS 'users_public' ('id' INTEGER NOT NULL, 'uts_id' TEXT NOT NULL, 'uts_email' TEXT, 'name' TEXT, PRIMARY KEY('id'));"
echo "$SQL" | sqlite3 $db_out

# Copy the data from the old table into the new table.
# Note we only copy across current, valid users.
SQL="INSERT INTO users_public SELECT id, uts_id, uts_email, name FROM users where status=2;"
echo "$SQL" | sqlite3 $db_out

# Drop the old table.
SQL="DROP TABLE IF EXISTS users;"
echo "$SQL" | sqlite3 $db_out

# Rename the new table to the old name.
SQL="ALTER TABLE users_public RENAME TO users;"
echo "$SQL" | sqlite3 $db_out

# This can be uncommented to check the data.
#SQL="select * from users;"
#echo "$SQL" | sqlite3 users_ldap_public.db
#echo '.schema' | sqlite3 users_ldap_public.db

