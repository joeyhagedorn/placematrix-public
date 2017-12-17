'''
Simple application to reimplement Reddit Place, but in the physical world
by toggling on and off LEDs on a Boldport p11-TheMatrix
https://en.wikipedia.org/wiki/Place_(Reddit)

Author: Joey Hagedorn - joey@joeyhagedorn.com

https://www.joeyhagedorn.com/
'''

from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for
from requests_futures.sessions import FuturesSession
from oauth2client import client, crypt
from application import db
from application.models import Placement, Representation, User
import urllib2, urllib
from string import digits
import json
import time
import base64
import sys
import hashlib

application = Flask(__name__, static_url_path='')
application.debug=False
application.secret_key = 'REDACTED'

application.config["GOOGLE_LOGIN_CLIENT_ID"] = "REDACTED"
application.config["GOOGLE_LOGIN_CLIENT_SECRET"] = "REDACTED"

frozenDigits = frozenset(digits)
httpsession = FuturesSession()

#pages
@application.route('/', methods=['GET', 'POST'])
@application.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@application.route('/log', methods=['POST', 'GET'])
def log():
    error = None
    if request.method == 'GET':
        try:
            query_db = Placement.query.order_by(Placement.id.desc()).limit(10000)
            num_return = Placement.query.count()
            representation = Representation.query.order_by(Representation.id.desc()).first()
            prefixsuffix = "+------------------------+"
            lines = [prefixsuffix]
            changedBitmap = representation.bitmap.replace('1', '*')
            changedBitmap = changedBitmap.replace('0', ' ')
            for i in xrange(0, len(changedBitmap), 24):
                line = "|"+changedBitmap[i:i+24]+"|"
                lines.append(line)
            lines.append(prefixsuffix)
            bitmapString = '\n'.join(lines)
            usercount = User.query.count()
        except:
            print("Unexpected error in Log:", sys.exc_info()[0])
        finally:
            db.session.close()

        return render_template('log.html', results = query_db, bitmap=bitmapString, num=num_return, usercount = usercount)

""" Demo Only """
"""
@application.route('/replay', methods=['POST', 'GET'])
def replay():
    error = None
    if request.method == 'GET':
        delay = "0.5"
        try:
            delay = request.args.get('delay')
        except:
            print("No Delay Arg, using 0.5 sec default")

        try:
            bytes = bytearray(15)
            for placement in Placement.query.order_by(Placement.id).limit(10000):
                index = placement.y * 24 + placement.x
                mask = 1 << (index % 8)
                bytes[index / 8] ^= mask
                time.sleep(float(delay))
                sendBitmapBytesToParticle(bytes)

        except:
            print("Unexpected error in Log:", sys.exc_info()[0])
        finally:
            db.session.close()

        return render_template('404.html')
"""

#json based API
@application.route('/toggle', methods=['POST', 'GET'])
def toggle():
    error = None
    success = 0
    if request.method == 'POST':
        coord = request.form['coord']
        id_token = request.form['id_token']
        profile = verifyToken(id_token)
        partialSuccess = createOrUpdateUser(profile)
        if (partialSuccess and profile != None and isUserEligibleToPlace(profile["sub"])):
            success = togglePixel(profile["sub"], coord)
    response = {"success" : success}
    if (profile != None):
        response["secondsUntilNextPlacement"] = secondsUntilNextPlacement(profile["sub"])
    return jsonify(response)

@application.route('/login', methods=['GET', 'POST'])
def login():
    id_token = request.form['id_token']
    profile = verifyToken(id_token)
    success = createOrUpdateUser(profile)
    response = {"success" : success}
    if (profile != None):
        response["secondsUntilNextPlacement"] = secondsUntilNextPlacement(profile["sub"])
    return jsonify(response)

@application.route('/secondsUntilNextPlacement', methods=['GET', 'POST'])
def secondsUntilNextPlacement():
    id_token = request.form['id_token']
    profile = verifyToken(token)
    success = (profile != None)
    response = {"success" : success}
    if (profile != None):
        response["secondsUntilNextPlacement"] = secondsUntilNextPlacement(profile["sub"])
    return jsonify(response)

#errors & static files
@application.route('/static/<path:path>', methods=['GET'])
def staticfiles(path):
    return send_from_directory('static', path)

@application.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@application.before_request
def before_request():
    if "X-Forwarded-Proto" in request.headers:
        if (request.headers["X-Forwarded-Proto"] == "http"):
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

#template processing
@application.context_processor
def sha256_value():
    def sha256(value):
        salt = 'REDACTED(random-64-char-long-hex-string)'
        return hashlib.sha256(value + salt).hexdigest()
    return dict(sha256=sha256)

# Pixel Toggling
def togglePixel(user, coord):
    result = 0
    valid, x, y = validxyFromCoord(coord)
    if (valid):
        queryResult = Representation.query.order_by(Representation.id.desc()).first()
        try:
            if (queryResult == None):
                latestRep = Representation('0'*(5*24))
                db.session.add(latestRep)
            else:
                latestRep = queryResult

            index = y * 24 + x
            lst = list(latestRep.bitmap)
            if (lst[index] == '0'):
                lst[index] = '1'
            else :
                lst[index] = '0'
            latestRep.bitmap = ''.join(lst)

            bytes = bytearray(15)
            index = 0
            for byte in range(0, 15):
                for bit in range(0, 8):
                    if (latestRep.bitmap[index] == '0'):
                        bytes[byte] = (bytes[byte] & ~(1 << bit))
                    else:
                        bytes[byte] = (bytes[byte] | (1 << bit))
                    index = index + 1

            placement = Placement(user, x, y)
            db.session.add(placement)
            user = User.query.filter(User.user_id==user).order_by(User.user_id.desc()).first()
            user.nextPlacementEligibleAt = calculateNextPlacementEligibilityFromNow()
            db.session.commit()
            result = 1
        except:
            print("Error: Unexpected error in pixel placement, rolling back:", sys.exc_info()[0])
            db.session.rollback()
        finally:
            sendBitmapBytesToParticle(bytes)
            db.session.close()

    return result

def validxyFromCoord(coord):
    valid = False
    x = 0
    y = 0
    numbersOnly = ''.join(c for c in coord if c in frozenDigits)
    if (len(numbersOnly) == 4):
        intX = int(numbersOnly[0:2])
        intY = int(numbersOnly[2:4])
        if (intX >= 0 and intX < 24 and intY >=0 and intY < 5):
            valid = True
            x = intX
            y = intY
    return (valid, x, y)

#particle communication
def particleAPIRequestDidFinish(session, response):
    if (response.status_code != 200):
        print "Particle API Communication Failed"
        print response.status_code
        print response.text
        return
    jsonResult = json.loads(response.text)
    if (jsonResult["return_value"] != 0):
        print "Particle API Communication Failed"
        print jsonResult
    return

def sendBitmapBytesToParticle(bytes):
    b64Encoded = base64.b64encode(bytes)
    url = 'https://api.particle.io/v1/devices/REDACTED/write'
    data = {'access_token' : 'REDACTED', 'arg' : b64Encoded}
    httpsession.post(url, data=data, background_callback=particleAPIRequestDidFinish)

# User/Token/Timing/Validation
def verifyToken(token):
    try:
        idinfo = client.verify_id_token(token, application.config["GOOGLE_LOGIN_CLIENT_ID"])
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError:
        return None
    return idinfo

def calculateNextPlacementEligibilityFromNow():
    count = User.query.count()
    #return int(time.time() + 3)
    delay = min(count * 5 + 30, 300)
    return int(time.time() + delay)

def isUserEligibleToPlace(userid):
    if (secondsUntilNextPlacement(userid) < 0.0):
        return True
    else:
        return False

def secondsUntilNextPlacement(userid):
    if (userid == None):
        return 0
    queryResult = User.query.filter(User.user_id==userid).first()
    if (queryResult == None):
        return 0
    if (queryResult.banned == True):
        print "Access denied for banned user: " + queryResult.user_id
        return 300
    return queryResult.nextPlacementEligibleAt - time.time()

def createOrUpdateUser(profile):
    result = 0
    if (profile == None):
        return result

    try:
        user = User(profile["name"], profile["given_name"], profile["family_name"], profile["sub"], profile["email"], profile["picture"], profile["locale"])

        db.session.merge(user)
        db.session.commit()
        result = 1
    except:
        db.session.rollback()
        print("Error Unexpected error in createOrUpdateUser:", sys.exc_info()[0])
    finally:
        db.session.close()

    return result

if __name__ == '__main__':
    application.run(host='0.0.0.0')
