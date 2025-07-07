# বাংলা টু বাংলা ডিকশনারি

এটি একটি Flask বেসড বাংলা টু বাংলা ডিকশনারি ওয়েবসাইট।

## ফিচার

- **পাবলিক সার্চ**: ব্যবহারকারীরা শব্দ সার্চ করতে পারবে
- **ইউজার রেজিস্ট্রেশন**: নতুন ইউজার রেজিস্টার করতে পারবে
- **অ্যাডমিন প্যানেল**: শব্দ এন্ট্রি, এডিট, ডিলিট
- **মাল্টিপল ডিকশনারি সাপোর্ট**: বিভিন্ন উৎস থেকে শব্দ

## ইনস্টলেশন

1. **ডিপেন্ডেন্সি ইনস্টল করুন**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **ডাটাবেস সেটআপ করুন**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **অ্যাডমিন ইউজার তৈরি করুন**:
   ```bash
   python3 -c "
   from app import app, db, User
   from werkzeug.security import generate_password_hash
   with app.app_context():
       admin = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
       db.session.add(admin)
       db.session.commit()
       print('Admin user created: admin/admin123')
   "
   ```

4. **অ্যাপ রান করুন**:
   ```bash
   flask run
   ```

## ব্যবহার

- **হোমপেজ**: http://localhost:5000
- **রেজিস্ট্রেশন**: http://localhost:5000/register
- **লগইন**: http://localhost:5000/login
  - অ্যাডমিন: `admin` / `admin123`
  - নতুন ইউজার: রেজিস্ট্রেশন করে তৈরি করুন

## ফাইল স্ট্রাকচার

```
├── app.py              # মূল Flask অ্যাপ
├── forms.py            # ফর্ম ক্লাস
├── templates/          # HTML টেমপ্লেট
│   ├── base.html
│   ├── index.html
│   └── admin/
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── add_word.html
│       └── edit_word.html
├── migrations/         # ডাটাবেস মাইগ্রেশন
└── requirements.txt    # পাইথন ডিপেন্ডেন্সি
``` 