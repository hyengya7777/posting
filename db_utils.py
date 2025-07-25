import sqlite3
import os
from datetime import datetime

DATABASE = 'board.db'

def init_database():
    """데이터베이스와 테이블을 초기화합니다"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # posts 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"데이터베이스 '{DATABASE}' 초기화 완료!")

def add_sample_data():
    """샘플 데이터를 추가합니다"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    sample_posts = [
        ('홍길동', '안녕하세요! 첫 번째 게시글입니다.'),
        ('김철수', '반갑습니다. 게시판이 잘 만들어졌네요!'),
        ('이영희', 'Flask와 SQLite로 만든 게시판입니다. 정말 좋아요!'),
        ('박민수', '댓글 기능도 있으면 좋겠어요.'),
        ('최지영', '디자인이 깔끔하고 사용하기 편해요!')
    ]
    
    cursor.executemany(
        'INSERT INTO posts (nickname, content) VALUES (?, ?)',
        sample_posts
    )
    
    conn.commit()
    conn.close()
    print(f"{len(sample_posts)}개의 샘플 게시글이 추가되었습니다!")

def view_all_posts():
    """모든 게시글을 조회합니다"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    
    if posts:
        print(f"\n=== 총 {len(posts)}개의 게시글 ===")
        for post in posts:
            print(f"ID: {post[0]}")
            print(f"닉네임: {post[1]}")
            print(f"내용: {post[2]}")
            print(f"작성일: {post[3]}")
            print("-" * 40)
    else:
        print("게시글이 없습니다.")
    
    conn.close()

def clear_all_posts():
    """모든 게시글을 삭제합니다"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM posts')
    count = cursor.fetchone()[0]
    
    if count > 0:
        confirm = input(f"{count}개의 게시글을 모두 삭제하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            cursor.execute('DELETE FROM posts')
            conn.commit()
            print("모든 게시글이 삭제되었습니다.")
        else:
            print("삭제가 취소되었습니다.")
    else:
        print("삭제할 게시글이 없습니다.")
    
    conn.close()

def get_db_info():
    """데이터베이스 정보를 표시합니다"""
    if os.path.exists(DATABASE):
        size = os.path.getsize(DATABASE)
        print(f"데이터베이스 파일: {os.path.abspath(DATABASE)}")
        print(f"파일 크기: {size} bytes")
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM posts')
        count = cursor.fetchone()[0]
        print(f"총 게시글 수: {count}개")
        conn.close()
    else:
        print("데이터베이스 파일이 존재하지 않습니다.")

def main():
    """메인 메뉴"""
    while True:
        print("\n=== 게시판 데이터베이스 관리 ===")
        print("1. 데이터베이스 초기화")
        print("2. 샘플 데이터 추가")
        print("3. 모든 게시글 조회")
        print("4. 모든 게시글 삭제")
        print("5. 데이터베이스 정보 확인")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-5): ").strip()
        
        if choice == '1':
            init_database()
        elif choice == '2':
            add_sample_data()
        elif choice == '3':
            view_all_posts()
        elif choice == '4':
            clear_all_posts()
        elif choice == '5':
            get_db_info()
        elif choice == '0':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 다시 선택해주세요.")

if __name__ == '__main__':
    main()