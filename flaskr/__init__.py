import os
import requests
from flask import Flask, render_template, redirect, request, session, url_for, escape, make_response
from flaskr.User import User
from flaskr.extra_funcs import *
from collections import deque

sessions = dict()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
 
    @app.route('/')
    def index():
        if 'sessionID' in request.cookies:
            return render_template('search.html')

        return render_template('home.html')
    
    @app.route('/about')
    def about():
        if 'sessionID' in request.cookies:
            return render_template('search.html')
        return render_template('about.html')

    @app.route('/join_data', methods=["POST"])
    def join_data():
        global sessions

        if 'sessionID' in request.cookies:
            return render_template('search.html')

        name = request.form['username']
        session_id = request.form['code']

        if session_id in sessions:
            new_user = User(False, name, session_id)
            sessions[session_id]["users"].append(new_user)
            return render_template('search.html')
        else:
            return render_template('join.html', invalid = True)

    
    @app.route('/spotifyAuth')
    def spotifyAuth():
        if 'sessionID' in request.cookies:
            return render_template('search.html')

        oauthUrl = 'https://accounts.spotify.com/authorize'
        oauthUrl += '?response_type=code'
        oauthUrl += '&client_id=32a33ef6be6f484aa7af70dbc0a8be74'
        oauthUrl += '&redirect_uri=http://localhost:5000/spotifyCallback'
        oauthUrl += '&scope=user-read-private%20&user-read-email'
        return redirect(oauthUrl,code=302)

    @app.route('/spotifyCallback', methods=['GET','POST'])
    def spotifyAuthCallback():      
        global sessions  

        if 'sessionID' in request.cookies:
            return render_template('search.html')

        code = request.args.get('code')
        tokenUrl = 'https://accounts.spotify.com/api/token'
        data = {'grant_type':'authorization_code',
                'code':code,
                'redirect_uri':'http://localhost:5000/spotifyCallback',
                'client_id':'32a33ef6be6f484aa7af70dbc0a8be74',
                'client_secret':'8c68f3903c78478ea18f9d18a79c7d13'
        }
        res = requests.post(tokenUrl,data=data)
        authorization_header = {"Authorization":"Bearer {}".format(res.json()['access_token'])}
        userInformation = requests.get('https://api.spotify.com/v1/me',headers=authorization_header)
        
        
        random_code = rand_code()

        # instantiate a new session
        sessions[random_code] = dict()
        sessions[random_code]["host"] = userInformation.json()["display_name"]
        sessions[random_code]["users"] = []
        sessions[random_code]["songs"] = deque()
        sessions[random_code]["api_token"]=res.json()['access_token']
        sessions[random_code]["refresh_token"]=res.json()['refresh_token']
        
        print(userInformation.json())
        
        new_user = User(True, userInformation.json()["display_name"], random_code)

        resp = make_response(render_template('search.html', random_code = random_code))
        resp.set_cookie('sessionID', random_code)
        resp.set_cookie('identifier', new_user.identifier)
        return resp 
        
        
    
    @app.route('/join')
    def join():
        if 'sessionID' in request.cookies:
            return render_template('search.html')

        return render_template('join.html')

    @app.route('/search',methods=["POST"])
    def search():
        global sessions
        data={
            'grant_type':'refresh_token',
            'refresh_token':sessions[request.cookies.get('sessionID')]["refresh_token"],
            'client_id':'32a33ef6be6f484aa7af70dbc0a8be74',
            'client_secret':'8c68f3903c78478ea18f9d18a79c7d13'
        }
        res=requests.post('https://accounts.spotify.com/api/token',data=data)
        sessions[request.cookies.get('sessionID')]["api_token"]=res.json()["access_token"]
        print(res.json()["access_token"])
        authorization_header = {"Authorization":"Bearer {}".format(sessions[request.cookies.get('sessionID')]["api_token"])}
        queryUrl = 'https://api.spotify.com/v1/search'
        queryUrl += '?q='+request.form['song']
        queryUrl += '&type=track'
        queryUrl += '&limit=10'
        song_list = requests.get(queryUrl,headers=authorization_header)
        return render_template('search.html')
    return app
