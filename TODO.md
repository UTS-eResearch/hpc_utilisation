# Mikes TODO

    $ python -m pip install --upgrade pip
    $ pip install pip-review
    $ pip install docopt


    wget https://raw.githubusercontent.com/pypa/virtualenv/main/src/virtualenv/activation/python/activate_this.py

Copy to: 
 
    $ cp activate_this.py /opt/eresearch/virtualenvs/hpc_utilisation/

<https://stackoverflow.com/questions/25020451/no-activate-this-py-file-in-venv-pyvenv>

    hpcnode01 hpc_utilisation/$ /opt/eresearch/hpc_utilisation/check_utilisation.py 
    Traceback (most recent call last):
      File "/opt/eresearch/hpc_utilisation/check_utilisation.py", line 48, in <module>
        exec(f.read(), dict(__file__=activate_this_file))
      File "<string>", line 10
    SyntaxError: future feature annotations is not defined
    hpcnode01 hpc_utilisation/$ 

Only issue is that the virtualenv docs are out of date for Python 3 (they claim
you use execfile, which doesn't exist). The Python 3 compatible alternative
would be:

    # Looted from virtualenv; should not require modification, since it's defined relatively
    activator = 'some/path/to/activate_this.py'
    with open(activator) as f:
        exec(f.read(), {'__file__': activator})

If so, then the error happens because according to PEP-563 the import of
__future__ annotations is available starting with Python 3.7.

