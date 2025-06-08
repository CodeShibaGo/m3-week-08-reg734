from flask import render_template, flash, redirect, url_for, request
from app import db
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import  login_user, logout_user, current_user, login_required
from sqlalchemy import text
import sqlalchemy as sa
from app.models import User
from urllib.parse import urlsplit
from werkzeug.security import generate_password_hash,check_password_hash
from flask_wtf.csrf import validate_csrf, CSRFError
from app.auth import bp
from app.auth.email import send_password_reset_email





@bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
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
                    return redirect(url_for('main.index'))
                else:
                    errors['password'] = '密碼錯誤'
            else:
                errors['username'] = '使用者不存在'

    return render_template('auth/login.html', form=form, errors=errors)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
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
            return redirect(url_for('auth.login'))

    return render_template('register.html',form=form, errors=errors)



@bp.route('/reset_password_request', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html',
                           title='重設密碼', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)





    



