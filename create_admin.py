from app import app, db, User
from werkzeug.security import generate_password_hash

username = input('নতুন অ্যাডমিন ইউজারনেম: ')
password = input('পাসওয়ার্ড: ')

with app.app_context():
    if User.query.filter_by(username=username).first():
        print('এই ইউজারনেম ইতিমধ্যে আছে!')
    else:
        user = User(username=username, password=generate_password_hash(password), is_admin=True)
        db.session.add(user)
        db.session.commit()
        print('অ্যাডমিন ইউজার তৈরি হয়েছে!') 