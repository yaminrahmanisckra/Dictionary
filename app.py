from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from forms import LoginForm, RegisterForm, DictionaryForm, WordForm, PasswordResetRequestForm, PasswordResetForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dictionary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
mail = Mail(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

class Dictionary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=True)
    publisher = db.Column(db.String(200), nullable=True)
    edition = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    pos = db.Column(db.String(50), nullable=True)  # পদ
    note = db.Column(db.Text, nullable=True)  # টীকা
    dictionary_id = db.Column(db.Integer, db.ForeignKey('dictionary.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    dictionary = db.relationship('Dictionary', backref='words')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), nullable=True)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.args.get('q')
    selected_dict_ids = request.args.getlist('dictionary_id', type=int)
    dictionaries = Dictionary.query.all()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    words = []
    pagination = None
    if query:
        if selected_dict_ids:
            word_query = Word.query.filter(Word.word.contains(query))
            word_query = word_query.filter(Word.dictionary_id.in_(selected_dict_ids))
            pagination = word_query.order_by(Word.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
            words = pagination.items
        else:
            words = []
    return render_template('index.html', words=words, query=query, dictionaries=dictionaries, selected_dict_ids=selected_dict_ids, pagination=pagination)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if not user.is_admin:
                flash('শুধুমাত্র অ্যাডমিন অনুমোদিত')
                return render_template('admin/login.html', form=form)
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('ভুল ইউজারনেম বা পাসওয়ার্ড')
    return render_template('admin/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    words = Word.query.order_by(Word.created_at.desc()).all()
    return render_template('admin/dashboard.html', words=words)

@app.route('/words')
@login_required
@admin_required
def words():
    selected_dict_id = request.args.get('dictionary_id', type=int, default=0)
    search_query = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    dictionaries = Dictionary.query.all()
    query = Word.query
    if selected_dict_id and selected_dict_id != 0:
        query = query.filter_by(dictionary_id=selected_dict_id)
    if search_query:
        query = query.filter(Word.word.contains(search_query))
    pagination = query.order_by(Word.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    words = pagination.items
    return render_template('admin/words.html', words=words, dictionaries=dictionaries, selected_dict_id=selected_dict_id, search_query=search_query, pagination=pagination)

@app.route('/add_word', methods=['GET', 'POST'])
@login_required
@admin_required
def add_word():
    form = WordForm()
    dictionaries = Dictionary.query.all()
    form.dictionary_id.choices = [(0, '-- ডিকশনারি নির্বাচন করুন --')] + [(d.id, d.name) for d in dictionaries]
    if form.validate_on_submit():
        word = Word(
            word=form.word.data, 
            definition=form.definition.data, 
            pos=form.pos.data,
            note=form.note.data,
            dictionary_id=form.dictionary_id.data if form.dictionary_id.data != 0 else None
        )
        db.session.add(word)
        db.session.commit()
        flash('শব্দ যোগ হয়েছে!')
        return redirect(url_for('words'))
    return render_template('admin/add_word.html', form=form)

@app.route('/edit_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_word(word_id):
    word = db.session.get_or_404(Word, word_id)
    form = WordForm(obj=word)
    dictionaries = Dictionary.query.all()
    form.dictionary_id.choices = [(0, '-- ডিকশনারি নির্বাচন করুন --')] + [(d.id, d.name) for d in dictionaries]
    if form.validate_on_submit():
        word.word = form.word.data
        word.definition = form.definition.data
        word.pos = form.pos.data
        word.note = form.note.data
        word.dictionary_id = form.dictionary_id.data if form.dictionary_id.data != 0 else None
        db.session.commit()
        flash('শব্দ আপডেট হয়েছে!')
        return redirect(url_for('words'))
    return render_template('admin/edit_word.html', form=form, word=word)

@app.route('/delete_word/<int:word_id>', methods=['POST'])
@login_required
@admin_required
def delete_word(word_id):
    word = db.session.get_or_404(Word, word_id)
    db.session.delete(word)
    db.session.commit()
    flash('শব্দ ডিলিট হয়েছে!')
    return redirect(url_for('words'))

@app.route('/dictionaries')
@login_required
@admin_required
def dictionaries():
    dictionaries = Dictionary.query.order_by(Dictionary.created_at.desc()).all()
    return render_template('admin/dictionaries.html', dictionaries=dictionaries)

@app.route('/add_dictionary', methods=['GET', 'POST'])
@login_required
@admin_required
def add_dictionary():
    form = DictionaryForm()
    if form.validate_on_submit():
        dictionary = Dictionary(
            name=form.name.data,
            author=form.author.data,
            publisher=form.publisher.data,
            edition=form.edition.data
        )
        db.session.add(dictionary)
        db.session.commit()
        flash('ডিকশনারি যোগ হয়েছে!')
        return redirect(url_for('dictionaries'))
    return render_template('admin/add_dictionary.html', form=form)

@app.route('/edit_dictionary/<int:dictionary_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_dictionary(dictionary_id):
    dictionary = db.session.get_or_404(Dictionary, dictionary_id)
    form = DictionaryForm(obj=dictionary)
    if form.validate_on_submit():
        dictionary.name = form.name.data
        dictionary.author = form.author.data
        dictionary.publisher = form.publisher.data
        dictionary.edition = form.edition.data
        db.session.commit()
        flash('ডিকশনারি আপডেট হয়েছে!')
        return redirect(url_for('dictionaries'))
    return render_template('admin/edit_dictionary.html', form=form, dictionary=dictionary)

@app.route('/delete_dictionary/<int:dictionary_id>', methods=['POST'])
@login_required
@admin_required
def delete_dictionary(dictionary_id):
    dictionary = db.session.get_or_404(Dictionary, dictionary_id)
    db.session.delete(dictionary)
    db.session.commit()
    flash('ডিকশনারি ডিলিট হয়েছে!')
    return redirect(url_for('dictionaries'))

@app.route('/users')
@login_required
@admin_required
def users():
    user_list = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=user_list)

def register():
    abort(403)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class UserEditForm(FlaskForm):
    username = StringField('ইউজারনেম', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('ইমেইল', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('নতুন পাসওয়ার্ড', validators=[Optional(), Length(min=6)])
    is_admin = BooleanField('অ্যাডমিন')
    submit = SubmitField('সংরক্ষণ করুন')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get_or_404(User, user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash('ইউজার আপডেট হয়েছে!')
        return redirect(url_for('users'))
    return render_template('admin/edit_user.html', form=form, user=user)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get_or_404(User, user_id)
    db.session.delete(user)
    db.session.commit()
    flash('ইউজার ডিলিট হয়েছে!')
    return redirect(url_for('users'))

class UserAddForm(FlaskForm):
    username = StringField('ইউজারনেম', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('ইমেইল', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired(), Length(min=6)])
    is_admin = BooleanField('অ্যাডমিন')
    submit = SubmitField('ইউজার তৈরি করুন')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserAddForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('এই ইউজারনেম ইতিমধ্যে আছে!')
            return render_template('admin/add_user.html', form=form)
        user = User(username=form.username.data, password=generate_password_hash(form.password.data), is_admin=form.is_admin.data, email=form.email.data)
        db.session.add(user)
        db.session.commit()
        # Send invitation email
        try:
            msg = Message('অ্যাডমিন ইনভাইটেশন', recipients=[form.email.data])
            msg.body = f"আপনাকে বাংলা ডিকশনারি অ্যাডমিন হিসেবে যুক্ত করা হয়েছে।\n\nলগইন লিঙ্ক: http://127.0.0.1:5000/login\nইউজারনেম: {form.username.data}\nপাসওয়ার্ড: {form.password.data}\n\nলগইন করার পর পাসওয়ার্ড পরিবর্তন করুন।"
            mail.send(msg)
            flash('ইউজার তৈরি হয়েছে এবং ইনভাইটেশন ইমেইল পাঠানো হয়েছে!')
        except Exception as e:
            flash(f'ইউজার তৈরি হয়েছে, কিন্তু ইমেইল পাঠানো যায়নি: {e}')
        return redirect(url_for('users'))
    return render_template('admin/add_user.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message('পাসওয়ার্ড রিসেট লিঙ্ক', recipients=[user.email])
                msg.body = f"পাসওয়ার্ড রিসেট করতে এই লিঙ্কে যান: {reset_url}\n\nলিঙ্কটি ১ ঘন্টার জন্য কার্যকর থাকবে।"
                mail.send(msg)
                flash('রিসেট লিঙ্ক ইমেইলে পাঠানো হয়েছে!')
            except Exception as e:
                flash(f'ইমেইল পাঠানো যায়নি: {e}')
        else:
            flash('এই ইমেইল কোনো ইউজারের সাথে মেলে না!')
    return render_template('admin/forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('রিসেট লিঙ্কের মেয়াদ শেষ!')
        return redirect(url_for('forgot_password'))
    except BadSignature:
        flash('লিঙ্কটি অবৈধ!')
        return redirect(url_for('forgot_password'))
    user = User.query.filter_by(email=email).first_or_404()
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('পাসওয়ার্ড রিসেট হয়েছে! এখন লগইন করুন।')
        return redirect(url_for('login'))
    return render_template('admin/reset_password.html', form=form)

class FirstAdminForm(FlaskForm):
    username = StringField('ইউজারনেম', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('ইমেইল', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('এডমিন তৈরি করুন')

@app.route('/first_admin', methods=['GET', 'POST'])
def first_admin():
    if User.query.first():
        flash('এডমিন ইতিমধ্যে আছে!')
        return redirect(url_for('login'))
    form = FirstAdminForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=generate_password_hash(form.password.data), is_admin=True, email=form.email.data)
        db.session.add(user)
        db.session.commit()
        flash('প্রথম এডমিন তৈরি হয়েছে! এখন লগইন করুন।')
        return redirect(url_for('login'))
    return render_template('admin/first_admin.html', form=form)

if __name__ == '__main__':
    app.run(debug=True) 