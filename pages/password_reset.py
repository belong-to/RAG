import streamlit as st
import time
from modules.user_profile import initiate_password_reset, complete_password_reset, is_strong_password
from modules.email_verification_enhanced import has_active_code

# 页面设置
st.set_page_config(page_title='RAG系统 - 密码重置', page_icon=':lock:', layout='centered')

# 加载自定义CSS
try:
    with open('e:/RAG实战/pages/style_enhanced.css', encoding='utf-8') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
except Exception as e:
    st.warning(f"加载样式表失败: {e}")

# 初始化session_state
if 'reset_step' not in st.session_state:
    st.session_state.reset_step = 'email'  # 初始步骤：输入邮箱
if 'reset_email' not in st.session_state:
    st.session_state.reset_email = ""
if 'verification_sent' not in st.session_state:
    st.session_state.verification_sent = False
if 'countdown' not in st.session_state:
    st.session_state.countdown = 0

# 页面标题
st.title("密码重置")

# 切换步骤函数
def change_step(step, email=None):
    st.session_state.reset_step = step
    if email:
        st.session_state.reset_email = email

# 倒计时函数
def start_countdown(seconds=60):
    st.session_state.countdown = seconds
    st.session_state.verification_sent = True

# 根据当前步骤显示不同内容
if st.session_state.reset_step == 'email':
    # 第一步：输入邮箱
    st.subheader("步骤1：输入您的邮箱")
    st.write("我们将向您的邮箱发送验证码，用于重置密码。")
    
    with st.form("email_form"):
        email = st.text_input("邮箱地址", key="email_input")
        submit_email = st.form_submit_button("发送验证码")
        
        if submit_email:
            if not email:
                st.error("请输入邮箱地址")
            else:
                # 检查是否有未过期的验证码
                has_code, remaining_time = has_active_code(email)
                if has_code:
                    st.warning(f"验证码已发送，请查收邮箱。{int(remaining_time/60)}分{remaining_time%60}秒后可重新发送。")
                    st.session_state.reset_email = email
                    st.session_state.verification_sent = True
                    st.session_state.countdown = remaining_time
                    change_step('verify')
                else:
                    # 发送验证码
                    success, message = initiate_password_reset(email)
                    if success:
                        st.success(message)
                        start_countdown()
                        change_step('verify', email)
                    else:
                        st.error(message)

    # 返回登录页面链接
    st.markdown("[返回登录页面](/login_app)")

elif st.session_state.reset_step == 'verify':
    # 第二步：验证码验证
    st.subheader("步骤2：输入验证码")
    st.write(f"验证码已发送至 {st.session_state.reset_email}")
    
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
    
    with st.form("verification_form"):
        verification_code = st.text_input("验证码", key="verification_code_input")
        new_password = st.text_input("新密码", type="password", key="new_password_input")
        confirm_password = st.text_input("确认新密码", type="password", key="confirm_password_input")
        submit_verification = st.form_submit_button("重置密码")
        
        if submit_verification:
            if not verification_code:
                st.error("请输入验证码")
            elif not new_password or not confirm_password:
                st.error("请输入新密码并确认")
            elif new_password != confirm_password:
                st.error("两次输入的密码不一致")
            else:
                # 验证密码强度
                strong_password, password_message = is_strong_password(new_password)
                if not strong_password:
                    st.error(password_message)
                else:
                    # 完成密码重置
                    success, message = complete_password_reset(
                        st.session_state.reset_email, 
                        verification_code, 
                        new_password
                    )
                    if success:
                        st.success(message)
                        change_step('success')
                    else:
                        st.error(message)
    
    # 重新发送验证码按钮
    if not st.session_state.verification_sent:
        if st.button("重新发送验证码"):
            success, message = initiate_password_reset(st.session_state.reset_email)
            if success:
                st.success(message)
                start_countdown()
                st.rerun()
            else:
                st.error(message)
    
    # 返回按钮
    if st.button("返回上一步"):
        change_step('email')

elif st.session_state.reset_step == 'success':
    # 第三步：重置成功
    st.success("密码重置成功！")
    st.write("您的密码已成功重置，请使用新密码登录。")
    
    if st.button("返回登录页面"):
        st.switch_page("login_app.py")

# 页脚
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>RAG文档检索系统 © 2023</div>", unsafe_allow_html=True)