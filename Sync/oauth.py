import json
from rauth import OAuth2Service, OAuth1Service
from flask import current_app, url_for, request, redirect, session
#import BaseHTTPServer
#import SocketServer
import base64
import requests

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            decoder=decode_json
        )
        #access_token = oauth_session.access_token_response.json()['access_token']
        #print('access token ='+ access_token)
        me = oauth_session.get('me?fields=id, email').json()
        #print(me['id'])
        return (
            'facebook$' + me['id'],
            me.get('email').split('@')[0],  # Facebook does not provide
                                            # username, so the email
                                            # is used instead
            me.get('email')
        )

class SpotifySignIn(OAuthSignIn):
    def __init__(self):
        super(SpotifySignIn, self).__init__('spotify')
        self.service = OAuth2Service(
            name='spotify',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://accounts.spotify.com/authorize/',
            access_token_url='https://accounts.spotify.com/api/token',
            base_url='https://api.spotify.com/v1',
        )

    def authorize(self):
        spotify_auth_url = (self.service.get_authorize_url(
            scope='user-read-private user-read-email user-read-playback-state user-modify-playback-state',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )
        #print("authorize URL =" + spotify_auth_url)
        return redirect(spotify_auth_url)

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        #auth_token = request.args['code']
        oauth_session = self.service.get_auth_session(
            method='POST',
            data={'code':request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            headers={'Authorization':'Basic {}'.format(base64.b64encode("{}:{}".format(self.consumer_id,self.consumer_secret)))},
            decoder=decode_json
        )
        access_token = oauth_session.access_token_response.json()['access_token']

        #get user profile data
        authorize_header = {"Authorization":"Bearer {}".format(access_token)}
        user_profile_endpoint = "{}/me".format('https://api.spotify.com/v1')
        profile_response = requests.get(user_profile_endpoint, headers =authorize_header)
        profile_data = json.loads(profile_response.text)
        return(
            access_token,
            'spotify$' + profile_data['id'],
            profile_data['id'],
            profile_data['email']
        )
        #me = oauth_session.get('me?fields=id').json()
        #print(me['id'])
        #return (
         #   'spotify$' + me['id'],
          #  me.get('email').split('@')[0],  # Facebook does not provide
                                            # username, so the email
                                            # is used instead
           # me.get('email')
        #)