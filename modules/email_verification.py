import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import time

# 邮件服务器配置
email_config = {
    'smtp_server': 'smtp.qq.com',  # 默认使用QQ邮箱的SMTP服务器
    'smtp_port': 587,  # 使用TLS的端口
    'sender_email': '',  # 发件人邮箱，需要在使用前设置
    'sender_password': ''  # 发件人邮箱密码或授权码，需要在使用前设置
}

# 生成随机验证码
def generate_verification_code(length=6):
    """
    生成指定长度的随机验证码
    :param length: 验证码长度，默认为6位
    :return: 随机验证码
    """
    # 使用数字生成验证码
    return ''.join(random.choices(string.digits, k=length))

# 发送验证码邮件
def send_verification_email(to_email, verification_code):
    """
    发送包含验证码的邮件
    :param to_email: 收件人邮箱
    :param verification_code: 验证码
    :return: 是否发送成功，错误信息
    """
    # 检查邮箱配置是否完整
    if not email_config['sender_email'] or not email_config['sender_password']:
        return False, "邮箱配置不完整，请设置发件人邮箱和密码"
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = email_config['sender_email']
        msg['To'] = to_email
        msg['Subject'] = "RAG系统 - 邮箱验证码"
        
        # 邮件正文
        body = f"""
        <html>
        <body>
            <h2>RAG系统 - 邮箱验证</h2>
            <p>您好！</p>
            <p>感谢您注册RAG文档检索系统。您的邮箱验证码是：</p>
            <h3 style="color: #4CAF50;">{verification_code}</h3>
            <p>验证码有效期为10分钟，请尽快完成验证。</p>
            <p>如果您没有注册我们的系统，请忽略此邮件。</p>
            <p>此邮件为系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        
        # 设置HTML格式的邮件内容
        msg.attach(MIMEText(body, 'html'))
        
        # 连接到SMTP服务器
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()  # 启用TLS加密
        server.login(email_config['sender_email'], email_config['sender_password'])
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        
        return True, "验证码已发送到您的邮箱"
    except Exception as e:
        return False, f"发送邮件失败: {str(e)}"

# 设置邮箱配置
def set_email_config(sender_email, sender_password, smtp_server=None, smtp_port=None):
    """
    设置邮箱配置
    :param sender_email: 发件人邮箱
    :param sender_password: 发件人邮箱密码或授权码
    :param smtp_server: SMTP服务器地址，默认为smtp.qq.com
    :param smtp_port: SMTP服务器端口，默认为587
    """
    email_config['sender_email'] = sender_email
    email_config['sender_password'] = sender_password
    
    if smtp_server:
        email_config['smtp_server'] = smtp_server
    if smtp_port:
        email_config['smtp_port'] = smtp_port

# 验证码存储和验证
verification_codes = {}  # 用于存储验证码和过期时间

# 存储验证码
def store_verification_code(email, code, expiry_minutes=10):
    """
    存储验证码和过期时间
    :param email: 用户邮箱
    :param code: 验证码
    :param expiry_minutes: 过期时间（分钟），默认10分钟
    """
    expiry_time = time.time() + (expiry_minutes * 60)  # 当前时间 + 过期分钟数
    verification_codes[email] = {'code': code, 'expiry': expiry_time}

# 验证验证码
def verify_code(email, code):
    """
    验证用户输入的验证码是否正确且未过期
    :param email: 用户邮箱
    :param code: 用户输入的验证码
    :return: 验证结果，错误信息
    """
    # 检查邮箱是否存在验证码记录
    if email not in verification_codes:
        return False, "验证码不存在或已过期，请重新获取"
    
    # 获取验证码信息
    code_info = verification_codes[email]
    
    # 检查验证码是否过期
    if time.time() > code_info['expiry']:
        # 删除过期验证码
        del verification_codes[email]
        return False, "验证码已过期，请重新获取"
    
    # 检查验证码是否正确
    if code != code_info['code']:
        return False, "验证码错误，请重新输入"
    
    # 验证成功后删除验证码记录
    del verification_codes[email]
    return True, "验证成功"