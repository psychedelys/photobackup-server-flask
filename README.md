# PhotoBackup Python server

The Python3 implementation of PhotoBackup server, made with
[Flask](http://flask.pocoo.org/). It follows more or less the
[official API](https://github.com/PhotoBackup/api/blob/master/api.raml).

Well, this is a first try to support a multi-user backup system,
the Android application to be used are:

    https://github.com/PhotoBackup/client-android

The url to be used are in the form:

    https://your-server.exemple.org/photobackup/user@yourdomain.org/

But, for now, the password are for now the same for all users.

Well your photos are automatically sorted by in the form, based on URL and exif tags:

    MediaRoot/yourdomain.org/user/yyyy_mm_dd/your-picture.jpg


On Debian, you need to install the following dependancies:

    apt-get install nginx uwsgi uwsgi-plugin-python3 python3-flask python3-logbook python3-urllib3 python-configparser


## Installation

    git clone https://github.com/psychedelys/photobackup-server-flask.git 

* Copy the config template to config production

    cp ./etc/configuration.ini.sample ./etc/configuration.ini

* Edit the config production

    editor_troll ./etc/configuration.ini

* Get the exifread folder from https://github.com/ianare/exif-py.git


## Usage

* Run-it as it, to test dependancy or to run-it without uwsgi:

    python3 photobackup/photobackup.py

* Run-it using uwsgi with Nginx in front

    cp contrib/nginx/photobackup /etc/nginx/sites-available/
    ln -s /etc/nginx/sites-available/photobackup /etc/nginx/sites-enabled/
    cp contrib/uwsgi/photobackup.ini /etc/uwsgi/apps-available/
    ln -s /etc/uwsgi/apps-available/photobackup.ini /etc/uwsgi/apps-enabled/

* Manual testing of uwsgi:

    uwsgi --plugins python3 --master --module photobackup.photobackup --callable app --protocol=http --socket :8240


## Production

It's better to use [uwsgi](http://uwsgi-docs.readthedocs.org/en/latest/),
or something like [gunicorn](http://gunicorn.org/)
behind your webserver.
