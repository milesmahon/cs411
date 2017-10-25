from flask import Flask, render_template
from flaskext.mysql import MySQL

app = Flask(__name__)
mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'yankees2'
app.config['MYSQL_DATABASE_DB'] = 'sakila'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)

#Example Query
conn = mysql.connect()
cursor = conn.cursor()
query = 'select title from film where film_id < 900;'
cursor.execute(query)
data = []
for item in cursor:
	data.append(item)

print(data)


@app.route('/')
def index():
	return render_template('index.html', data = data)

@app.route('/hello/')
def hello():
	return 'hello'

if __name__ == '__main__':
    app.run()