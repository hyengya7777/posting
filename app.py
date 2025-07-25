from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# 데이터베이스 파일 경로
DATABASE = 'board.db'

def get_db():
    """데이터베이스 연결을 가져오는 함수"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
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
        # 테이블 생성 SQL
        db.execute('''
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
    posts = db.execute(
        'SELECT id, nickname, content, created_at '
        'FROM posts '
        'ORDER BY created_at DESC'
    ).fetchall()
    
    # 날짜 형식을 보기 좋게 변환
    formatted_posts = []
    for post in posts:
        formatted_post = dict(post)
        # SQLite의 TIMESTAMP를 파이썬 datetime으로 변환 후 포맷팅
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
    db.execute(
        'INSERT INTO posts (nickname, content) VALUES (?, ?)',
        (nickname, content)
    )
    db.commit()

# Flask 2.2+ 호환성을 위해 before_first_request 제거

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
    db.execute('DELETE FROM posts')
    db.commit()
    return redirect(url_for('index'))

# 애플리케이션 시작 시 데이터베이스 초기화
with app.app_context():
    init_db()

if __name__ == '__main__':
    print(f"데이터베이스 파일: {os.path.abspath(DATABASE)}")
    print("서버 시작: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)