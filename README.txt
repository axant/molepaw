An easy and flexible tool to extract and mash up data from different sources and analyze, to visualize them to gain actionable info

internally it's called just etl https://en.wikipedia.org/wiki/Extract,_transform,_load

Installation and Setup
======================

Clone the repository::

    $ git clone http://github.com/axant/molepaw.git
    $ cd molepaw
    
Create a python2 virtualenv::

    $ virtualenv -p python2 venv
    $ source venv/bin/activate
    
Install ``etl`` using the setup.py script::

    $ pip install -e '.[testing]'

Create the project database for any model classes defined::

    $ gearbox setup-app

Start the paste http server::

    $ gearbox serve

While developing you may want the server to reload after changes in package files (or its dependencies) are saved. This can be achieved easily by adding the --reload option::

    $ gearbox serve --reload --debug

Then you are ready to go.
For further informations: https://turbogears.readthedocs.io/en/latest/cookbook/contributing/prepenv.html

Vagrant Environment
===================

You can use vagrant for both development and simulating a production environment. refer to the README inside ansible folder

Infrastructure
==============

- TurboGears2 - https://turbogears.readthedocs.io/en/latest/
- pandas - https://pandas.pydata.org/pandas-docs/stable/
- numpy - https://numpy.org/doc/
- ractive.js - https://ractive.js.org/
- bokeh - https://docs.bokeh.org/en/latest/index.html

First Steps
===========

login
-----
Once you got your instance of molepaw go on http://localhost:8080 and try to login with credentials
- username: admin
- password: adminpass
If it doesn't work: did you do the setup-app step successfully? check the credentials in ``etl/websetup/bootstrap.py``

Create a datasource
-------------------

Molepaw connects to datasources, them can be remote or local, can be sql databases (sqlalchemy), mongodb databases (ming), json or csv
let's set up a new datasource: go on ``admin/datasources/new`` and add the url and a name. see the folder ``etl/lib/dbsessions`` for internals.
Note that if you want to connect to mongodb you need to install ming with pip, as it's not a dependency of molepaw

Create a sataset
----------------

Datasets are derived from a datasource and you can specify a query that will be applied to the datasource
Datasets aren't extractions. an examples could be "users" (just the sql table) or "tickets sold for each day"

create first extraction
-----------------------
go in ``/extractions`` and press the add extraction button, add the name and save, then press edit on the new extraction.
press the biggest + button, select your dataset and then press the largest + button. You can join other datasets or create an extraction step using the + button below to produce your extraction.
example extractions could be "users by province" or "tickets sold for each cinema".

All extractions are exposed as html, csv and json, you could make a json datasource from an already created extracion

Production
==========

It's suggested to wrap molepaw with ``chausette`` and chausette in ``circus``. refer to the ansible playbook to set them up
https://pypi.org/project/chausette/
https://circus.readthedocs.io/en/latest/

Database Migrations
===================

Molepaw has 2 ways to migrate the db, choose your preferred one:

alembic
-------

Refer to https://alembic.sqlalchemy.org/en/latest/

tgext.evolve
------------

just create a new file in ``etl/config/evolutions`` and add it into ``etl/config/app_cfg.py``
Refer to https://github.com/axant/tgext.evolve
