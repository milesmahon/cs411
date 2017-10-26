from flask import Flask, render_template
# from flaskext.mysql import MySQL

app = Flask(__name__)

# Much of below is from  a starter tutorial given in CS460 w Prof Kollios
# it lets us use a database in our flask app.
# mysql = MySQL()
#
# app.config['MYSQL_DATABASE_USER'] = 'root'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'
# app.config['MYSQL_DATABASE_DB'] = 'sakila'
# app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
# mysql.init_app(app)

#Example Query
# conn = mysql.connect()
# cursor = conn.cursor()
# query = 'select title from film where film_id < 900;'
# cursor.execute(query)
# data = []
# for item in cursor:
# 	data.append(item)
#
# print(data)

# if we wanted to print something to the terminal (not show it on our webpage):
# print("hello")
import spotipy
from flask import request
from spotipy.oauth2 import SpotifyClientCredentials

@app.route('/')
def index():
    return render_template('index.html', data = [["hello"]])

@app.route('/result', methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      formlist = request.form.getlist("searchquery")

        #OAUTH
      client_credentials_manager = SpotifyClientCredentials(client_id='3ec0f35ae45f45e9bbfeaf8a28a47921',
                                                            client_secret='32b8e5599c234d999d63f6e28682465b')
      sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

      # print(formlist)
      results = sp.search(q=formlist, limit=20)
      tracknames = []
      for i, t in enumerate(results['tracks']['items']):
          tracknames += [t['name']]

      print(tracknames)
      return render_template("result.html",tracknames = tracknames)


# if we had another html file we could serve it at the /hello url like this:
# @app.route('/hello/')
# def hello():
# 	return 'hello'

if __name__ == '__main__':
    app.run()