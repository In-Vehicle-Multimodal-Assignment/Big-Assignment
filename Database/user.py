import sqlite3
import hashlib
from getpass import getpass
from typing import Optional, Dict
from pathlib import Path

class UserManager:
    def __init__(self, db_name='users.db'):
        """初始化用户数据库"""
        script_dir = Path(__file__).parent
        db_path = script_dir / db_name
        self.conn = sqlite3.connect(
            str(db_path), 
            check_same_thread=False, 
            timeout=10.0  
        )
        self.conn.execute("PRAGMA journal_mode=WAL")  
        self._create_table()

    def _create_table(self):

        """创建用户表"""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            is_admin INTEGER NOT NULL DEFAULT 0,
            has_fatigue_tendency INTEGER NOT NULL DEFAULT 0,
            log_history TEXT
        )
        ''')
        self.conn.commit()


    def add_user(self, username: str, is_admin: bool = False, 
                has_fatigue_tendency: bool = False, log_history: str = '') -> bool:
        """添加新用户"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO users (username, is_admin, has_fatigue_tendency, log_history)
            VALUES (?, ?, ?, ?)
            ''', (username, int(is_admin), int(has_fatigue_tendency), log_history))
            self.conn.commit()
            print(f"用户 '{username}' 添加成功")
            return True
        except sqlite3.IntegrityError:
            print(f"错误: 用户名 '{username}' 已存在")
            return False

    def authenticate(self, username: str, is_admin: bool) -> Optional[Dict]:
        """验证用户登录"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, is_admin, has_fatigue_tendency, log_history 
        FROM users 
        WHERE username = ? 
        ''', (username,))
        
        result = cursor.fetchone()
        if result:
            user = {
                'username': result[0],
                'is_admin': bool(result[1]),
                'has_fatigue_tendency': bool(result[2]),
                'log_history': result[3]
            }
            print(f"登录成功! 欢迎, {username}")
            return user
        else:
            self.add_user(username, is_admin=is_admin, has_fatigue_tendency=False, log_history='')
            user = {
                'username': username,
                'is_admin': is_admin,
                'has_fatigue_tendency': False,
                'log_history': ''
            }
            print("新用户已经建立！")
            return user

    def update_log_history(self, username: str, new_log_entry: str) -> bool:
        """更新用户日志历史"""
        try:
            # 获取现有日志
            current_log = self.get_user(username)['log_history'] or ''
            
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE users 
            SET log_history = ?
            WHERE username = ?
            ''', (current_log + "\n" + new_log_entry, username))
            self.conn.commit()
            print(f"用户 '{username}' 的日志已更新")
            return True
        except Exception as e:
            print(f"更新日志失败: {str(e)}")
            return False

    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, is_admin, has_fatigue_tendency, log_history 
        FROM users 
        WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'username': result[0],
                'is_admin': bool(result[1]),
                'has_fatigue_tendency': bool(result[2]),
                'log_history': result[3]
            }
        return None

    def __del__(self):
        """析构函数，关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

# # 使用示例
# if __name__ == '__main__':
#     manager = UserManager()
    
#     manager.authenticate('user1')
#     manager.update_log_history('user1', '2023-11-01: 用户完成了疲劳测试')
#     manager.update_log_history('user1', '2023-11-02: 用户报告了疲劳症状')

#     user = manager.authenticate('user1')
#     if user:
#         print(f"用户信息: {user}")
#     user = manager.authenticate('user2')
#     if user:
#         print(f"用户信息: {user}")