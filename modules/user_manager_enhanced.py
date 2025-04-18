import logging
import re
import streamlit as st
from modules.db_pool import db_pool, query, query_one, execute
from modules.auth import jwt_auth
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('user_manager')

# 密码加密函数
def hash_password(password):
    """密码加密
    
    Args:
        password (str): 原始密码
        
    Returns:
        str: 加密后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()

# 初始化数据库
def init_db():
    """初始化数据库，创建必要的表"""
    try:
        # 创建用户表
        execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建验证码表
        execute("""
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) NOT NULL,
            code VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE
        )
        """)
        
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

# 创建管理员账户函数
def create_admin_user():
    """创建默认管理员账户"""
    try:
        # 检查管理员账户是否已存在
        admin = query_one("SELECT * FROM users WHERE username = %s", ('admin',))
        if admin:
            logger.info("管理员账户已存在")
            return True  # 管理员账户已存在
        
        # 创建管理员账户
        hashed_password = hash_password('admin')
        execute(
            "INSERT INTO users (username, password, email, email_verified, role) VALUES (%s, %s, %s, %s, %s)",
            ('admin', hashed_password, 'admin@example.com', True, 'admin')
        )
        logger.info("管理员账户创建成功")
        return True
    except Exception as e:
        logger.error(f"创建管理员账户失败: {e}")
        return False

# 用户注册函数
def register_user(username, password, email, role='user'):
    """注册新用户
    
    Args:
        username (str): 用户名
        password (str): 密码
        email (str): 电子邮箱
        role (str): 用户角色，默认为'user'
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 检查用户名是否已存在
        user = query_one("SELECT * FROM users WHERE username = %s", (username,))
        if user:
            return False, "用户名已存在"
        
        # 检查邮箱是否已存在
        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if user:
            return False, "邮箱已被注册"
        
        # 加密密码并存储用户信息
        hashed_password = hash_password(password)
        execute(
            "INSERT INTO users (username, password, email, email_verified, role) VALUES (%s, %s, %s, %s, %s)",
            (username, hashed_password, email, False, role)
        )
        logger.info(f"用户 {username} 注册成功")
        return True, "注册成功！请验证您的邮箱。"
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return False, f"注册失败: {str(e)}"

# 用户登录函数
def login_user(username, password):
    """用户登录
    
    Args:
        username (str): 用户名
        password (str): 密码
        
    Returns:
        tuple: (成功标志, 消息, 用户信息)
    """
    try:
        # 查询用户
        user = query_one("SELECT * FROM users WHERE username = %s", (username,))
        
        if not user:
            return False, "用户名不存在", None
        
        # 验证密码
        hashed_password = hash_password(password)
        if hashed_password != user['password']:
            return False, "密码错误", None
        
        # 生成JWT令牌
        token = jwt_auth.generate_token(user['id'], user['username'], user['role'])
        
        logger.info(f"用户 {username} 登录成功")
        return True, "登录成功！", {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'token': token
        }
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return False, f"登录失败: {str(e)}", None

# 验证邮箱格式
def is_valid_email(email):
    """验证邮箱格式
    
    Args:
        email (str): 电子邮箱
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# 验证密码强度
def is_strong_password(password):
    """验证密码强度
    
    Args:
        password (str): 密码
        
    Returns:
        tuple: (是否强密码, 消息)
    """
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

# 更新用户信息
def update_user(user_id, data):
    """更新用户信息
    
    Args:
        user_id (int): 用户ID
        data (dict): 要更新的数据
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 构建更新语句
        fields = []
        values = []
        
        for key, value in data.items():
            if key == 'password':
                value = hash_password(value)
            fields.append(f"{key} = %s")
            values.append(value)
        
        if not fields:
            return False, "没有提供要更新的字段"
        
        # 添加用户ID
        values.append(user_id)
        
        # 执行更新
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        execute(query, tuple(values))
        
        logger.info(f"用户 ID {user_id} 信息更新成功")
        return True, "用户信息更新成功"
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        return False, f"更新失败: {str(e)}"

# 获取用户信息
def get_user(user_id=None, username=None, email=None):
    """获取用户信息
    
    Args:
        user_id (int): 用户ID
        username (str): 用户名
        email (str): 电子邮箱
        
    Returns:
        dict: 用户信息
    """
    try:
        if user_id:
            return query_one("SELECT * FROM users WHERE id = %s", (user_id,))
        elif username:
            return query_one("SELECT * FROM users WHERE username = %s", (username,))
        elif email:
            return query_one("SELECT * FROM users WHERE email = %s", (email,))
        else:
            return None
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return None

# 获取所有用户
def get_all_users():
    """获取所有用户
    
    Returns:
        list: 用户列表
    """
    try:
        return query("SELECT id, username, email, role, email_verified, created_at FROM users")
    except Exception as e:
        logger.error(f"获取所有用户失败: {e}")
        return []

# 删除用户
def delete_user(user_id):
    """删除用户
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        execute("DELETE FROM users WHERE id = %s", (user_id,))
        logger.info(f"用户 ID {user_id} 已删除")
        return True, "用户已删除"
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return False, f"删除失败: {str(e)}"

# 设置邮箱验证状态
def set_email_verified(email, verified=True):
    """设置邮箱验证状态
    
    Args:
        email (str): 电子邮箱
        verified (bool): 验证状态
        
    Returns:
        bool: 是否成功
    """
    try:
        execute("UPDATE users SET email_verified = %s WHERE email = %s", (verified, email))
        logger.info(f"邮箱 {email} 验证状态已更新为 {verified}")
        return True
    except Exception as e:
        logger.error(f"更新邮箱验证状态失败: {e}")
        return False

# 退出登录函数
def logout():
    """退出登录，清除会话状态"""
    if 'jwt_token' in st.session_state:
        del st.session_state.jwt_token
    if 'username' in st.session_state:
        del st.session_state.username
    if 'logged_in' in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' in st.session_state:
        del st.session_state.user_role
    
    logger.info("用户已退出登录")