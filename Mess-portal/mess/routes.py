import secrets
import sqlite3
import nltk
from PIL import Image
from nltk.corpus import wordnet
from wordcloud import WordCloud, STOPWORDS
import os
from mess.models import User, Post, Complaint, Menu, NewComplaint
from flask import Flask, render_template, url_for, flash, redirect, request,abort
from mess.form import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, MenuForm, NewMenuForm, FindDate
from mess import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime,date
from keras.preprocessing.sequence import pad_sequences
from mess.imdbReview import extract_words
import tensorflow as tf
import pickle
global graph
nltk.download('wordnet')
graph = tf.compat.v1.get_default_graph()
funny_words=['lol','lmao','laugh','laughing','kidding']
with open('mess/vect.pkl','rb') as f:
    vectorizer=pickle.load(f)
with open('mess/funny.pkl','rb') as f:
    classifier_liblinear=pickle.load(f)
def process_output(test_string,prediction):
	test_string = list(test_string.split(" "))
	for word in test_string:
		if word in funny_words:
			return "Funny!"
	return "Not Funny!"

def encode_docs(tokenizer, max_length, docs):
    # integer encode
    encoded = tokenizer.texts_to_sequences(docs)
    # pad sequences
    padded = pad_sequences(encoded, maxlen=max_length, padding= 'post' )
    return padded
Tokenizer =pickle.load(open("mess/TOKENIZER.pickle", "rb"))
'''vectorizer = TfidfVectorizer(min_df=4, max_df=0.8,
                            sublinear_tf=True, use_idf=True)'''
classifier_liblinear = pickle.load(open('mess/funny.pkl','rb'))
sentiment = pickle.load(open('mess/funny.pkl','rb'))
@app.route("/")
@app.route("/home")
def home():
	data = Menu.query.all()
	return render_template('home.html',posts=data)

@app.route("/about")
def display_blogs():
	data = Menu.query.all()
	return render_template("about.html",posts=data,title="Edit Menu")

@app.route("/about2",methods=["GET","POST"])
def display_complaints():
	form = FindDate()
	page = request.args.get('page',1,type=int)
	if form.validate_on_submit():
		start_month = form.start_date.data.month
		start_day = form.start_date.data.day
		start_year = form.start_date.data.year
		end_month = form.end_date.data.month
		end_day = form.end_date.data.day
		end_year = form.end_date.data.year
		start = datetime(year=start_year, month=start_month, day=start_day)
		end = datetime(year=end_year, month=end_month, day=end_day)
		conn = sqlite3.connect('mess/site.db')
		c = conn.cursor()
		c.execute("SELECT * FROM new_complaint")
		rows = c.fetchall()
		string = ''
		for row in rows:
			d = datetime.strptime((row[2].split(' '))[0], "%Y-%m-%d")
			if d >= start and d <= end:
				string += row[3] + ' '
		from nltk.stem import WordNetLemmatizer
		lemmatizer = WordNetLemmatizer()
		raw1 = (' ').join([lemmatizer.lemmatize(word, wordnet.VERB) for word in string.split()])
		stopwords = set(STOPWORDS)
		wc = WordCloud(background_color="white", max_words=50, stopwords=stopwords, max_font_size=80)
		wc.generate(raw1)
		random_hex = secrets.token_hex(8)
		wc.to_file('mess/static/img/'+random_hex+'.png')
		address='static/img/'+random_hex+'.png'
		data_fil = NewComplaint.query.filter(NewComplaint.date_posted >= start).filter(NewComplaint.date_posted <= end)
		return render_template("about3.html", posts=data_fil,addr=address)

	data = NewComplaint.query.order_by(NewComplaint.date_posted.desc()).paginate(per_page=4,page=page)
	return render_template("about2.html",posts=data,form=form,title="Complaints")



@app.route("/register",methods=["GET","POST"])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		# generate password hash and create user
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash('Account created !','success')
		return redirect(url_for('login'))

	return render_template("register.html", title="Register", form=form)

@app.route("/login",methods=["GET","POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data)==True:
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash("Login unsuccessful. Check email/password",'danger')
	return render_template("login.html", title="Login", form=form)

@app.route("/forgot_password")
def forgot_password():
	return "Not made"

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	f_name, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	picture_path = os.path.join(app.root_path,'static/img', picture_fn)

	output_size = (125,125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)

	i.save(picture_path)

	return picture_fn

@app.route("/account",methods=["GET","POST"])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Your account has been updated','success')
		redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename="img/"+current_user.image_file)
	return render_template('account.html', title='Account', image_file=image_file, form= form)

@app.route("/post/new",methods=["GET","POST"])
@login_required
def new_post():
	form = MenuForm()
	if form.validate_on_submit():
		post = Post(title=form.title.data, content = form.content.data, author = current_user)
		db.session.add(post)
		db.session.commit()
		flash('The Menu has been Added','success')
		return redirect(url_for('home'))
	return render_template('create_post.html', title='Create Menu',legend="Add Menu", form = form)
@app.route("/menu/new",methods=["GET","POST"])
@login_required
def new_menu():
	form = NewMenuForm()
	if form.validate_on_submit():
		post = Menu(title=form.title.data, breakfast = form.breakfast.data,lunch = form.lunch.data,dinner= form.dinner.data,author = current_user)
		db.session.add(post)
		db.session.commit()
		flash('The Menu has been Added','success')
		return redirect(url_for('home'))
	return render_template('create_menu.html', title='Create Menu',legend="Add Menu", form = form)

@app.route("/post/<int:post_id>")
def post(post_id):
	post = Post.query.get_or_404(post_id)
	return render_template('post.html',title=post.title,post=post)
@app.route("/menu/<int:post_id>")
def menu(post_id):
	post = Menu.query.get_or_404(post_id)
	return render_template('menu.html',title=post.title,post=post)
@app.route("/complaint/<int:post_id>")
def complaint(post_id):
	post = Complaint.query.get_or_404(post_id)
	return render_template('complaint.html',title=post.title,post=post)
@app.route("/newcomplaint/<int:post_id>")
def newcomplaint(post_id):
	post = NewComplaint.query.get_or_404(post_id)
	return render_template('newcomplaint.html',title=post.title,post=post)

@app.route("/post/<int:post_id>/update",methods=["GET","POST"])
@login_required
def update_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data
		form.content = form.content.data
		db.session.commit()
		flash('The Menu for the day has been updated!','success')
		return redirect(url_for('post',post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content

	return render_template('create_post.html', title='Update Post',
						   form=form, legend='Update Post')

@app.route("/menu/<int:post_id>/update",methods=["GET","POST"])
@login_required
def update_menu(post_id):
	post = Menu.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = NewMenuForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.breakfast = form.breakfast.data
		post.lunch = form.lunch.data
		post.dinner = form.dinner.data
		db.session.commit()
		flash('The Menu for the day has been updated!','success')
		return redirect(url_for('menu',post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.breakfast.data = post.breakfast
		form.lunch.data = post.lunch
		form.dinner.data = post.dinner

	return render_template('create_menu.html', title='Update Post',
						   form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	db.session.delete(post)
	db.session.commit()
	flash('The Menu for the day has been deleted!', 'success')
	return redirect(url_for('home'))
@app.route("/post/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_menu(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	db.session.delete(post)
	db.session.commit()
	flash('The Menu for the day has been deleted!', 'success')
	return redirect(url_for('home'))

@app.route("/complaint/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_complaint(post_id):
	post = Complaint.query.get_or_404(post_id)
	db.session.delete(post)
	db.session.commit()
	flash('This Complaint has been deleted!', 'success')
	return redirect(url_for('home'))
@app.route("/newcomplaint/<int:post_id>/delete",methods=["POST"])
@login_required
def delete_newcomplaint(post_id):
	post = NewComplaint.query.get_or_404(post_id)
	db.session.delete(post)
	db.session.commit()
	flash('This Complaint has been deleted!', 'success')
	return redirect(url_for('home'))

@app.route("/complaint/new",methods=["GET","POST"])
@login_required
def new_complaint():
	form = PostForm()
	if form.validate_on_submit():
		x=list()
		x.append(form.content.data)
		x= encode_docs(Tokenizer,414,x)
		with graph.as_default():
			prediction = sentiment.predict(x)
		prediction = list(prediction[0])
		funny_string = ""
		if(prediction[0]>0.6):
			senti_string="Review: Negative"
		elif(prediction[2]>0.6):
			senti_string="Review: Positive"
		else:
			senti_string="Review: Neutral"
		y=list()
		y.append(form.content.data)
		input_features = vectorizer.transform(extract_words(y))
		prediction = classifier_liblinear.predict(input_features)
		if(prediction[0]==1):
			funny_string="Funny!"
		else:
			funny_string= process_output(form.content.data,prediction)
		post = Complaint(title=form.title.data,content = form.content.data,date_posted=form.date.data,author= current_user )
		post1 = NewComplaint(title=form.title.data,senti=senti_string,funny=funny_string, content = form.content.data,date_posted=form.date.data, author= current_user)
		db.session.add(post1)
		db.session.add(post)
		db.session.commit()
		flash('Your complaint has been sucessfully added','success')
		return redirect(url_for('home'))
	return render_template('create_complaint.html', title='Complaint Portal',legend="New Complaint", form = form)

