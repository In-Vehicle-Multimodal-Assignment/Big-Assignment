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
        self.add_user('admin', is_admin=True)

    def _create_table(self):
        """创建用户表"""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            is_admin INTEGER NOT NULL DEFAULT 0,
            has_fatigue_tendency INTEGER NOT NULL DEFAULT 0,
            has_distraction_tendency INTEGER NOT NULL DEFAULT 0,
            prefers_air_conditioner INTEGER NOT NULL DEFAULT 0,
            prefers_music INTEGER NOT NULL DEFAULT 0,
            log_history TEXT
        )
        ''')
        self.conn.commit()

    def add_user(self, username: str, is_admin: bool = False, 
                has_fatigue_tendency: bool = False,
                has_distraction_tendency: bool = False,
                prefers_air_conditioner: bool = False,
                prefers_music: bool = False,
                log_history: str = '') -> bool:
        """添加新用户"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO users 
            (username, is_admin, has_fatigue_tendency, has_distraction_tendency, 
             prefers_air_conditioner, prefers_music, log_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, int(is_admin), int(has_fatigue_tendency), 
                 int(has_distraction_tendency), int(prefers_air_conditioner),
                 int(prefers_music), log_history))
            self.conn.commit()
            # print(f"用户 '{username}' 添加成功")
            return True
        except sqlite3.IntegrityError:
            # print(f"错误: 用户名 '{username}' 已存在")
            return False


    def authenticate(self, username: str) -> tuple:
        """验证用户登录"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, is_admin, has_fatigue_tendency, has_distraction_tendency,
               prefers_air_conditioner, prefers_music, log_history 
        FROM users 
        WHERE username = ? 
        ''', (username,))
        
        result = cursor.fetchone()
        if result:
            return result
        else:
            self.add_user(username)
            return (username, False, False, False, False, False, "")

    def update_log_history(self, username: str, new_log_entry: str) -> bool:
        """更新用户日志历史，最多保留最近5条记录"""
        try:
            # 获取当前日志（如果没有，则初始化为空字符串）
            user_data = self.get_user(username)
            if not user_data:
                return False  # 用户不存在
            
            current_log = user_data['log_history'] or ''
            log_lines = current_log.split('\n') if current_log else []
            
            # 如果已有5条日志，则移除最旧的一条
            if len(log_lines) >= 5:
                log_lines.pop(0)  # 删除最早的日志
            log_lines.append(new_log_entry)
            updated_log = '\n'.join(log_lines)
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE users 
            SET log_history = ?
            WHERE username = ?
            ''', (updated_log, username))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新日志失败: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, is_admin, has_fatigue_tendency, has_distraction_tendency,
               prefers_air_conditioner, prefers_music, log_history 
        FROM users 
        WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'username': result[0],
                'is_admin': bool(result[1]),
                'has_fatigue_tendency': bool(result[2]),
                'has_distraction_tendency': bool(result[3]),
                'prefers_air_conditioner': bool(result[4]),
                'prefers_music': bool(result[5]),
                'log_history': result[6]
            }
        return None
    
    def get_all_usernames(self) -> list[str]:
        """获取所有用户名列表"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT username FROM users
            ''')
            results = cursor.fetchall()
            return [row[0] for row in results]  # 提取用户名组成列表
        except Exception as e:
            print(f"获取用户名列表失败: {e}")
            return []  # 出错时返回空列表

    def update_user_tendencies(self, username: str, tendencies: list[int]) -> bool:
        # 验证输入
        if len(tendencies) != 4 or not all(isinstance(x, int) and x in (0, 1) for x in tendencies):
            print("错误: tendencies参数必须是包含4个0或1的列表")
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE users 
            SET 
                has_fatigue_tendency = ?,
                has_distraction_tendency = ?,
                prefers_air_conditioner = ?,
                prefers_music = ?
            WHERE username = ?
            ''', (
                tendencies[0],  # 疲劳倾向
                tendencies[1],  # 分心倾向
                tendencies[2],  # 空调倾向
                tendencies[3],  # 音乐倾向
                username
            ))
            self.conn.commit()
            return cursor.rowcount > 0  # 返回是否实际更新了行
        except Exception as e:
            print(f"更新用户倾向失败: {e}")
            return False
    
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