from flask import Flask, render_template, request, redirect, url_for, g, flash
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # 실제로는 환경변수로 설정

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.environ.get('DATABASE_URL')

def hash_password(password):
    """비밀번호를 해시화하는 함수"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    """데이터베이스 연결을 가져오는 함수"""
    if 'db' not in g:
        if DATABASE_URL:
            # 배포 환경 (PostgreSQL)
            g.db = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            # 로컬 환경 (SQLite 폴백)
            import sqlite3
            g.db = sqlite3.connect('board.db')
            g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """데이터베이스 연결을 닫는 함수"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """데이터베이스 초기화 함수"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        if DATABASE_URL:
            # PostgreSQL용 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    nickname VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    password_hash VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite용 테이블 생성 (로컬 개발용)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT NOT NULL,
                    content TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        db.commit()

def get_all_posts():
    """모든 게시글을 가져오는 함수"""
    db = get_db()
    cursor = db.cursor()
    
    if DATABASE_URL:
        # PostgreSQL
        cursor.execute(
            'SELECT id, nickname, content, created_at '
            'FROM posts '
            'ORDER BY created_at DESC'
        )
        posts = cursor.fetchall()
        
        # 컬럼명으로 접근할 수 있도록 딕셔너리 변환
        formatted_posts = []
        for post in posts:
            formatted_post = {
                'id': post[0],
                'nickname': post[1], 
                'content': post[2],
                'date': post[3].strftime('%Y-%m-%d %H:%M:%S') if post[3] else ''
            }
            formatted_posts.append(formatted_post)
    else:
        # SQLite (로컬)
        posts = cursor.execute(
            'SELECT id, nickname, content, created_at '
            'FROM posts '
            'ORDER BY created_at DESC'
        ).fetchall()
        
        formatted_posts = []
        for post in posts:
            formatted_post = dict(post)
            try:
                dt = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                formatted_post['date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_post['date'] = post['created_at']
            formatted_posts.append(formatted_post)
    
    return formatted_posts

def get_post_by_id(post_id):
    """ID로 특정 게시글을 가져오는 함수"""
    db = get_db()
    cursor = db.cursor()
    
    if DATABASE_URL:
        cursor.execute(
            'SELECT id, nickname, content, password_hash, created_at FROM posts WHERE id = %s',
            (post_id,)
        )
        post = cursor.fetchone()
        if post:
            return {
                'id': post[0],
                'nickname': post[1],
                'content': post[2],
                'password_hash': post[3],
                'date': post[4].strftime('%Y-%m-%d %H:%M:%S') if post[4] else ''
            }
    else:
        post = cursor.execute(
            'SELECT id, nickname, content, password_hash, created_at FROM posts WHERE id = ?',
            (post_id,)
        ).fetchone()
        if post:
            formatted_post = dict(post)
            try:
                dt = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                formatted_post['date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_post['date'] = post['created_at']
            return formatted_post
    return None

def add_post(nickname, content, password):
    """새 게시글을 추가하는 함수"""
    db = get_db()
    cursor = db.cursor()
    password_hash = hash_password(password)
    
    cursor.execute(
        'INSERT INTO posts (nickname, content, password_hash) VALUES (%s, %s, %s)' if DATABASE_URL 
        else 'INSERT INTO posts (nickname, content, password_hash) VALUES (?, ?, ?)',
        (nickname, content, password_hash)
    )
    db.commit()

def update_post(post_id, nickname, content):
    """게시글을 수정하는 함수"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'UPDATE posts SET nickname = %s, content = %s WHERE id = %s' if DATABASE_URL
        else 'UPDATE posts SET nickname = ?, content = ? WHERE id = ?',
        (nickname, content, post_id)
    )
    db.commit()

def delete_post(post_id):
    """게시글을 삭제하는 함수"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'DELETE FROM posts WHERE id = %s' if DATABASE_URL
        else 'DELETE FROM posts WHERE id = ?',
        (post_id,)
    )
    db.commit()

def verify_password(post_id, password):
    """비밀번호를 확인하는 함수"""
    post = get_post_by_id(post_id)
    if post:
        return post['password_hash'] == hash_password(password)
    return False

@app.teardown_appcontext
def close_db_connection(exception):
    """요청 종료 시 데이터베이스 연결 정리"""
    close_db(exception)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        content = request.form.get('content', '').strip()
        password = request.form.get('password', '').strip()
        
        if nickname and content and password:
            add_post(nickname, content, password)
            flash('게시글이 작성되었습니다!', 'success')
        else:
            flash('모든 필드를 입력해주세요.', 'error')
        
        return redirect(url_for('index'))
    
    posts = get_all_posts()
    return render_template('index.html', posts=posts)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = get_post_by_id(post_id)
    if not post:
        flash('게시글을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        
        if not verify_password(post_id, password):
            flash('비밀번호가 틀렸습니다.', 'error')
            return render_template('edit.html', post=post)
        
        nickname = request.form.get('nickname', '').strip()
        content = request.form.get('content', '').strip()
        
        if nickname and content:
            update_post(post_id, nickname, content)
            flash('게시글이 수정되었습니다!', 'success')
            return redirect(url_for('index'))
        else:
            flash('닉네임과 내용을 모두 입력해주세요.', 'error')
    
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post_route(post_id):
    password = request.form.get('password', '').strip()
    
    if not verify_password(post_id, password):
        flash('비밀번호가 틀렸습니다.', 'error')
        return redirect(url_for('index'))
    
    delete_post(post_id)
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/clear')
def clear_posts():
    """관리자용: 모든 게시글 삭제 (개발용)"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM posts')
    db.commit()
    flash('모든 게시글이 삭제되었습니다.', 'info')
    return redirect(url_for('index'))

# 애플리케이션 시작 시 데이터베이스 초기화
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("서버 시작: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)