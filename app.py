from flask import Flask, render_template, request, redirect, url_for, g
import psycopg2
import psycopg2.extras
from datetime import datetime
import os

app = Flask(__name__)

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.environ.get('DATABASE_URL')

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

def add_post(nickname, content):
    """새 게시글을 추가하는 함수"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'INSERT INTO posts (nickname, content) VALUES (%s, %s)' if DATABASE_URL 
        else 'INSERT INTO posts (nickname, content) VALUES (?, ?)',
        (nickname, content)
    )
    db.commit()

@app.teardown_appcontext
def close_db_connection(exception):
    """요청 종료 시 데이터베이스 연결 정리"""
    close_db(exception)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        content = request.form.get('content', '').strip()
        
        if nickname and content:
            add_post(nickname, content)
        
        return redirect(url_for('index'))
    
    posts = get_all_posts()
    return render_template('index.html', posts=posts)

@app.route('/admin/clear')
def clear_posts():
    """관리자용: 모든 게시글 삭제 (개발용)"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM posts')
    db.commit()
    return redirect(url_for('index'))

# 애플리케이션 시작 시 데이터베이스 초기화
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("서버 시작: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)