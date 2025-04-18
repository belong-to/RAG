import logging
import re
import streamlit as st
from modules.db_pool import query, query_one, execute
from modules.email_verification_enhanced import send_verification_email, generate_verification_code, store_verification_code, verify_code
import hashlib
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('user_profile')

# 密码加密函数
def hash_password(password):
    """
    密码加密
    
    Args:
        password (str): 原始密码
        
    Returns:
        str: 加密后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()

# 获取用户资料
def get_user_profile(user_id):
    """
    获取用户资料
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        dict: 用户资料信息
    """
    try:
        user = query_one("SELECT id, username, email, email_verified, role, created_at FROM users WHERE id = %s", (user_id,))
        if not user:
            logger.warning(f"未找到用户ID: {user_id}的资料")
            return None
        
        logger.info(f"成功获取用户ID: {user_id}的资料")
        return user
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return None

# 更新用户资料
def update_user_profile(user_id, data):
    """
    更新用户资料
    
    Args:
        user_id (int): 用户ID
        data (dict): 要更新的数据，可包含username, email等字段
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 构建更新语句
        fields = []
        values = []
        
        for key, value in data.items():
            if key in ['username', 'email']:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if not fields:
            return False, "没有提供有效的更新字段"
        
        # 添加用户ID到参数列表
        values.append(user_id)
        
        # 执行更新
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        execute(query, tuple(values))
        
        logger.info(f"用户ID: {user_id}的资料已更新")
        return True, "资料更新成功"
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return False, f"更新失败: {str(e)}"

# 验证当前密码
def verify_current_password(user_id, current_password):
    """
    验证用户当前密码是否正确
    
    Args:
        user_id (int): 用户ID
        current_password (str): 当前密码
        
    Returns:
        bool: 密码是否正确
    """
    try:
        user = query_one("SELECT password FROM users WHERE id = %s", (user_id,))
        if not user:
            return False
        
        hashed_password = hash_password(current_password)
        return hashed_password == user['password']
    except Exception as e:
        logger.error(f"验证当前密码失败: {e}")
        return False

# 更新密码
def update_password(user_id, new_password):
    """
    更新用户密码
    
    Args:
        user_id (int): 用户ID
        new_password (str): 新密码
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        hashed_password = hash_password(new_password)
        execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id))
        
        logger.info(f"用户ID: {user_id}的密码已更新")
        return True, "密码更新成功"
    except Exception as e:
        logger.error(f"更新密码失败: {e}")
        return False, f"更新密码失败: {str(e)}"

# 验证密码强度
def is_strong_password(password):
    """
    验证密码强度
    
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

# 发起密码重置
def initiate_password_reset(email):
    """
    发起密码重置流程
    
    Args:
        email (str): 用户邮箱
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 检查邮箱是否存在
        user = query_one("SELECT id, username FROM users WHERE email = %s", (email,))
        if not user:
            logger.warning(f"密码重置请求: 邮箱 {email} 不存在")
            return False, "该邮箱未注册"
        
        # 生成验证码
        verification_code = generate_verification_code(6, True)  # 使用字母数字混合的验证码
        
        # 发送验证码邮件
        success, message = send_verification_email(email, verification_code, "reset_password")
        if not success:
            return False, message
        
        # 存储验证码
        store_result, store_message = store_verification_code(email, verification_code)
        if not store_result:
            return False, store_message
        
        logger.info(f"密码重置验证码已发送到: {email}")
        return True, "密码重置验证码已发送到您的邮箱"
    except Exception as e:
        logger.error(f"发起密码重置失败: {e}")
        return False, f"发起密码重置失败: {str(e)}"

# 完成密码重置
def complete_password_reset(email, verification_code, new_password):
    """
    完成密码重置流程
    
    Args:
        email (str): 用户邮箱
        verification_code (str): 验证码
        new_password (str): 新密码
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 验证验证码
        verify_result, verify_message = verify_code(email, verification_code)
        if not verify_result:
            return False, verify_message
        
        # 验证密码强度
        strong_password, password_message = is_strong_password(new_password)
        if not strong_password:
            return False, password_message
        
        # 更新密码
        hashed_password = hash_password(new_password)
        execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        
        logger.info(f"用户邮箱: {email}的密码已重置")
        return True, "密码重置成功，请使用新密码登录"
    except Exception as e:
        logger.error(f"完成密码重置失败: {e}")
        return False, f"密码重置失败: {str(e)}"

# 更新邮箱验证状态
def update_email_verification_status(user_id, verified=True):
    """
    更新用户邮箱验证状态
    
    Args:
        user_id (int): 用户ID
        verified (bool): 验证状态，默认为True
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        execute("UPDATE users SET email_verified = %s WHERE id = %s", (verified, user_id))
        
        logger.info(f"用户ID: {user_id}的邮箱验证状态已更新为: {verified}")
        return True, "邮箱验证状态已更新"
    except Exception as e:
        logger.error(f"更新邮箱验证状态失败: {e}")
        return False, f"更新邮箱验证状态失败: {str(e)}"

# 检查用户邮箱验证状态
def check_email_verification_status(user_id):
    """
    检查用户邮箱是否已验证
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        bool: 邮箱是否已验证
    """
    try:
        user = query_one("SELECT email_verified FROM users WHERE id = %s", (user_id,))
        if not user:
            return False
        
        return user['email_verified']
    except Exception as e:
        logger.error(f"检查邮箱验证状态失败: {e}")
        return False

# 发送邮箱验证提醒
def send_verification_reminder(user_id):
    """
    向未验证邮箱的用户发送验证提醒
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        # 获取用户信息
        user = query_one("SELECT email, email_verified FROM users WHERE id = %s", (user_id,))
        if not user:
            return False, "用户不存在"
        
        # 检查邮箱是否已验证
        if user['email_verified']:
            return False, "邮箱已验证，无需发送提醒"
        
        # 生成新的验证码
        verification_code = generate_verification_code()
        
        # 发送验证码邮件
        success, message = send_verification_email(user['email'], verification_code, "register")
        if not success:
            return False, message
        
        # 存储验证码
        store_result, store_message = store_verification_code(user['email'], verification_code)
        if not store_result:
            return False, store_message
        
        logger.info(f"验证提醒已发送到: {user['email']}")
        return True, "验证提醒已发送到您的邮箱"
    except Exception as e:
        logger.error(f"发送验证提醒失败: {e}")
        return False, f"发送验证提醒失败: {str(e)}"