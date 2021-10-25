# hpc_utilisation

Python program to check the utilisation of HPC jobs using the PBS schedular.

In the Python code the `users_db_name` is a small sqlite database that just contains user information.
The schema is:

    $ echo '.schema' | sqlite3 users_ldap_public.db
    CREATE TABLE IF NOT EXISTS "users" ( 'id' INTEGER NOT NULL, 'uts_id' TEXT NOT NULL, 'uts_email' TEXT, 'name' TEXT, PRIMARY KEY('id'));


