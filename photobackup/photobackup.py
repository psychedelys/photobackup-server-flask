#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of PhotoBackup.
#
# PhotoBackup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PhotoBackup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2015-2015 Psychedelys
#

"""

PhotoBackup Python Flask server.

"""

# stlib
import configparser
import os
import sys
from flask import Flask, render_template, request, redirect, abort
from werkzeug import secure_filename
from logbook import debug, info, warn, error
import pprint
import exifread
import re
import urllib

__version__ = "0.1.0"

app = Flask(__name__)
runPath = os.path.dirname(os.path.realpath(__file__))
cfg_file = runPath + '/../etc/configuration.ini'


def read_config():
    """ Set configuration file data into local dictionnary. """
    config = configparser.ConfigParser()
    try:
        config.read_file(open(cfg_file))
    except OSError as e:
        error("can't read configuration file %s. %s." % (cfg_file, str(e)))

    # Check if all keys are in the file
    keys = ['MediaRoot', 'Password', 'Port', 'Debug', 'Root_URL', 'Allowed_Extention']
    for key in keys:
        if key not in config['photobackup']:
            error("config file %s incomplete, please check!" % (cfg_file))
    return config['photobackup']


def end(code, message):
    error(message)
    abort(code, message)

re_date = re.compile(r'^(\d{4}):(\d{2}):(\d{2})\s', re.UNICODE | re.I)
pp = pprint.PrettyPrinter(indent=4)
config = read_config()

# TODO: Should be in config...
allowed_extention = ['.jpg', '.jpeg', '.mp4']
root_url = config['Root_URL']
Debug = config['Debug']

# Max must be the same as the nginx parameter client_max_body_size
# if nginx is used in front
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024


# Flask routes
@app.route(root_url, methods=['GET'], strict_slashes=False)
@app.route(root_url + '/', methods=['GET'], strict_slashes=False)
def index():
    # return 'Hello'
    debug("got a GET root call.")
    app.logger.debug('Query:'+pp.pformat(request))
    app.logger.debug('Query:'+pp.pformat(request.form))
    app.logger.debug('Query:'+pp.pformat(request.args))
    return ('', 204)
    # return redirect("https://photobackup.github.io/", code=302)


@app.route(root_url, methods=['POST'])
@app.route(root_url+'/<username>@<domain>', methods=['POST'])
def save_image(username, domain):
    debug("got a POST root call.")
    # app.logger.debug('Query:'+pp.pformat(request))
    # app.logger.debug('Query:'+pp.pformat(request.form))
    password = request.form.get('password')
    if password != config['Password']:
        error("password NOT ok.")
        end(403, "wrong password!")

    debug("ok: password")
    # app.logger.debug('File:'+pp.pformat(request.files))
    try:
        debug("ok: getlist %s." % (pp.pformat(request.getlists)))
    except Exception as e:
        debug("getlist failed %s." % (str(e)))

    try:
        upfile = request.files.get('upfile')
        # upfile = request.files['upfile']
    except Exception as e:
        debug("upfile request get failed %s." % (str(e)))

    if not upfile:
        error("no file in the request.")
        end(401, "no file in the request!")
    upfile1 = upfile

    debug("ok: file present in request.")
    # remove anypath inside the filename to insure against injection.
    # ex: upfil.raw_filename should not contain any '..'
    # already done by secure_filename
    # filename = os.path.basename(filename)
    try:
        filename = secure_filename(upfile.filename)
    except Exception as e:
        debug("secure_filename failed: %s:%s" % (upfile.filename, str(e)))

    debug("ok: secure_filename succeed %s" % filename)
    # Prevent uploading file with more than 1 dot.
    dotCount = filename.count('.')
    if dotCount != 1:
        error("file do contains more than 1 dot.")
        end(403, "file contains more than 1 dot!")

    debug("ok: file do not contains more than 1 dot.")
    # Prevent uploading from unwanted file which can be used for injection
    extension = os.path.splitext(filename)[1].lower()
    if extension not in allowed_extention:
        error("file extension NOT allowed '%s'." % extension)
        debug("error: allowed %s." % (pp.pformat(allowed_extention)))
        end(403, "file extension not allowed!")

    debug("ok: file extension allowed.")

    # app.logger.debug('Query:'+pp.pformat(upfile))

    # extract the exif date, to get the date
    try:
        tags = exifread.process_file(upfile)
        # for tag in tags.keys():
        #    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
        #        debug("Key: %s, value %s" % (tag, tags[tag]))
    except Exception as e:
        debug("exif not working %s" % str(e))

    debug("ok: got the img exif content")

    # EXIF DateTimeOriginal
    # value 2015:09:14 15:37:03
    try:
        if 'EXIF DateTimeOriginal' in tags:
            debug("ok: got exif EXIF DateTimeOriginal")
            date = str(tags['EXIF DateTimeOriginal'])
        elif 'Image DateTime' in tags:
            # generated PANO file
            debug("ok: got exif Image DateTime")
            date = str(tags['Image DateTime'])
        else:
            debug("hum, no date found in exif tag")
            date = ''
            for tag in tags.keys():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    debug("Key: %s, value %s" % (tag, tags[tag]))

        debug("ok, no exception up to now")
    except Exception as e:
        for tag in tags.keys():
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                debug("Key: %s, value %s" % (tag, tags[tag]))
        debug("error: failed to read date from read tags from array.")
        end(400, "oups, read tags from array")

    debug("ok: got exif date '%s'" % date)

    if username is not None and domain is not None:
        username = secure_filename(urllib.parse.quote_plus(username).lower())
        domain = secure_filename(urllib.parse.quote_plus(domain).lower())
        debug("username %s, domain %s" % (username, domain))
        basepath = os.path.join(config['MediaRoot'], domain, username)
    else:
        basepath = os.path.join(config['MediaRoot'])

    res = False
    try:
        res = re_date.match(date)
    except Exception as e:
        debug("error: failed to apply regex: %s " % str(e))
    if res:
        date_folder = res.group(1) + '_' + res.group(2) + '_' + res.group(3)
        debug("ok: exif passed '%s'." % date_folder)
        filedir = os.path.join(basepath, date_folder)
    else:
        debug("error: could not find date in string '%s'" % date)
        filedir = os.path.join(basepath)

    debug("ok: using folder '%s'." % filedir)

    filepath = os.path.join(filedir, filename)
    if not os.path.isdir(filedir):
        debug("Need to create folder %s on system." % (filedir))
        try:
            os.makedirs(filedir)
        except Exception as e:
            debug("error: Cannot create folder %s" % str(e))
            end(400, "oups, cannot create directory '%s'." % (str(e)))

    if not os.path.isfile(filepath):
        debug("Storing file %s on system." % (filepath))
        filesize = -1
        try:
            filesize = int(request.form.get('filesize'))
        except TypeError as e:
            debug("error: %s" % str(e))
            end(400, "missing file size in the request!")
        except Exception as e:
            debug("error: %s" % str(e))
            end(400, "missing file size in the request!")

        # save file
        debug("upfile path: '%s'." % (filepath))
        upfile.seek(0, os.SEEK_SET)
        upfile.save(filepath)

        # check file size in request against written file size
        if filesize != os.stat(filepath).st_size:
            debug("error: file sizes do not match '%s' <> '%s'." % (filesize, os.stat(filepath).st_size))
            end(411, "file sizes do not match!")

        return ('', 200)

    else:
        warn("file " + filepath + " already exists")
        filesize = -1
        try:
            filesize = int(request.form.get('filesize'))
        except TypeError as e:
            debug("error: %s" % str(e))
            end(400, "missing file size in the request!")
        except Exception as e:
            debug("error: %s" % str(e))
            end(400, "missing file size in the request!")

        debug("ok: got filesize from header '%s'." % filesize)

        # check file size in request against written file size
        if filesize != os.stat(filepath).st_size:
            debug("error: file sizes do not match '%s' <> '%s'" % (filesize, os.stat(filepath).st_size))
            end(411, "file sizes do not match!")

        return ('', 200)


@app.route(root_url + '/<test>', methods=['POST'])
@app.route(root_url + '/<username>@<domain>/<test>', methods=['POST'], strict_slashes=False)
def test(username, domain, test):
    debug("got a POST call is param test.")
    if test is not None and test == 'test':
        debug("got a POST test call.")
        app.logger.debug('Query:'+pp.pformat(request))
        app.logger.debug('Query:'+pp.pformat(request.form))
        password = request.form.get('password')
        if password != config['Password']:
            end(403, "wrong password!")

        if not os.path.exists(config['MediaRoot']):
            debug("ERROR: MEDIA_ROOT does not exist!")
            end(500, "MEDIA_ROOT does not exist!")

        testfile = os.path.join(config['MediaRoot'], '.test_file_to_write')
        debug("testfile is %s" % (testfile))
        try:
            with open(testfile, 'w') as tf:
                tf.write('')
        except Exception as e:
            debug("ERROR: Can't write to MEDIA_ROOT: %s" % str(e))
            end(500, "Can't write to MEDIA_ROOT!")
        finally:
            os.remove(testfile)
            debug("Test succeeded \o/")
            return ('', 200)
    else:
        debug("ERROR: Bad call, parameter not supported '%s'." % (test))
        end(500, "Bad call!")


if __name__ == '__main__':
    app.debug = Debug
    flaskHost = '192.168.44.65'
    flaskPort = int(config['Port'])
    flaskDebug = Debug
    app.run(host=flaskHost, port=flaskPort, debug=flaskDebug)
