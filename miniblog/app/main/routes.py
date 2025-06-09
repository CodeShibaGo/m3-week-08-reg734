from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from flask_login import logout_user, current_user, login_required
from sqlalchemy import text
import sqlalchemy as sa
from app.models import User, Post
from urllib.parse import urlsplit
from datetime import datetime, timezone
from langdetect import detect, LangDetectException
from app.translate import translate
from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash('你的貼文現在已發布！')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='首頁', form = form, posts=posts.items, next_url=next_url,prev_url=prev_url)

@bp.route('/explore')
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
        SELECT post.id AS post_id, post.body, post.timestamp, post.user_id,post.language,
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

    next_url = url_for('main.explore', page=pagination.next_num) if pagination.has_next else None
    prev_url = url_for('main.explore', page=pagination.prev_num) if pagination.has_prev else None

    return render_template('index.html', title='探索', posts=posts,
                           next_url=next_url, prev_url=prev_url)


    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)



@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))
    
@bp.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    if not data or 'text' not in data or 'source_language' not in data or 'dest_language' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    text = data['text']
    source_language = data['source_language']
    dest_language = data['dest_language']

    translated_text = translate(text, source_language, dest_language)
    return jsonify({'text': translated_text})
    



