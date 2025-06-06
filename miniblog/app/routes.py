from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import  login_user, logout_user, current_user, login_required
from sqlalchemy import text
import sqlalchemy as sa
from app.models import User
from urllib.parse import urlsplit
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, timezone
from flask_wtf.csrf import validate_csrf, CSRFError
from app.models import Post
from app.email import send_password_reset_email



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('你的貼文現在已發布！')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='首頁', form = form, posts=posts.items, next_url=next_url,prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    per_page = 5 or app.config.get('POSTS_PER_PAGE') 
    print("每頁顯示筆數：", per_page)
    offset = (page - 1) * per_page

    # 查詢總數（用來判斷是否有下一頁）
    total_sql = text("SELECT COUNT(*) FROM post")
    total = db.session.execute(total_sql).scalar()

    # Raw SQL 查詢含 JOIN user
    sql = text("""
        SELECT post.id AS post_id, post.body, post.timestamp, post.user_id,
               user.id AS user_id, user.username, user.email
        FROM post
        JOIN user ON post.user_id = user.id
        ORDER BY post.timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    result = db.session.execute(sql, {'limit': per_page, 'offset': offset})
    rows = result.fetchall()

    posts = []
    for row in rows:
        # 建立 User 實例
        user = User(id=row.user_id, username=row.username, email=row.email)

        # 建立 Post 實例，注意欄位對應
        post = Post(id=row.post_id, body=row.body, timestamp=row.timestamp, user_id=row.user_id)

        # 手動指定 post.author
        post.author = user

        posts.append(post)

    # 分頁控制（手動模擬 flask-sqlalchemy 的 pagination）
    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total

        @property
        def has_next(self):
            return self.page * self.per_page < self.total

        @property
        def has_prev(self):
            return self.page > 1

        @property
        def next_num(self):
            return self.page + 1

        @property
        def prev_num(self):
            return self.page - 1

    pagination = Pagination(page, per_page, total)

    next_url = url_for('explore', page=pagination.next_num) if pagination.has_next else None
    prev_url = url_for('explore', page=pagination.prev_num) if pagination.has_prev else None

    return render_template('index.html', title='探索', posts=posts,
                           next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    errors = {}
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            errors['csrf'] = 'CSRF 驗證失敗'
            return render_template('login.html', errors=errors)

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember_me'))

        # 基本欄位驗證
        if not username:
            errors['username'] = '請輸入使用者名稱'
        if not password:
            errors['password'] = '請輸入密碼'

        if not errors:
            # 查找使用者
            sql = text("SELECT * FROM user WHERE username = :username")
            result = db.session.execute(sql, {'username': username}).first()

            if result:
                user = User.query.get(result.id)  # 將原始資料轉為 SQLAlchemy model 使用
                if check_password_hash(user.password_hash, password):
                    login_user(user, remember=remember)
                    flash('登入成功！')
                    return redirect(url_for('index'))
                else:
                    errors['password'] = '密碼錯誤'
            else:
                errors['username'] = '使用者不存在'

    return render_template('login.html', form=form, errors=errors)
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('請檢查你的電子郵件以獲取重設密碼的指示')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='重設密碼', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    errors = {}

    if request.method == 'POST':
        # CSRF 驗證
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            errors['csrf'] = 'CSRF 驗證失敗'

        # 取得欄位並去除多餘空白
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        # 手動表單驗證
        if not username:
            errors['username'] = '請輸入使用者名稱'
        if not email or '@' not in email:
            errors['email'] = '請輸入有效 Email'
        if not password:
            errors['password'] = '請輸入密碼'
        if password != password2:
            errors['password2'] = '密碼不一致'

        # 重複資料驗證（只有在前面沒錯時才進行）
        if not errors:
            sql_user = text("SELECT id FROM user WHERE username = :username")
            if db.session.execute(sql_user, {'username': username}).first():
                errors['username'] = '使用者名稱已存在'

            sql_email = text("SELECT id FROM user WHERE email = :email")
            if db.session.execute(sql_email, {'email': email}).first():
                errors['email'] = 'Email 已被註冊'

        # 若沒有錯誤就寫入 DB
        if not errors:
            hashed_password = generate_password_hash(password)
            sql_insert = text("""
                INSERT INTO user (username, email, password_hash)
                VALUES (:username, :email, :password_hash)
            """)
            db.session.execute(sql_insert, {
                'username': username,
                'email': email,
                'password_hash': hashed_password
            })
            db.session.commit()
            flash('註冊成功！')
            return redirect(url_for('login'))

    return render_template('register.html',form=form, errors=errors)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
    



