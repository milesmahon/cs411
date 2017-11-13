from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def main():
	return render_template('index.html')

@app.route('/showLogIn')
def showLogIn():
	return render_template('login.html')

@app.route('/home')
def home():
	return render_template('home.html')
	
if __name__ == "__main__":
	app.run()
