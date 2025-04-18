import random
import string
import smtplib
import logging
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_verification')

# 邮件服务器配置
email_config = {
    'smtp_server': 'smtp.qq.com',  # 默认使用QQ邮箱的SMTP服务器
    'smtp_port': 587,  # 使用TLS的端口
    'sender_email': '',  # 发件人邮箱，需要在使用前设置
    'sender_password': '',  # 发件人邮箱密码或授权码，需要在使用前设置
    'sender_name': 'RAG系统'  # 发件人显示名称
}

# 验证码存储和验证
verification_codes = {}  # 用于存储验证码和过期时间

# 生成随机验证码
def generate_verification_code(length=6, use_letters=False):
    """
    生成指定长度的随机验证码
    :param length: 验证码长度，默认为6位
    :param use_letters: 是否使用字母，默认只使用数字
    :return: 随机验证码
    """
    try:
        if use_letters:
            # 使用数字和大写字母生成验证码，排除容易混淆的字符
            chars = string.digits + ''.join([c for c in string.ascii_uppercase if c not in 'OI0'])
        else:
            # 只使用数字生成验证码
            chars = string.digits
        
        code = ''.join(random.choices(chars, k=length))
        logger.info(f"生成验证码: {code[:2]}****")
        return code
    except Exception as e:
        logger.error(f"生成验证码失败: {e}")
        return ''.join(random.choices(string.digits, k=length))  # 出错时使用简单数字验证码

# 验证邮箱格式
def is_valid_email(email):
    """
    验证邮箱格式是否有效
    :param email: 邮箱地址
    :return: 是否有效
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# 发送验证码邮件
def send_verification_email(to_email, verification_code, template="register"):
    """
    发送包含验证码的邮件
    :param to_email: 收件人邮箱
    :param verification_code: 验证码
    :param template: 邮件模板类型，默认为注册模板
    :return: 是否发送成功，错误信息
    """
    # 检查邮箱格式
    if not is_valid_email(to_email):
        return False, "邮箱格式不正确"
    
    # 检查邮箱配置是否完整
    if not email_config['sender_email'] or not email_config['sender_password']:
        logger.error("邮箱配置不完整")
        return False, "邮箱配置不完整，请设置发件人邮箱和密码"
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        sender_name = email_config.get('sender_name', 'RAG系统')
        msg['From'] = f"{sender_name} <{email_config['sender_email']}>"
        msg['To'] = to_email
        
        # 根据模板类型设置不同的主题和内容
        if template == "register":
            msg['Subject'] = "RAG系统 - 注册验证码"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #4285f4; text-align: center;">RAG系统 - 邮箱验证</h2>
                    <p>您好！</p>
                    <p>感谢您注册RAG文档检索系统。您的邮箱验证码是：</p>
                    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 4px; margin: 20px 0;">
                        <h3 style="color: #4CAF50; font-size: 24px; margin: 0;">{verification_code}</h3>
                    </div>
                    <p>验证码有效期为10分钟，请尽快完成验证。</p>
                    <p>如果您没有注册我们的系统，请忽略此邮件。</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #777; text-align: center;">此邮件为系统自动发送，请勿回复。</p>
                </div>
            </body>
            </html>
            """
        elif template == "reset_password":
            msg['Subject'] = "RAG系统 - 密码重置验证码"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #4285f4; text-align: center;">RAG系统 - 密码重置</h2>
                    <p>您好！</p>
                    <p>您正在进行密码重置操作。您的验证码是：</p>
                    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 4px; margin: 20px 0;">
                        <h3 style="color: #4CAF50; font-size: 24px; margin: 0;">{verification_code}</h3>
                    </div>
                    <p>验证码有效期为10分钟，请尽快完成验证。</p>
                    <p>如果您没有请求重置密码，请忽略此邮件并确保您的账号安全。</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #777; text-align: center;">此邮件为系统自动发送，请勿回复。</p>
                </div>
            </body>
            </html>
            """
        else:
            msg['Subject'] = "RAG系统 - 验证码"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #4285f4; text-align: center;">RAG系统 - 验证码</h2>
                    <p>您好！</p>
                    <p>您的验证码是：</p>
                    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 4px; margin: 20px 0;">
                        <h3 style="color: #4CAF50; font-size: 24px; margin: 0;">{verification_code}</h3>
                    </div>
                    <p>验证码有效期为10分钟，请尽快完成验证。</p>
                    <p>如果您没有请求此验证码，请忽略此邮件。</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #777; text-align: center;">此邮件为系统自动发送，请勿回复。</p>
                </div>
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
        
        logger.info(f"验证码邮件已发送到: {to_email}")
        return True, "验证码已发送到您的邮箱"
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP认证失败，请检查邮箱和密码")
        return False, "邮箱认证失败，请检查发件人邮箱和密码"
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {e}")
        return False, f"发送邮件失败: SMTP错误"
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return False, f"发送邮件失败: {str(e)}"

# 设置邮箱配置
def set_email_config(sender_email, sender_password, smtp_server=None, smtp_port=None, sender_name=None):
    """
    设置邮箱配置
    :param sender_email: 发件人邮箱
    :param sender_password: 发件人邮箱密码或授权码
    :param smtp_server: SMTP服务器地址，默认为smtp.qq.com
    :param smtp_port: SMTP服务器端口，默认为587
    :param sender_name: 发件人显示名称
    :return: 是否设置成功
    """
    try:
        email_config['sender_email'] = sender_email
        email_config['sender_password'] = sender_password
        
        if smtp_server:
            email_config['smtp_server'] = smtp_server
        if smtp_port:
            email_config['smtp_port'] = smtp_port
        if sender_name:
            email_config['sender_name'] = sender_name
            
        logger.info("邮箱配置已更新")
        return True
    except Exception as e:
        logger.error(f"设置邮箱配置失败: {e}")
        return False

# 存储验证码
def store_verification_code(email, code, expiry_minutes=10):
    """
    存储验证码和过期时间
    :param email: 用户邮箱
    :param code: 验证码
    :param expiry_minutes: 过期时间（分钟），默认10分钟
    :return: 是否存储成功
    """
    try:
        # 清理过期验证码
        clean_expired_codes()
        
        # 检查是否频繁请求验证码
        if email in verification_codes:
            last_request = verification_codes[email].get('last_request', 0)
            if time.time() - last_request < 60:  # 限制1分钟内只能请求一次
                logger.warning(f"邮箱 {email} 请求验证码过于频繁")
                return False, "请求过于频繁，请1分钟后再试"
        
        # 存储新验证码
        expiry_time = time.time() + (expiry_minutes * 60)  # 当前时间 + 过期分钟数
        verification_codes[email] = {
            'code': code, 
            'expiry': expiry_time,
            'attempts': 0,  # 验证尝试次数
            'last_request': time.time()  # 上次请求时间
        }
        
        # 格式化过期时间为可读格式
        expiry_datetime = datetime.fromtimestamp(expiry_time)
        expiry_str = expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"验证码已存储: {email}, 过期时间: {expiry_str}")
        
        return True, "验证码已生成"
    except Exception as e:
        logger.error(f"存储验证码失败: {e}")
        return False, f"存储验证码失败: {str(e)}"

# 验证验证码
def verify_code(email, code):
    """
    验证用户输入的验证码是否正确且未过期
    :param email: 用户邮箱
    :param code: 用户输入的验证码
    :return: 验证结果，错误信息
    """
    try:
        # 清理过期验证码
        clean_expired_codes()
        
        # 检查邮箱是否存在验证码记录
        if email not in verification_codes:
            logger.warning(f"邮箱 {email} 没有验证码记录或已过期")
            return False, "验证码不存在或已过期，请重新获取"
        
        # 获取验证码信息
        code_info = verification_codes[email]
        
        # 检查验证码是否过期
        if time.time() > code_info['expiry']:
            # 删除过期验证码
            del verification_codes[email]
            logger.warning(f"邮箱 {email} 的验证码已过期")
            return False, "验证码已过期，请重新获取"
        
        # 增加尝试次数
        code_info['attempts'] += 1
        
        # 检查尝试次数是否超过限制
        if code_info['attempts'] > 5:
            # 删除验证码记录
            del verification_codes[email]
            logger.warning(f"邮箱 {email} 验证尝试次数过多")
            return False, "验证尝试次数过多，请重新获取验证码"
        
        # 检查验证码是否正确
        if code != code_info['code']:
            logger.warning(f"邮箱 {email} 输入的验证码错误")
            return False, "验证码错误，请重新输入"
        
        # 验证成功后删除验证码记录
        del verification_codes[email]
        logger.info(f"邮箱 {email} 验证成功")
        return True, "验证成功"
    except Exception as e:
        logger.error(f"验证码验证失败: {e}")
        return False, f"验证失败: {str(e)}"

# 清理过期验证码
def clean_expired_codes():
    """
    清理所有过期的验证码
    """
    try:
        current_time = time.time()
        expired_emails = [email for email, info in verification_codes.items() if current_time > info['expiry']]
        
        for email in expired_emails:
            del verification_codes[email]
            logger.info(f"已清理过期验证码: {email}")
        
        return len(expired_emails)
    except Exception as e:
        logger.error(f"清理过期验证码失败: {e}")
        return 0

# 检查邮箱是否有未过期的验证码
def has_active_code(email):
    """
    检查邮箱是否有未过期的验证码
    :param email: 用户邮箱
    :return: 是否有未过期验证码，剩余有效时间（秒）
    """
    try:
        # 清理过期验证码
        clean_expired_codes()
        
        if email not in verification_codes:
            return False, 0
        
        code_info = verification_codes[email]
        remaining_time = code_info['expiry'] - time.time()
        
        if remaining_time <= 0:
            del verification_codes[email]
            return False, 0
        
        return True, int(remaining_time)
    except Exception as e:
        logger.error(f"检查验证码状态失败: {e}")
        return False, 0

# 测试邮箱配置
def test_email_config():
    """
    测试邮箱配置是否正确
    :return: 是否成功，错误信息
    """
    try:
        # 检查邮箱配置是否完整
        if not email_config['sender_email'] or not email_config['sender_password']:
            return False, "邮箱配置不完整，请设置发件人邮箱和密码"
        
        # 连接到SMTP服务器
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()  # 启用TLS加密
        server.login(email_config['sender_email'], email_config['sender_password'])
        server.quit()
        
        logger.info("邮箱配置测试成功")
        return True, "邮箱配置测试成功"
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP认证失败，请检查邮箱和密码")
        return False, "邮箱认证失败，请检查发件人邮箱和密码"
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {e}")
        return False, f"邮箱配置测试失败: SMTP错误"
    except Exception as e:
        logger.error(f"邮箱配置测试失败: {e}")
        return False, f"邮箱配置测试失败: {str(e)}"