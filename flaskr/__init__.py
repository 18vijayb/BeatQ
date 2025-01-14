import os
import requests
from flask import Flask, render_template, redirect, request, session, url_for, escape, make_response
from flaskr.User import User
from flaskr.extra_funcs import *
from flaskr.Assests import CookieException
from collections import deque
sessions = dict()
_client_key = "CLIENT-KEY-HERE"
_client_secret = "CLIENT-SECRET-HERE"

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
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp
            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)

        return render_template('home.html', page_name='BeatQ - Home')
    
    @app.route('/about')
    def about():
        if 'sessionID' in request.cookies:
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp
            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)
        return render_template('about.html', page_name='BeatQ - About')

    @app.route('/join_data', methods=["POST"])
    def join_data():
        global sessions

        if 'sessionID' in request.cookies:
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp
            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)

        name = request.form['username']
        session_id = request.form['code']

        if session_id in sessions:
            new_user = User(False, name, session_id)
            sessions[session_id]["users"][new_user.name] = new_user
            num_users=len(sessions[session_id]["users"])
            resp = make_response(render_template('dashboard.html', page_name="BeatQ - Dashboard", host = False, seshes = sessions, session_id = session_id, num_users = num_users))
            resp.set_cookie('sessionID', session_id)
            resp.set_cookie('identifier', new_user.name)
            return resp 
        else:
            return render_template('join.html', invalid = True, page_name="BeatQ - Join")

    
    @app.route('/spotifyAuth')
    def spotifyAuth():
        if 'sessionID' in request.cookies:
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp

            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)

        oauthUrl = 'https://accounts.spotify.com/authorize'
        oauthUrl += '?response_type=code'
        oauthUrl += '&client_id=' + _client_key # client key 
        oauthUrl += '&redirect_uri=http://127.0.0.1:5000/spotifyCallback'
        oauthUrl += '&scope=playlist-modify-public%20&playlist-modify-private%20&user-read-private%20&user-read-email'
        return redirect(oauthUrl,code=302)

    @app.route('/spotifyCallback', methods=['GET','POST'])
    def spotifyAuthCallback():      
        global sessions  

        if 'sessionID' in request.cookies:
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp

            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)

        code = request.args.get('code')
        tokenUrl = 'https://accounts.spotify.com/api/token'
        data = {'grant_type':'authorization_code',
                'code':code,
                'redirect_uri':'http://127.0.0.1:5000/spotifyCallback',
                'client_id':_client_key, # client key
                'client_secret':_client_secret # client secret
        }
        res = requests.post(tokenUrl,data=data)
        authorization_header = {'Authorization':'Bearer {}'.format(res.json()["access_token"]),
                                "Content-Type":"application/json"}
        userInformation = requests.get('https://api.spotify.com/v1/me',headers=authorization_header)
        
        
        random_code = rand_code()

        # instantiate a new session
        sessions[random_code] = dict()
        sessions[random_code]["host"] = userInformation.json()["display_name"]
        sessions[random_code]["users"] = dict()
        sessions[random_code]["songs"] = deque()
        sessions[random_code]["api_token"]=res.json()['access_token']
        sessions[random_code]["refresh_token"]=res.json()['refresh_token']

        create_playlist = "{\"name\":\"BeatQ "+random_code+"\"}"
        playlist_response = requests.post('https://api.spotify.com/v1/users/'+userInformation.json()["id"]+'/playlists',data=create_playlist,headers=authorization_header)
        print(playlist_response.json())
        sessions[random_code]["playlist_id"]=playlist_response.json()["id"]
        
        new_user = User(True, userInformation.json()["display_name"], random_code)
        sessions[random_code]["users"][new_user.name] = new_user

        num_users=len(sessions[random_code]["users"])
        resp = make_response(render_template('dashboard.html', page_name="BeatQ - Dashboard", host = True, seshes = sessions, session_id = random_code, num_users=len(sessions[random_code]["users"])))
        resp.set_cookie('sessionID', random_code)
        resp.set_cookie('identifier', new_user.name)
        return resp 
        
        
    
    @app.route('/join')
    def join():
        if 'sessionID' in request.cookies:
            try:
                host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
            except Exception as CookieException:
                resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
                resp.set_cookie('sessionID', '', expires=0)
                resp.set_cookie('identifier', '', expires=0)
                return resp

            num_users=len(sessions[request.cookies.get('sessionID')]["users"])
            return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)


        return render_template('join.html', page_name='BeatQ - Join')

    @app.route('/search',methods=["POST"])
    def search():
        global sessions
        data={
            'grant_type':'refresh_token',
            'refresh_token':sessions[request.cookies.get('sessionID')]["refresh_token"],
            'client_id':_client_key, # client key
            'client_secret':_client_secret # client secret
        }
        res=requests.post('https://accounts.spotify.com/api/token',data=data)
        sessions[request.cookies.get('sessionID')]["api_token"]=res.json()["access_token"]
        print(res.json()["access_token"])
        authorization_header = {"Authorization":"Bearer {}".format(sessions[request.cookies.get('sessionID')]["api_token"]),
                                "Content-Type":"application/json"}
        queryUrl = 'https://api.spotify.com/v1/search'
        queryUrl += '?q='+request.form['song']
        queryUrl += '&type=track'
        queryUrl += '&limit=10'
        song_list = requests.get(queryUrl,headers=authorization_header)
        song_names = list()
        song_uris = list()
        for i in song_list.json()["tracks"]["items"]:
            song_names.append(i["name"])
            song_uris.append(i["uri"])
        num_users=len(sessions[request.cookies.get('sessionID')]["users"])
        return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier')), seshes = sessions, session_id = request.cookies.get('sessionID'),song_names=song_names,song_uris=song_uris,num_users = num_users)

    @app.route('/dashboard',methods=["POST"])
    def dashboard():
        global sessions
        data={
            'grant_type':'refresh_token',
            'refresh_token':sessions[request.cookies.get('sessionID')]["refresh_token"],
            'client_id':_client_key,
            'client_secret':_client_secret
        }
        res=requests.post('https://accounts.spotify.com/api/token',data=data)
        sessions[request.cookies.get('sessionID')]["api_token"]=res.json()["access_token"]
        print(res.json()["access_token"])
        authorization_header = {"Authorization":"Bearer {}".format(sessions[request.cookies.get('sessionID')]["api_token"])}
        try:
            host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
        except Exception as CookieException:
            resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
            resp.set_cookie('sessionID', '', expires=0)
            resp.set_cookie('identifier', '', expires=0)
            return resp
            
        num_users=len(sessions[request.cookies.get('sessionID')]["users"])
        return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'), num_users = num_users)
    @app.route('/enqueue/',methods=["POST","GET"])
    def enqueue():
        global sessions
        song_name = request.args.get("name")
        song_uri = request.args.get("uri")
        data={
            'grant_type':'refresh_token',
            'refresh_token':sessions[request.cookies.get('sessionID')]["refresh_token"],
            'client_id':_client_key, # client key 
            'client_secret':_client_secret # client secret
        }
        res=requests.post('https://accounts.spotify.com/api/token',data=data)
        sessions[request.cookies.get('sessionID')]["api_token"]=res.json()["access_token"]
        print(res.json()["access_token"])
        print(sessions[request.cookies.get('sessionID')]["playlist_id"])
        authorization_header = {"Authorization":"Bearer {}".format(sessions[request.cookies.get('sessionID')]["api_token"]),
                                "Content-Type":"application/json"}
        queryUrl = '	https://api.spotify.com/v1/playlists/'
        queryUrl += sessions[request.cookies.get('sessionID')]["playlist_id"]+"/tracks"
        queryUrl += '?uris='+song_uri
        print(queryUrl)
        addTracks = requests.post(queryUrl,headers=authorization_header)
        try:
            host = is_host(sessions, request.cookies.get('sessionID'), request.cookies.get('identifier'))
        except Exception as CookieException:
            resp = make_response(render_template('home.html', page_name = "BeatQ - Home"))
            resp.set_cookie('sessionID', '', expires=0)
            resp.set_cookie('identifier', '', expires=0)
            return resp
        
        sessions[request.cookies.get('sessionID')]["users"][request.cookies.get('identifier')].add_song(song_name)

        return render_template('dashboard.html', page_name="BeatQ - Dashboard", host = host, seshes = sessions, session_id = request.cookies.get('sessionID'))
    return app
