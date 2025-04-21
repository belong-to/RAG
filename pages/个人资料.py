import streamlit as st
import time
import os
from modules.user_profile import get_user_profile, update_user_profile, verify_current_password, update_password, is_strong_password, check_email_verification_status, send_verification_reminder
from modules.email_verification_enhanced import has_active_code, verify_code

# 页面设置
st.set_page_config(page_title='RAG系统 - 个人资料', page_icon=':bust_in_silhouette:', layout='centered')

# 加载自定义CSS
try:
    css_path = os.path.join(os.path.dirname(__file__), 'style_enhanced.css')
    with open(css_path, encoding='utf-8') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
except Exception as e:
    st.warning(f"加载样式表失败: {e}")

# 检查用户是否已登录
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录系统")
    st.markdown("[前往登录页面](/login_app)")
    st.stop()

# 初始化session_state
if 'profile_tab' not in st.session_state:
    st.session_state.profile_tab = "基本信息"  # 默认标签页
if 'verification_sent' not in st.session_state:
    st.session_state.verification_sent = False
if 'countdown' not in st.session_state:
    st.session_state.countdown = 0
if 'user_id' not in st.session_state:
    st.warning("用户ID信息缺失，请重新登录系统")
    st.markdown("[前往登录页面](/login_app)")
    st.stop()

# 页面标题
st.title("个人资料")

# 获取用户资料
user_profile = get_user_profile(st.session_state.user_id)
if not user_profile:
    st.error("获取用户资料失败")
    st.stop()

# 检查邮箱验证状态
email_verified = check_email_verification_status(st.session_state.user_id)

# 标签页
tabs = ["基本信息", "修改密码", "邮箱验证"]
selected_tab = st.radio("选择操作", tabs, horizontal=True, index=tabs.index(st.session_state.profile_tab))
st.session_state.profile_tab = selected_tab

# 倒计时函数
def start_countdown(seconds=60):
    st.session_state.countdown = seconds
    st.session_state.verification_sent = True

# 基本信息标签页
if selected_tab == "基本信息":
    st.subheader("基本信息")
    
    # 显示当前信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**用户名**: {user_profile['username']}")
        st.markdown(f"**邮箱**: {user_profile['email']}")
    with col2:
        st.markdown(f"**角色**: {user_profile['role']}")
        st.markdown(f"**注册时间**: {user_profile['created_at']}")
    
    st.markdown(f"**邮箱验证状态**: {'已验证 ✅' if email_verified else '未验证 ❌'}")
    
    # 编辑表单
    st.subheader("编辑资料")
    with st.form("profile_form"):
        new_username = st.text_input("用户名", value=user_profile['username'])
        submit_profile = st.form_submit_button("更新资料")
        
        if submit_profile:
            if new_username != user_profile['username']:
                # 更新用户名
                success, message = update_user_profile(st.session_state.user_id, {"username": new_username})
                if success:
                    st.success(message)
                    st.session_state.username = new_username  # 更新session中的用户名
                    st.rerun()  # 刷新页面显示新信息
                else:
                    st.error(message)
            else:
                st.info("未检测到资料变更")

# 修改密码标签页
elif selected_tab == "修改密码":
    st.subheader("修改密码")
    
    with st.form("password_form"):
        current_password = st.text_input("当前密码", type="password")
        new_password = st.text_input("新密码", type="password")
        confirm_password = st.text_input("确认新密码", type="password")
        submit_password = st.form_submit_button("更新密码")
        
        if submit_password:
            if not current_password or not new_password or not confirm_password:
                st.error("请填写所有密码字段")
            elif new_password != confirm_password:
                st.error("两次输入的新密码不一致")
            else:
                # 验证当前密码
                if not verify_current_password(st.session_state.user_id, current_password):
                    st.error("当前密码不正确")
                else:
                    # 验证新密码强度
                    strong_password, password_message = is_strong_password(new_password)
                    if not strong_password:
                        st.error(password_message)
                    else:
                        # 更新密码
                        success, message = update_password(st.session_state.user_id, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

# 邮箱验证标签页
elif selected_tab == "邮箱验证":
    st.subheader("邮箱验证")
    
    if email_verified:
        st.success("您的邮箱已验证")
        st.info(f"当前邮箱: {user_profile['email']}")
    else:
        st.warning("您的邮箱尚未验证")
        st.info(f"请验证邮箱: {user_profile['email']}")
        
        # 显示倒计时
        if st.session_state.verification_sent and st.session_state.countdown > 0:
            st.info(f"可在 {int(st.session_state.countdown/60)}分{st.session_state.countdown%60}秒 后重新发送验证码")
            # 更新倒计时
            if 'last_update_time' not in st.session_state:
                st.session_state.last_update_time = time.time()
            
            current_time = time.time()
            elapsed = current_time - st.session_state.last_update_time
            if elapsed >= 1:
                st.session_state.countdown -= int(elapsed)
                st.session_state.last_update_time = current_time
                if st.session_state.countdown <= 0:
                    st.session_state.verification_sent = False
                    st.rerun()
        
        # 检查是否有未过期的验证码
        has_code, remaining_time = has_active_code(user_profile['email'])
        if has_code and not st.session_state.verification_sent:
            st.info(f"验证码已发送，请查收邮箱。{int(remaining_time/60)}分{remaining_time%60}秒后可重新发送。")
            st.session_state.verification_sent = True
            st.session_state.countdown = remaining_time
        
        # 验证码表单
        with st.form("verification_form"):
            verification_code = st.text_input("验证码")
            submit_verification = st.form_submit_button("验证邮箱")
            
            if submit_verification:
                if not verification_code:
                    st.error("请输入验证码")
                else:
                    # 验证验证码
                    success, message = verify_code(user_profile['email'], verification_code)
                    if success:
                        # 更新邮箱验证状态
                        from modules.user_profile import update_email_verification_status
                        update_success, update_message = update_email_verification_status(st.session_state.user_id, True)
                        if update_success:
                            st.success("邮箱验证成功！")
                            st.rerun()  # 刷新页面显示新状态
                        else:
                            st.error(f"更新验证状态失败: {update_message}")
                    else:
                        st.error(message)
        
        # 发送验证码按钮
        if not st.session_state.verification_sent and not has_code:
            if st.button("发送验证码"):
                success, message = send_verification_reminder(st.session_state.user_id)
                if success:
                    st.success(message)
                    start_countdown()
                    st.rerun()
                else:
                    st.error(message)

# 返回按钮
st.markdown("---")
if st.button("返回主页"):
    st.switch_page("pages/主页面.py")

# 页脚
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>RAG文档检索系统 © 2023</div>", unsafe_allow_html=True)