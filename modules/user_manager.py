import mysql.connector
import hashlib
import re
import streamlit as st

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 用户指定的MySQL密码
    'database': 'RAG'
}

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 初始化数据库
def init_db():
    try:
        # 连接MySQL服务器
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        
        # 使用数据库
        cursor.execute(f"USE {db_config['database']}")
        
        # 创建用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建管理员表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            role VARCHAR(50) DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        st.success("数据库初始化成功！")
        return True
    except mysql.connector.Error as err:
        st.error(f"数据库初始化失败: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 创建管理员账户函数
def create_admin_user():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查管理员账户是否已存在
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            return True  # 管理员账户已存在
        
        # 创建管理员账户
        hashed_password = hash_password('admin')
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
            ('admin', hashed_password, 'admin@example.com')
        )
        conn.commit()
        st.success("管理员账户创建成功！")
        return True
    except mysql.connector.Error as err:
        st.error(f"创建管理员账户失败: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 用户注册函数
def register_user(username, password, email):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "用户名已存在"
        
        # 检查邮箱是否已存在
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "邮箱已被注册"
        
        # 加密密码并存储用户信息
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, email, email_verified) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, email, False)
        )
        conn.commit()
        return True, "注册成功！请验证您的邮箱。"
    except mysql.connector.Error as err:
        return False, f"注册失败: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 用户登录函数
def login_user(username, password):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            return False, "用户名不存在"
        
        # 验证密码
        hashed_password = hash_password(password)
        if hashed_password == user[2]:  # 索引2是密码字段
            return True, "登录成功！"
        else:
            return False, "密码错误"
    except mysql.connector.Error as err:
        return False, f"登录失败: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 验证邮箱格式
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# 验证密码强度
def is_strong_password(password):
    # 密码至少8位，包含大小写字母和数字
    if len(password) < 8:
        return False, "密码长度至少为8位"
    if not re.search(r'[A-Z]', password):
        return False, "密码需包含大写字母"
    if not re.search(r'[a-z]', password):
        return False, "密码需包含小写字母"
    if not re.search(r'\d', password):
        return False, "密码需包含数字"
    return True, ""

# 退出登录函数
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "login"
    st.rerun()  # 强制重新运行应用以应用状态变化

# 将普通用户提升为管理员函数
def promote_to_admin(username, admin_username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 验证操作者是否为管理员
        cursor.execute("SELECT * FROM admins WHERE username = %s", (admin_username,))
        if not cursor.fetchone():
            return False, "您没有管理员权限执行此操作"
        
        # 检查要提升的用户是否存在
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return False, "用户不存在"
        
        # 检查用户是否已经是管理员
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "该用户已经是管理员"
        
        # 获取用户信息
        user_id = user[0]  # 用户ID
        user_password = user[2]  # 密码
        user_email = user[3]  # 邮箱
        
        # 将用户添加到管理员表
        cursor.execute(
            "INSERT INTO admins (username, password, email) VALUES (%s, %s, %s)",
            (username, user_password, user_email)
        )
        conn.commit()
        return True, f"用户 {username} 已成功提升为管理员"
    except mysql.connector.Error as err:
        return False, f"提升管理员失败: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 获取所有管理员列表
def get_all_admins():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询所有管理员
        cursor.execute("SELECT id, username, email, role, created_at FROM admins")
        admins = cursor.fetchall()
        return admins
    except mysql.connector.Error as err:
        st.error(f"获取管理员数据失败: {err}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()