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
ACCESS_TOKEN = {}
REFRESH_TOKEN = None
PROFILE_DATA = None

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

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/info')
def get_info():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data =  json.loads(context_response.text)
    return render_template('info.html', context_data=context_data)

@app.route('/pause')
def pause():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    pause_endpoint = "https://api.spotify.com/v1/me/player/pause"
    pause_response = requests.put(pause_endpoint, headers=auth_header)
    print(pause_response)
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
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == "__main__":
	socketio.run(app, debug=True)
