######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, flash
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from dateutil.parser import parse

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
upload_folder = '/Users/younith/Desktop/social_media_website/templates/uploads' #store all the picture uploaded into his directory on the file system

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'longlong1155'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['UPLOAD_FOLDER'] = upload_folder
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		bday=request.form.get('bday')
		ht=request.form.get('ht')
		gender=request.form.get('gender')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test1 =  isEmailUnique(email)
	test2 = qualify(gender)
	print test2 
	if test1 and test2:
		print cursor.execute("INSERT INTO Users (first_name, last_name, date_of_birth, email, hometown, gender, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(fname, lname, bday, email, ht, gender, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=fname, message='Account Created!')
	else:
		print "couldn't find all tokens"
		flask.flash('True')
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(aid))
	r = cursor.fetchall()
	print r
	return r #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def qualify(gender):
	if (gender == 'male' or gender == 'female'):
		return True
	else:
		return False

def getUserinfoFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT 	first_name, last_name, date_of_birth, hometown, gender FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchall()[0]

def getFriendsFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT U2.first_name, U2.last_name, U2.email FROM users U1, users U2, friends F WHERE U1.user_id = F.user_id AND U2.user_id = F.friend_id AND U1.email = '{0}'".format(email))
	return cursor.fetchall()

def getAlbumsFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT A.name FROM albums A, users U WHERE A.owner_id = U.user_id AND U.email = '{0}'".format(email))
	return cursor.fetchall()

def getActivelist():
	cursor = conn.cursor()
	cursor.execute("SELECT email, count(*) FROM users U, albums A, pictures P WHERE U.user_id = A.owner_id and P.album_id = A.album_id GROUP BY user_id ORDER BY count(*) desc")
	return cursor.fetchall()

def getAid(name):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM albums WHERE name = '{0}'".format(name))
	return cursor.fetchall()
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	uinfo = getUserinfoFromEmail(flask_login.current_user.id)
	print uinfo
	flist = getFriendsFromEmail(flask_login.current_user.id)
	fnum = len(flist)
	print flist
	print fnum
	activeList = getActivelist()
	print activeList
	return render_template('hello.html', name=uinfo[0], infos=uinfo, num=fnum, list=flist, actlist=activeList, message="Here's your profile")

@app.route('/friend', methods=['GET'])
@flask_login.login_required
def friend():
	return render_template('friend.html')

@app.route('/friend', methods=['POST'])
@flask_login.login_required
def add_friend():
	try:
		email=request.form.get('email')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('friend'))
	cursor = conn.cursor()
	if email == flask_login.current_user.id:
		print "cannot add self as friend"
		flask.flash('cannot add yourself as friend, try again!')
		return flask.redirect(flask.url_for('friend'))
	if isEmailUnique(email): #check if the email is registered
		print "There is no such account"
		flask.flash('There is no such account!')
		return flask.redirect(flask.url_for('friend'))
	else:
		cursor.execute("SELECT U1.user_id, U1.first_name, U2.user_id FROM users U1, users U2 WHERE U1.email = '{0}' and U2.email = '{1}'". format(flask_login.current_user.id, email))
		r = cursor.fetchall()[0]
		print r
		uid1 = r[0]
		fname = r[1]
		uid2 = r[2]
		if alreadyFriends(uid1, uid2):
			print "Already had this friend"
			flask.flash('Already had this friend!')
			return flask.redirect(flask.url_for('friend'))
		print cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid1, uid2))
		conn.commit()
		return render_template('hello.html', name=fname, message='Friend added!')

def alreadyFriends(user, friend):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM friends WHERE friend_id = '{0}' AND user_id = '{1}'".format(friend, user)):
		return True
	else:
		return False

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	alist = getAlbumsFromEmail(flask_login.current_user.id)
	anum = len(alist)
	if request.method == 'POST':
		aid = getAid(request.form.get('albumName'))
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		print caption
		print aid
		if not aid:
			return render_template('upload.html', message='Album input does not exists, do you want to creat a new one?')
		else:
			aid = aid[0][0]
		if imgfile and allowed_file(imgfile.filename):
			filename = secure_filename(imgfile.filename)
			imgfile.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Pictures (album_id, imgdata, caption) VALUES ('{0}', '{1}', '{2}' )".format(aid, filename, caption))
			conn.commit()
			info = getUserinfoFromEmail(flask_login.current_user.id)[0]
			return render_template('hello.html', name=info, message='Photo uploaded!', photos=getUsersPhotos(aid))
		else:
			return render_template('upload.html', message='file choosen cannot be uploaded', num=anum, list=alist)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', num=anum, list=alist)
#end photo uploading code 

@app.route('/send/<filename>')
@flask_login.login_required
def send_file(filename):
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#upload page for album

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
