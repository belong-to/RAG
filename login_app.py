import streamlit as st
import mysql.connector
import hashlib
import re
import os
from modules.email_verification import generate_verification_code, send_verification_email, store_verification_code, verify_code, set_email_config

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 用户指定的MySQL密码
    'database': 'RAG'
}

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

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        return True, "注册成功！"
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
        cursor = conn.cursor(dictionary=True)  # 使用字典游标
        
        # 查询用户
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            return False, "用户名不存在", None
        
        # 验证密码
        hashed_password = hash_password(password)
        if hashed_password == user['password']:  # 使用字典键访问
            # 返回用户信息
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
            return True, "登录成功！", user_info
        else:
            return False, "密码错误", None
    except mysql.connector.Error as err:
        return False, f"登录失败: {err}", None
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

# 页面设置
st.set_page_config(page_title='RAG系统 - 用户认证', page_icon=':lock:', layout='wide')

# 加载自定义CSS
try:
    with open('e:/RAG实战/pages/login_style.css', encoding='utf-8') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
except UnicodeDecodeError:
    with open('e:/RAG实战/pages/login_style.css', encoding='latin-1') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

# 初始化session_state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'page' not in st.session_state:
    st.session_state.page = "login"  # 默认显示登录页面

# 切换页面函数
def change_page(page):
    st.session_state.page = page

# 退出登录函数
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "login"
    st.rerun()  # 强制重新运行应用以应用状态变化

# 初始化数据库
init_db()

# 创建管理员账户
create_admin_user()

# 页面标题
st.title('RAG文档检索系统')
st.markdown('---')

# 侧边栏
with st.sidebar:
    st.header("导航")
    if st.session_state.logged_in:
        st.write(f"欢迎, {st.session_state.username}!")
        if st.button("进入RAG系统", use_container_width=True):
            st.session_state.page = "rag"
        if st.button("退出登录", use_container_width=True):
            logout()
    else:
        if st.button("登录", use_container_width=True):
            st.session_state.page = "login"
        if st.button("注册", use_container_width=True):
            st.session_state.page = "register"

# 主页面内容
if not st.session_state.logged_in:
    # 登录页面
    if st.session_state.page == "login":
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
                st.markdown("<h2 class='auth-title'>用户登录</h2>", unsafe_allow_html=True)
                
                with st.form("login_form", clear_on_submit=False):
                    st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
                    
                    # 用户名输入框
                    st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                    st.markdown("<i class='auth-input-icon'>👤</i>", unsafe_allow_html=True)
                    username = st.text_input("用户名", placeholder="请输入您的用户名")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 密码输入框
                    st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                    st.markdown("<i class='auth-input-icon'>🔒</i>", unsafe_allow_html=True)
                    password = st.text_input("密码", type="password", placeholder="请输入您的密码")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    submit = st.form_submit_button("登 录")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if submit:
                        if not username or not password:
                            st.markdown("<div class='auth-message error'>请填写所有字段</div>", unsafe_allow_html=True)
                        else:
                            success, message, user_info = login_user(username, password)
                            if success:
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_id = user_info['id']  # 添加用户ID到session_state
                                st.session_state.page = "rag"
                                st.markdown(f"<div class='auth-message success'>{message}</div>", unsafe_allow_html=True)
                                st.rerun()
                            else:
                                st.markdown(f"<div class='auth-message error'>{message}</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='auth-divider'>或</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='auth-links'>还没有账号？ <a href='#' id='register-link'>创建新账号</a></div>", unsafe_allow_html=True)
                
                # JavaScript代码处理链接点击
                st.markdown("""
                <script>
                document.getElementById('register-link').addEventListener('click', function(e) {
                    e.preventDefault();
                    // 使用Streamlit的API触发按钮点击
                    document.querySelector('button[kind="secondary"]').click();
                });
                </script>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 隐藏按钮，用于JavaScript触发
                if st.button("创建新账号", key="hidden_register", help="点击注册新账号"):
                    st.session_state.page = "register"
                    st.rerun()
    
    # 注册页面
    elif st.session_state.page == "register":
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
                st.markdown("<h2 class='auth-title'>用户注册</h2>", unsafe_allow_html=True)
                
                # 初始化session状态
                if 'verification_sent' not in st.session_state:
                    st.session_state.verification_sent = False
                if 'register_email' not in st.session_state:
                    st.session_state.register_email = ""
                if 'register_username' not in st.session_state:
                    st.session_state.register_username = ""
                if 'register_password' not in st.session_state:
                    st.session_state.register_password = ""
                
                # 邮箱配置表单（仅在开发环境中显示，实际部署时应预先配置）
                with st.expander("邮箱配置（仅开发环境）"):
                    with st.form("email_config_form"):
                        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>📧</i>", unsafe_allow_html=True)
                        sender_email = st.text_input("发件人邮箱", placeholder="请输入发件人邮箱")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🔑</i>", unsafe_allow_html=True)
                        sender_password = st.text_input("邮箱授权码", type="password", placeholder="请输入邮箱授权码")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🖥️</i>", unsafe_allow_html=True)
                        smtp_server = st.text_input("SMTP服务器", value="smtp.qq.com", placeholder="请输入SMTP服务器")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🔢</i>", unsafe_allow_html=True)
                        smtp_port = st.number_input("SMTP端口", value=587)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        config_submit = st.form_submit_button("保存配置")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        if config_submit:
                            if not sender_email or not sender_password:
                                st.markdown("<div class='auth-message error'>请填写发件人邮箱和授权码</div>", unsafe_allow_html=True)
                            else:
                                set_email_config(sender_email, sender_password, smtp_server, int(smtp_port))
                                st.markdown("<div class='auth-message success'>邮箱配置已保存</div>", unsafe_allow_html=True)
                
                # 注册第一步：填写基本信息
                if not st.session_state.verification_sent:
                    with st.form("register_form_step1"):
                        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>👤</i>", unsafe_allow_html=True)
                        username = st.text_input("用户名", placeholder="请输入用户名 (至少3个字符)")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>📧</i>", unsafe_allow_html=True)
                        email = st.text_input("电子邮箱", placeholder="请输入有效的电子邮箱")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🔒</i>", unsafe_allow_html=True)
                        password = st.text_input("密码", type="password", placeholder="至少8位，包含大小写字母和数字")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🔐</i>", unsafe_allow_html=True)
                        confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        submit_step1 = st.form_submit_button("发送验证码")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        if submit_step1:
                            if not username or not email or not password or not confirm_password:
                                st.markdown("<div class='auth-message error'>请填写所有字段</div>", unsafe_allow_html=True)
                            elif len(username) < 3:
                                st.markdown("<div class='auth-message error'>用户名至少需要3个字符</div>", unsafe_allow_html=True)
                            elif not is_valid_email(email):
                                st.markdown("<div class='auth-message error'>请输入有效的电子邮箱</div>", unsafe_allow_html=True)
                            elif password != confirm_password:
                                st.markdown("<div class='auth-message error'>两次输入的密码不一致</div>", unsafe_allow_html=True)
                            else:
                                is_strong, msg = is_strong_password(password)
                                if not is_strong:
                                    st.markdown(f"<div class='auth-message error'>{msg}</div>", unsafe_allow_html=True)
                                else:
                                    # 检查用户名和邮箱是否已存在
                                    conn = mysql.connector.connect(**db_config)
                                    cursor = conn.cursor()
                                    
                                    # 检查用户名
                                    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                                    if cursor.fetchone():
                                        st.markdown("<div class='auth-message error'>用户名已存在</div>", unsafe_allow_html=True)
                                    else:
                                        # 检查邮箱
                                        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                                        if cursor.fetchone():
                                            st.markdown("<div class='auth-message error'>邮箱已被注册</div>", unsafe_allow_html=True)
                                        else:
                                            # 生成验证码并发送邮件
                                            verification_code = generate_verification_code()
                                            success, message = send_verification_email(email, verification_code)
                                            
                                            if success:
                                                # 存储验证码
                                                store_verification_code(email, verification_code)
                                                # 保存用户信息到session_state
                                                st.session_state.register_username = username
                                                st.session_state.register_email = email
                                                st.session_state.register_password = password
                                                st.session_state.verification_sent = True
                                                st.markdown(f"<div class='auth-message success'>{message}</div>", unsafe_allow_html=True)
                                                st.rerun()
                                            else:
                                                st.markdown(f"<div class='auth-message error'>{message}</div>", unsafe_allow_html=True)
                                    
                                    cursor.close()
                                    conn.close()
                
                # 注册第二步：验证邮箱
                else:
                    st.markdown(f"<div class='auth-message info'>验证码已发送到邮箱: {st.session_state.register_email}</div>", unsafe_allow_html=True)
                    with st.form("register_form_step2"):
                        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='auth-input-container'>", unsafe_allow_html=True)
                        st.markdown("<i class='auth-input-icon'>🔢</i>", unsafe_allow_html=True)
                        verification_code = st.text_input("验证码", placeholder="请输入收到的验证码", max_chars=6, key="verification_code_input", help="请查看您的邮箱获取验证码", css_classes=["verification-code-input"])
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        submit_step2 = st.form_submit_button("完成注册")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        if submit_step2:
                            if not verification_code:
                                st.markdown("<div class='auth-message error'>请输入验证码</div>", unsafe_allow_html=True)
                            else:
                                # 验证验证码
                                success, message = verify_code(st.session_state.register_email, verification_code)
                                
                                if success:
                                    # 注册用户
                                    reg_success, reg_message = register_user(
                                        st.session_state.register_username, 
                                        st.session_state.register_password, 
                                        st.session_state.register_email
                                    )
                                    
                                    if reg_success:
                                        st.markdown("<div class='auth-message success'>注册成功！邮箱验证完成。</div>", unsafe_allow_html=True)
                                        # 重置session状态
                                        st.session_state.verification_sent = False
                                        st.session_state.register_email = ""
                                        st.session_state.register_username = ""
                                        st.session_state.register_password = ""
                                        # 跳转到登录页面
                                        st.session_state.page = "login"
                                        st.rerun()
                                    else:
                                        st.markdown(f"<div class='auth-message error'>{reg_message}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div class='auth-message error'>{message}</div>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("重新发送验证码", use_container_width=True):
                            verification_code = generate_verification_code()
                            success, message = send_verification_email(st.session_state.register_email, verification_code)
                            
                            if success:
                                store_verification_code(st.session_state.register_email, verification_code)
                                st.markdown(f"<div class='auth-message success'>{message}</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='auth-message error'>{message}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("返回修改信息", use_container_width=True):
                            st.session_state.verification_sent = False
                            st.rerun()
                
                st.markdown("<div class='auth-divider'>或</div>", unsafe_allow_html=True)
                st.markdown("<div class='auth-links'>已有账号？ <a href='#' id='login-link'>返回登录</a></div>", unsafe_allow_html=True)
                
                # JavaScript代码处理链接点击
                st.markdown("""
                <script>
                document.getElementById('login-link').addEventListener('click', function(e) {
                    e.preventDefault();
                    // 使用Streamlit的API触发按钮点击
                    document.querySelector('button[kind="secondary"]').click();
                });
                </script>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 隐藏按钮，用于JavaScript触发
                if st.button("返回登录", key="hidden_login", help="返回登录页面"):
                    st.session_state.page = "login"
                    st.rerun()

# 登录后显示RAG系统或重定向到RAG系统
else:
    if st.session_state.page == "rag":
        st.header(f"欢迎使用RAG文档检索系统，{st.session_state.username}！")
        st.info("请点击下方按钮进入RAG系统")
        
        if st.button("进入RAG文档检索系统", use_container_width=True):
            # 重定向到web_app.py
            st.markdown(f'''
            <meta http-equiv="refresh" content="0;url=http://localhost:8501/web_app">
            ''', unsafe_allow_html=True)
            st.stop()
