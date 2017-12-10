from flask import Flask, render_template, request, url_for, request, redirect, \
    session, flash, jsonify, send_from_directory
from threading import Lock
from flask_sqlalchemy import SQLAlchemy
from oauth import OAuthSignIn
from flask_security import LoginForm, Security, SQLAlchemyUserDatastore, RoleMixin, login_required
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from flask_socketio import SocketIO, send, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import config
import requests
import json
from collections import defaultdict
from array import array



async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQL_ROOT
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
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
hostl = []
SESSION_USERS = defaultdict(list)

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

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')



@app.route("/")
def index():
    if current_user.is_anonymous or not str(current_user.id) in ACCESS_TOKEN:
        return redirect(url_for('oauth_authorize', provider='spotify'))
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/guest")
def guest():
    return render_template('guest.html', async_mode=socketio.async_mode)

@app.route("/guest", methods = ['POST'])
def guest_sesh_join():
    text = request.form['sname']
    processed_text = text.upper()
    if processed_text in SESSION_USERS.keys():
        SESSION_USERS[processed_text].append(tuple((current_user.name,current_user.id)))
        sessioninfo = SESSION_USERS[processed_text]
        print("Success")
        return redirect(url_for('room', sessionname = processed_text))
    else:
        sessioninfo = "Session does not exist"
        print(sessioninfo)
        return render_template('guest.html',sessioninfo = sessioninfo)

@app.route("/host")
def host():
    #hostl.append(current_user.id)
    return render_template('host.html', async_mode=socketio.async_mode)

@app.route("/host", methods = ['POST'])
def host_sesh_create():
        text = request.form['sname']
        processed_text = text.upper()
        if processed_text in SESSION_USERS:
            sessionerror = "ERROR, SESSION ALREADY EXISTS"
            return redirect(url_for('host', sessionerror=sessionerror))
        SESSION_USERS[processed_text].append(tuple((current_user.name,current_user.id)))
        hostl.append(current_user.name)
        sessioninfo = SESSION_USERS[processed_text]
        return redirect(url_for('loading', sessionname = processed_text))

@app.route('/get_data/<sessionname>')
def get_data(sessionname):
    in_session = ""
    users = SESSION_USERS[sessionname]
    for user in users:
        in_session += ("\n" + user[0])
    return in_session

@app.route('/loading/<sessionname>')
def loading(sessionname):
	return render_template('loading.html', sessionname=sessionname, in_session= get_data(sessionname))

@app.route('/room/<sessionname>')
def room(sessionname):
    hosts = hostl
    access_token = ACCESS_TOKEN[str(current_user.id)]
    auth_header = {"Authorization":"Bearer {}".format(access_token)}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data =  json.loads(context_response.text)

    # eventbrite info
    artists = context_data['item']['artists']
    access_token = "ST6W4BKCJNWSDELYV7SS"
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    event_endpoint = "https://www.eventbriteapi.com/v3/events/search/"

    events = []
    for artist in artists:
        query = artist['name']
        event_response = requests.get(event_endpoint, headers=auth_header, params={('q', query)})
        for i in range(5):
            try:
                link = event_response.json()['events'][i]['url']
                event = (event_response.json()['events'][i]['name']['text'], link)
                events.append(event)
            except:
                print("tried to get too many events")
    print(events)
    return render_template('room.html', hosts=hosts, context_data=context_data, sessionname=sessionname, events=events)

"""
@app.route('/guest_home')
def guest_home():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(access_token)}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    if context_response:
        context_data =  json.loads(context_response.text)
    return render_template('guest_home.html', context_data=context_data)

@app.route('/host_home')
def host_home():
    access_token = ACCESS_TOKEN[str(current_user.id)]
    print("access token = " + access_token)
    auth_header = {"Authorization":"Bearer {}".format(ACCESS_TOKEN[str(current_user.id)])}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    if context_response:
        context_data = context_response.json()
    return render_template('host_home.html', context_data=context_data)
<<<<<<< HEAD
"""

@app.route('/logout')
def logout():
    logout_user()
    return render_template(url_for('home'))

@app.route('/exit')
def exit():
    print("CURRENT DICT = ", SESSION_USERS)
    for value in SESSION_USERS.values():
        if tuple((current_user.name,current_user.id)) in value:
            print('exit!!!')
            value.remove(tuple((current_user.name,current_user.id)))
    print("NEW DICT = ", SESSION_USERS)
    return render_template('home.html')

@app.route('/end')
def end():
    print("CURRENT DICT = ", SESSION_USERS)
    for key, values in SESSION_USERS.iteritems():
        if current_user.name in values[0]:
            del SESSION_USERS[key]
            hostl.remove(current_user.name)
            break
    print("NEW DICT = ", SESSION_USERS)
    return render_template('home.html')

@app.route('/info/<sessionname>')
def get_info(sessionname):
    print("MY_PRINT:", SESSION_USERS)
    in_session = ""
    session_id = ""
    host = ""
    for key in SESSION_USERS.keys():
        if sessionname == key:
            session_id = key
            for x in SESSION_USERS[key]:
                print hostl
                if x[0] in hostl:
                    host = x[0]
                else:
                    in_session += ("\n" + x[0])

    access_token = ACCESS_TOKEN[str(current_user.id)]
    print(access_token)
    auth_header = {"Authorization":"Bearer {}".format(access_token)}
    print(auth_header)
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    print(context_response.json())
    context_data = context_response.json()
    print(context_data)
    return render_template('info.html', session_id=session_id, in_session=in_session, host=host, context_data=context_data, sessionname=sessionname)

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
@app.route('/pause/<session>')
def pause(session):
    users = SESSION_USERS[session]
    hosts = hostl
    for user in users:
        access_token = ACCESS_TOKEN[str(user[1])]
        auth_header = {"Authorization": "Bearer {}".format(access_token)}
        pause_endpoint = "https://api.spotify.com/v1/me/player/pause"
        pause_response = requests.put(pause_endpoint, headers=auth_header)
        print(pause_response)
    return redirect(url_for('room', sessionname = session, hosts = hosts))

@app.route('/play/<session>') #TODO: correct url? same q for pause method
def play(session):
    #dummy header for other play method

    access_token = ACCESS_TOKEN[str(current_user.id)]
    # print("access token = " + access_token)
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    context_endpoint = "https://api.spotify.com/v1/me/player"
    context_response = requests.get(context_endpoint, headers=auth_header)
    context_data = context_response.json()
    print(json.dumps(context_data, indent=4, sort_keys=True))

    return play(context_data, session)

def play(song_info,session):
    #takes json song info and plays selected song at correct time
    #currently ASSUMES the user is not at the same point in song/same song as host

    #/me/player endpoint gives us song_info json

    #for /play endpoint
    hosts = hostl
    context = song_info['item']
    print(context)
    track = (song_info['item']['track_number'])-1 #get context uri of song
    trackname = song_info['item']
    context_uri = song_info['item']['album']['uri']
    print(track)
    print(context_uri)

    #for /seek endpoint
    position_ms = song_info['progress_ms']

    # hit /play endpoint
    users = SESSION_USERS[session]
    for user in users:
        access_token = ACCESS_TOKEN[str(user[1])]
        auth_header = {"Authorization": "Bearer {}".format(access_token)}
        play_endpoint = "https://api.spotify.com/v1/me/player/play"
        payload = {'context_uri': context_uri,
                   'offset': {'position': track}}
        play_response = requests.put(play_endpoint,
                                     data = json.dumps(payload),
                                     headers=auth_header,
                                     )
        print("play_respnse" + play_response.text)
      # if play_response:
       #     print("play response =" + play_response.text)

        #hit /seek endpoint
        seek_endpoint = "https://api.spotify.com/v1/me/player/seek"
        seek_response = requests.put(seek_endpoint, headers=auth_header, params={('position_ms', position_ms),})
        #if seek_response:
         #   print(seek_response.text)
    return redirect(url_for('room', sessionname = session, hosts = hosts))


#@app.route('/showLogIn')
#def showLogIn():
#	return render_template('login.html')

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    # if not current_user.is_anonymous:
    #     return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        logout_user()
        print("logout success")
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
    # global ACCESS_TOKEN
    ACCESS_TOKEN[str(current_user.id)] = access_token
    return redirect(url_for('index'))


"""
@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()



@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})
"""

if __name__ == "__main__":
    #db.create_all()
	socketio.run(app, debug=True)
