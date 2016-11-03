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
import datetime
import re

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
upload_folder = '/Users/yeungSL/Desktop/social_media_website/templates/uploads' #store all the picture uploaded into his directory on the file system

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
	return r #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotosFromUid(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption FROM Pictures P, Albums A WHERE A.owner_id = '{0}' AND A.album_id = P.album_id".format(uid))
	return cursor.fetchall()

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
	cursor.execute("SELECT A.name, A.date_created, A.album_id FROM albums A, users U WHERE A.owner_id = U.user_id AND U.email = '{0}'".format(email))
	return cursor.fetchall()

def getActivelist():
	cursor = conn.cursor()
	cursor.execute("SELECT T1.email, (T1.num + T2.num)As Tnum FROM (SELECT email, count(*) As num FROM users U, albums A, pictures P WHERE U.user_id = A.owner_id and P.album_id = A.album_id group by user_id) As T1, (SELECT email, count(*) As num FROM users S, comments C WHERE S.user_id = C.owner_id group by user_id) As T2 WHERE T1.email = T2.email ORDER BY Tnum DESC")
	return cursor.fetchall()

def getAid(name):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM albums WHERE name = '{0}'".format(name))
	return cursor.fetchall()

def verifyAlbums(aname, cdate):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, owner_id FROM albums WHERE name = '{0}' AND date_created = '{1}'".format(aname, cdate))
	m = cursor.fetchall()[0]
	if m[1] != getUserIdFromEmail(flask_login.current_user.id):
		m = "cannnot delete album from other people"
		return False, m
	if m[1] == getUserIdFromEmail(flask_login.current_user.id):
		return True, m
	else:
		m = "There is no such album in the list"
		return False, m

def privateTags(email):
	cursor = conn.cursor()
	cursor.execute("SELECT description FROM (SELECT picture_id, description FROM tags WHERE picture_id IN( SELECT T2.picture_id FROM tags T2, users U, albums A, pictures P WHERE U.email = '{0}' AND U.user_id = A.owner_id AND A.album_id = P.album_id AND P.picture_id = T2.picture_id))AS Temp GROUP BY description HAVING count(*)>=1 ORDER BY count(*) DESC".format(email))
	return cursor.fetchall()

def getCommentsFromPhotos(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT comment_id, text, date_left FROM comments WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchall()	

def getLikesFromPhotos(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT count(*) FROM likes WHERE picture_id = '{0}'".format(pid))
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
	alist = getAlbumsFromEmail(flask_login.current_user.id)
	anum = len(alist)
	print alist
	print anum
	tags = privateTags(flask_login.current_user.id)
	yml_list = []
	pclist = []
	private = 0
	yml = 0
	if tags:
		print tags
		yml_list = you_may_also_like(tags, getUserIdFromEmail(flask_login.current_user.id))
		pclist = getCLfromPic(yml_list)
		print pclist
		private = 1
		yml = 1
	return render_template('hello.html', name=uinfo[0], infos=uinfo, num=fnum, list=flist, anum=anum, alist=alist, pclist=pclist, actlist=activeList, tags=tags, private=private, photos=yml_list, yml=yml, message="Here's your profile")

@app.route('/expand_album/<aid>/<aname>')
def expand_album(aid, aname):
	p = getUsersPhotos(aid)
	pclist = {}	
	for photo in p:
			l = getLikesFromPhotos(photo[1])
			c = getCommentsFromPhotos(photo[1])
			print c
			pclist[photo] = c
			pclist[photo] += l 
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		return render_template('hello.html', message=aname, photos=p, pclist=pclist)
	info = getUserinfoFromEmail(flask_login.current_user.id)[0]
	return render_template('hello.html', name=info, message=aname, photos=p, private=1, pclist=pclist)

@app.route('/friend', methods=['GET'])
@flask_login.login_required
def friend():
	flist = getFriendsFromEmail(flask_login.current_user.id)
	fnum = len(flist)
	return render_template('friend.html', num=fnum, list=flist)

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
		return flask.redirect('/profile')

def alreadyFriends(user, friend):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM friends WHERE friend_id = '{0}' AND user_id = '{1}'".format(friend, user)):
		return True
	else:
		return False

@app.route('/visit/<email>')
def visit(email):
	uinfo = getUserinfoFromEmail(email)
	flist = getFriendsFromEmail(email)
	fnum = len(flist)
	activeList = getActivelist()
	alist = getAlbumsFromEmail(email)
	anum = len(alist)
	tags = privateTags(email)
	p = getUsersPhotosFromUid(getUserIdFromEmail(email))
	pclist = getCLfromPic(p)
	print pclist
	info = getUserinfoFromEmail(flask_login.current_user.id)[0]
	try:
		uemail = flask_login.current_user.id
		if email == uemail:
			return flask.redirect('/profile')
		else:
			return render_template('hello.html', name=info, infos=uinfo, num=fnum, list=flist, anum=anum, alist=alist, pclist=pclist, actlist=activeList, tags=tags, photos=p, message="Here's the profile")
	except:
		return render_template('hello.html', name=info, infos=uinfo, num=fnum, list=flist, anum=anum, alist=alist, pclist=pclist, actlist=activeList, tags=tags, photos=p, message="Here's the profile")





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
		tag = request.form.get('tag')
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
			p = getUsersPhotos(aid)
			AddTag(p, tag)
			pclist	= getCLfromPic(p)
			return render_template('hello.html', name=info, message='Photo uploaded!', photos=p, pclist=pclist)
		else:
			return render_template('upload.html', message='file choosen cannot be uploaded', num=anum, list=alist)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', num=anum, list=alist)
#end photo uploading code 

def AddTag(p, tag):
	pid = p[-1][1]
	print pid
	print tag
	tags = re.split('#|\s', tag)[1:]
	print tags
	cursor = conn.cursor()
	for t in tags:
		cursor.execute("INSERT INTO Tags (picture_id, description) VALUES('{0}', '{1}')".format(pid, t))
	conn.commit()

def gatherTags():
	cursor = conn.cursor()
	cursor.execute("SELECT description FROM tags GROUP BY description HAVING count(*)>=1 ORDER BY count(*) DESC")
	return cursor.fetchall()

def getTagsPhotos(d):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM tags WHERE description = '{0}'".format(d))
	pids = cursor.fetchall()
	print pids
	photos = list()
	for pid in pids:
		cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(pid[0]))
		photos += cursor.fetchall()
	print photos
	return photos

def getTagsPhotosPrivate(d, uid):
	print uid
	cursor = conn.cursor()
	cursor.execute("SELECT T.picture_id FROM tags T, albums A, pictures P WHERE T.description = '{0}' AND A.owner_id = '{1}' AND P.picture_id = T.picture_id AND A.album_id = P.album_id ".format(d, uid))
	pids = cursor.fetchall()
	print pids
	photos = list()
	for pid in pids:
		cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(pid[0]))
		photos += cursor.fetchall()
	print photos
	return photos

@app.route('/upload/add_albums', methods=['POST'])
@flask_login.login_required
def add_albums():
	cdate = datetime.datetime.now().date().isoformat()
	print cdate
	try:
		aname=request.form.get('albumName')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect('/upload')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	info = getUserinfoFromEmail(flask_login.current_user.id)[0]
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Albums (name, owner_id, date_created) VALUES ('{0}', '{1}', '{2}')".format(aname, uid, cdate))
	conn.commit()
	return flask.redirect('/profile')

@app.route('/upload/delete_albums', methods=['POST'])
@flask_login.login_required
def delete_albums():
	try:
		cdate = request.form.get('cdate')
		aname = request.form.get('albumName')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('upload'))
	t, message = verifyAlbums(aname, cdate)
	if t:
		print message
		info = getUserinfoFromEmail(flask_login.current_user.id)[0]
		photos = getUsersPhotos(message[0])
		cursor = conn.cursor()
		for photo in photos:
			print photo[1]
			cursor.execute("DELETE FROM pictures WHERE picture_id = '{0}'".format(photo[1]))
		cursor.execute("DELETE FROM albums WHERE album_id = '{0}'".format(message[0]))
		conn.commit()
		return render_template('hello.html', name=info, message='The Album is deleted', albums=getAlbumsFromEmail(flask_login.current_user.id))
	else:
		print message
		return render_template('upload.html', message=message)

@app.route('/search_tags', methods=['POST'])
def search_tags():
	try:
		words = request.form.get('words')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('/'))
	ws = re.split(' ', words)
	print ws
	T = []
	for x in gatherTags():
		T += [x[0]]
	plist = list()
	print T
	for tag in ws:
		if tag in T:
			plist += getTagsPhotos(tag)
	plist = set(plist)
	pclist = getCLfromPic(plist)
	return render_template('hello.html', message='Related pictures', photos=plist, pclist=pclist)

@app.route('/tags_recom', methods=['POST'])
def tags_recom():
	try:
		tags = request.form.get('tags')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('/'))
	ws = re.split(' ', tags)
	print ws
	taglist = []
	for t in gatherTags():
		taglist += [t[0]]
	T = []
	for x in ws:
		print x 
		if x in taglist:
			T += [x]
	print T
	tags = tag_recommendation(T)
	return render_template('hello.html', message='Recommanded tags', tags=tags)


@app.route('/delete_pictures/<pid>', methods=['POST'])
@flask_login.login_required
def delete_pictures(pid):
	print pid
	info = getUserinfoFromEmail(flask_login.current_user.id)[0]
	cursor = conn.cursor()
	cursor.execute("DELETE FROM pictures WHERE picture_id = '{0}'".format(pid))
	conn.commit()
	return render_template('hello.html', name=info, message='The picture is deleted')

@app.route('/show_tags/<d>', methods=['POST'])
def show_tags(d):
	print d 
	p = getTagsPhotos(d)
	pclist = getCLfromPic(p)	
	return render_template('hello.html', message='All picture in this tag', photos=p, pclist=pclist)

@app.route('/show_tags_private/<d>', methods=['POST'])
def show_tags_private(d):
	print d 
	info = getUserinfoFromEmail(flask_login.current_user.id)
	p = getTagsPhotosPrivate(d, getUserIdFromEmail(flask_login.current_user.id))
	pclist = getCLfromPic(p)
	return render_template('hello.html', name=info[0], message='All picture in this tag', photos=p, pclist=pclist)

@app.route('/send/<filename>')
@flask_login.login_required
def send_file(filename):
	return flask.send_from_directory(app.config['UPLOAD_FOLDER'], filename)
#upload page for album

@app.route('/comment_pictures/<pid>', methods=['POST'])
def comment_pictures(pid):
	cdate = datetime.datetime.now().date().isoformat()
	try:
		comment = request.form.get('comment')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect('/')
	cursor = conn.cursor()
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		cursor.execute("INSERT INTO Comments (text, date_left, picture_id) VALUES ('{0}', '{1}', '{2}')".format(comment, cdate, pid))
		conn.commit()
		return flask.redirect('/')
	if addCommentSelf(uid, pid):
		return render_template('hello.html', message='cannot comment photo of your own')
	cursor.execute("INSERT INTO Comments (owner_id, text, date_left, picture_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(uid, comment, cdate, pid))
	conn.commit()
	return flask.redirect('/')

def addCommentSelf(uid, pid):
	cursor = conn.cursor()
	if cursor.execute("SELECT picture_id  FROM pictures P, albums A WHERE A.owner_id = '{0}' AND A.album_id = P.album_id AND P.picture_id = '{1}'".format(uid, pid)): 
		#this means there are greater than zero entries with that email
		return True
	else:
		return False


@app.route('/like_pictures/<pid>', methods=['POST'])
def like_pictures(pid):
	cursor = conn.cursor()
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except:
		cursor.execute("INSERT INTO Likes (picture_id) VALUES ('{0}')".format(pid))
		conn.commit()
		return flask.redirect('/')
	if likedBefore(pid, uid):
		return flask.redirect('/profile')
	cursor.execute("INSERT INTO Likes (picture_id, user_id) VALUES ('{0}', '{1}')".format(pid, uid))
	conn.commit()
	return flask.redirect('/profile')

def likedBefore(pid, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT picture_id, user_id FROM likes WHERE picture_id = '{0}' AND user_id = '{1}'".format(pid, uid)):
		return True
	else:
		return False


def you_may_also_like(tags, uid):
	query_head = "SELECT P.imgdata, T.picture_id, P.caption FROM Pictures P, Tags T, Albums A WHERE A.owner_id = '{0}' AND A.album_id = P.album_id AND P.picture_id = T.picture_id AND (".format(uid)
	query_tail = ") GROUP BY T.picture_id ORDER BY Count(T.description) DESC"
	for tag in tags:
		if tag == tags[-1]:
			query_head += "T.description = '{0}'".format(tag[0])
			break 
		query_head += "T.description = '{0}' OR ".format(tag[0]) 
	query = query_head + query_tail
	print query
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

def tag_recommendation(tags):
	pics_head = "( SELECT T2.picture_id FROM Tags T2 WHERE " 
	badg_head = "( SELECT T3.description FROM Tags T3 WHERE "
	for tag in tags:
		if tag == tags[-1]:
			pics_head += "T2.description = '{0}' GROUP BY T2.picture_id HAVING count(*)>= 1 ) As Temp".format(tag)
			badg_head += "T3.description = '{0}' GROUP BY description HAVING count(*) >= 1 )".format(tag)
			break
		pics_head += "T2.description = '{0}' OR ".format(tag)
		badg_head += "T3.description = '{0}' OR ". format(tag)

	query = "SELECT description, count(T1.description) AS dnum FROM Tags T1, " + pics_head + " WHERE Temp.picture_id = T1.picture_id AND T1.description NOT IN " + badg_head + " GROUP BY description ORDER BY dnum DESC"
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()


#default page  
@app.route("/", methods=['GET'])
def hello():
	tags = gatherTags()
	print tags
	activeList = getActivelist()
	print activeList
	p = set(getAllPics())
	print p
	pclist=getCLfromPic(p)
	print pclist
	return render_template('hello.html', message='Welecome to Photoshare', tags=tags, actlist=activeList, photos=p, pclist=pclist)

def getAllPics():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM pictures ")
	return cursor.fetchall()

def getCLfromPic(p):
	pclist={}
	for photo in p:
		l = getLikesFromPhotos(photo[1])
		c = getCommentsFromPhotos(photo[1])
		print c
		pclist[photo] = c 
		pclist[photo] += l
	return pclist

if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
