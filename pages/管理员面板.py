import streamlit as st
import mysql.connector
import pandas as pd
import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.user_manager import db_config, hash_password, promote_to_admin, get_all_admins

# 页面设置
st.set_page_config(page_title='RAG系统 - 管理员控制台', page_icon=':lock:', layout='wide')

# 初始化session_state
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = ""
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# 管理员登录函数
def admin_login(username, password):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询管理员表
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()
        
        if not admin:
            return False, "管理员账户不存在"
        
        # 验证密码
        hashed_password = hash_password(password)
        if hashed_password == admin[2]:  # 索引2是密码字段
            return True, "登录成功！"
        else:
            return False, "密码错误"
    except mysql.connector.Error as err:
        return False, f"登录失败: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 获取所有普通用户数据
def get_all_users():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询所有用户
        cursor.execute("SELECT id, username, email, email_verified, created_at FROM users")
        users = cursor.fetchall()
        
        # 转换为DataFrame以便于展示
        if users:
            df = pd.DataFrame(users, columns=['ID', '用户名', '邮箱', '邮箱已验证', '创建时间'])
            return df
        else:
            return pd.DataFrame()
    except mysql.connector.Error as err:
        st.error(f"获取用户数据失败: {err}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 获取用户详细信息
def get_user_details(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # 返回字典格式的结果
        
        # 查询用户详细信息
        cursor.execute("""
        SELECT id, username, email, email_verified, created_at,
               (SELECT COUNT(*) FROM users) as total_users
        FROM users WHERE id = %s
        """, (user_id,))
        user_details = cursor.fetchone()
        
        # 查询用户的聊天记录数量（如果有相关表）
        try:
            cursor.execute("SELECT COUNT(*) as chat_count FROM chat_history WHERE user_id = %s", (user_id,))
            chat_result = cursor.fetchone()
            if chat_result:
                user_details['chat_count'] = chat_result['chat_count']
            else:
                user_details['chat_count'] = 0
        except:
            user_details['chat_count'] = 0  # 如果表不存在或查询出错
        
        return user_details
    except mysql.connector.Error as err:
        st.error(f"获取用户详细信息失败: {err}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 页面标题
st.title('RAG系统 - 管理员控制台')
st.markdown('---')

# 管理员登录页面
if not st.session_state.admin_logged_in:
    st.header("管理员登录")
    with st.form("admin_login_form"):
        username = st.text_input("管理员用户名")
        password = st.text_input("密码", type="password")
        submit = st.form_submit_button("登录")
        
        if submit:
            if not username or not password:
                st.error("请填写所有字段")
            else:
                success, message = admin_login(username, password)
                if success:
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_username = username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

# 管理员控制台
else:
    st.header(f"欢迎，管理员 {st.session_state.admin_username}")
    
    # 侧边栏 - 导航
    with st.sidebar:
        st.header("管理员功能")
        st.write(f"当前登录: {st.session_state.admin_username}")
        
        # 添加导航选项
        nav_option = st.radio(
            "导航",
            ["用户管理", "管理员管理"],
            index=0
        )
        
        if st.button("退出登录", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.admin_username = ""
            st.rerun()
    
    # 根据导航选项显示不同内容
    if nav_option == "用户管理":
        # 主页面 - 用户数据展示
        st.subheader("用户数据管理")
        
        # 获取并显示所有用户数据
        user_data = get_all_users()
        if not user_data.empty:
            # 添加查看详情按钮列
            user_data['操作'] = None
            st.dataframe(user_data, use_container_width=True)
            
            # 显示用户统计信息
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总用户数", len(user_data))
            with col2:
                verified_users = user_data['邮箱已验证'].sum() if '邮箱已验证' in user_data.columns else 0
                st.metric("已验证邮箱用户数", verified_users)
            
            # 用户详情查看区域
            st.subheader("查看用户详细信息")
            user_id = st.selectbox("选择用户ID", user_data['ID'].tolist(), format_func=lambda x: f"ID: {x} - {user_data[user_data['ID']==x]['用户名'].values[0]}")
            
            if st.button("查看详情", key="view_details"):
                st.session_state.selected_user = user_id
            
            # 显示选中用户的详细信息
            if st.session_state.selected_user:
                user_details = get_user_details(st.session_state.selected_user)
                if user_details:
                    st.subheader(f"用户 {user_details['username']} 的详细信息")
                    
                    # 使用列布局展示详细信息
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info("基本信息")
                        st.write(f"**用户ID:** {user_details['id']}")
                        st.write(f"**用户名:** {user_details['username']}")
                        st.write(f"**邮箱:** {user_details['email']}")
                        st.write(f"**邮箱验证状态:** {'已验证' if user_details['email_verified'] else '未验证'}")
                    
                    with col2:
                        st.info("使用统计")
                        st.write(f"**注册时间:** {user_details['created_at']}")
                        st.write(f"**聊天记录数:** {user_details.get('chat_count', '未知')}")
                        
                    # 添加用户操作按钮
                    st.subheader("用户操作")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("重置用户密码", key="reset_pwd"):
                            st.warning("此功能尚未实现")
                    with col2:
                        if st.button("提升为管理员", key="promote_user"):
                            success, message = promote_to_admin(user_details['username'], st.session_state.admin_username)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
        else:
            st.info("暂无用户数据")
    
    elif nav_option == "管理员管理":
        # 添加提升用户为管理员的功能
        st.subheader("提升用户为管理员")
        with st.form("promote_admin_form"):
            username_to_promote = st.text_input("输入要提升为管理员的用户名")
            promote_submit = st.form_submit_button("提升为管理员")
            
            if promote_submit:
                if not username_to_promote:
                    st.error("请输入用户名")
                else:
                    success, message = promote_to_admin(username_to_promote, st.session_state.admin_username)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # 显示当前管理员列表
        st.subheader("管理员列表")
        admins = get_all_admins()
        if admins:
            admin_df = pd.DataFrame(admins, columns=['ID', '用户名', '邮箱', '角色', '创建时间'])
            st.dataframe(admin_df, use_container_width=True)
        else:
            st.info("暂无管理员数据")