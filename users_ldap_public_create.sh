#!/bin/bash

# Create users_ldap_public.db with less fields.
# This database is used by the program: check_utilisation.py

# In sqlite you cannot remove columns. The way to remove a column is to copy
# the existing database to a new database, and create a new table, with just
# the fields that you want, from the old table. Then you can drop the old 
# table and rename the table you want.
 
# Copy the full database to a new one.
cp users_ldap.db users_ldap_public.db

# Create a new table.
SQL="CREATE TABLE IF NOT EXISTS 'users_public' ('id' INTEGER NOT NULL, 'uts_id' TEXT NOT NULL, 'uts_email' TEXT, 'name' TEXT, PRIMARY KEY('id'));"
echo "$SQL" | sqlite3 users_ldap_public.db

# Copy the data from the old table into the new table.
# Note we only copy across current, valid users.
SQL="INSERT INTO users_public SELECT id, uts_id, uts_email, name FROM users where status=2;"
echo "$SQL" | sqlite3 users_ldap_public.db

# Drop the old table.
SQL="DROP TABLE IF EXISTS users;"
echo "$SQL" | sqlite3 users_ldap_public.db

# Rename the new table to the old name.
SQL="ALTER TABLE users_public RENAME TO users;"
echo "$SQL" | sqlite3 users_ldap_public.db

# This can be uncommented to check the data.
#SQL="select * from users;"
#echo "$SQL" | sqlite3 users_ldap_public.db
#echo '.schema' | sqlite3 users_ldap_public.db

