from flask import Flask, render_template, request, url_for, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from oauth import OAuthSignIn
from flask_security import LoginForm, Security, SQLAlchemyUserDatastore, RoleMixin, login_required
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from flask_socketio import SocketIO, send, emit
import config
import requests
import json

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_ROOT
socketio = SocketIO(app, async_mode=async_mode)
app.config['OAUTH_CREDENTIALS'] = {
	'facebook':{
	'id': config.FB_APP_ID,
	'secret': config.FB_SECRET_KEY
},
    'spotify':{
    	'id':config.SPOTIFY_APP_ID,
    	'secret':config.SPOTIFY_SECRET_KEY
    }}

#app.config['SECURITY_POST_LOGIN_VIEW'] = '/'

db = SQLAlchemy(app)
ACCESS_TOKEN =  {}
REFRESH_TOKEN = None
PROFILE_DATA = None
user_data = []

# role model
class Role(db.Model, RoleMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50)),
	description = db.Column(db.String(255))


# user model
class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	social_id = db.Column(db.String(64), nullable=False, unique=True)
	email = db.Column(db.String(50))
	#password = db.Column(db.String(50))
	active = db.Column(db.Boolean)
	name = db.Column(db.String(50))


security = Security(app, SQLAlchemyUserDatastore(db, User, Role))
#Social(app, SQLAlchemyConnectionDatastore(db, Connection))


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/host")
def host():
    return render_template('host.html', async_mode=socketio.async_mode)


@app.route("/guest")
def guest():
    return render_template('guest.html', async_mode=socketio.async_mode)

@app.route("/host", methods = ['POST'])
def host_pause_guest():
    text = request.form['pause']
    processed_text = text.upper()
    print(processed_text)
    return pause(processed_text)


@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/guest_home')
def guest_home():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data =  json.loads(context_response.text)
    return render_template('guest_home.html', context_data=context_data)

@app.route('/host_home')
def host_home():
    return render_template('host_home.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/info')
def get_info():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    #print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data =  json.loads(context_response.text)
    print(context_data)
    return render_template('info.html', context_data=context_data)

"""
@app.route('/guest')
def get_info():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data =  json.loads(context_response.text)
    return render_template('info.html', context_data=context_data)
"""
@app.route('/pause')
def pause(user):
    access_token = ACCESS_TOKEN[str(user)]
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    pause_endpoint = "https://api.spotify.com/v1/me/player/pause"
    pause_response = requests.put(pause_endpoint, headers=auth_header)
    print(pause_response)
    return redirect(url_for('host'))

@app.route('/play') #TODO: correct url? same q for pause method
def play():
    #dummy header for other play method

    print(ACCESS_TOKEN)
    access_token = ACCESS_TOKEN[str(current_user.id)]
    # print("access token = " + access_token)
    auth_header = {"Authorization": "Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data = json.loads(context_response.text)
    print(json.dumps(context_data, indent=4, sort_keys=True))

    return play(context_data)

def play(song_info):
    #takes json song info and plays selected song at correct time
    #currently ASSUMES the user is not at the same point in song/same song as host

    #/me/player endpoint gives us song_info json

    #for /play endpoint
    context_uri = song_info['item']['uri'] #get context uri of song

    #for /seek endpoint
    position_ms = song_info['progress_ms']

    # hit /play endpoint
    access_token = ACCESS_TOKEN[str(current_user.id)]
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    play_endpoint = "https://api.spotify.com/v1/me/player/play"
    play_response = requests.put(play_endpoint, headers=auth_header, params={('context_uri', context_uri)})
    print(ACCESS_TOKEN)
    if play_response:
        print(play_response.text)


    #TODO:TESTING only! this next line
    position_ms = 100000

    # hit /seek endpoint
    seek_endpoint = "https://api.spotify.com/v1/me/player/seek"
    seek_response = requests.put(seek_endpoint, headers=auth_header, params={('position_ms', position_ms)})
    print(ACCESS_TOKEN)
    if seek_response:
        print(seek_response.text)
    return redirect(url_for('home'))


#@app.route('/showLogIn')
#def showLogIn():
#	return render_template('login.html')

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    access_token, social_id, username, email = oauth.callback()
    #PROFILE_DATA = profile_data
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, name=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    global ACCESS_TOKEN
    ACCESS_TOKEN[str(current_user.id)] = access_token
    return redirect(url_for('index'))

@socketio.on('my event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']})

@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/test')
def test_connect():
    print(current_user.id)
    emit('my response', {'data': current_user.id})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == "__main__":
    #db.create_all()
	socketio.run(app, debug=True)
