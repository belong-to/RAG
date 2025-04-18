import pandas as pd
import streamlit as st

def init_chat_history():
    '''
    初始化聊天记录
    '''
    if "messages" not in st.session_state:
        st.session_state.messages = []

def add_user_message(message):
    '''
    添加用户消息到聊天记录
    :param message: 用户消息内容
    '''
    st.session_state.messages.append({"role": "user", "content": message})

def add_ai_message(message):
    '''
    添加AI消息到聊天记录
    :param message: AI消息内容
    '''
    st.session_state.messages.append({"role": "AI", "content": message})

def clear_chat_history():
    '''
    清空对话记录
    '''
    if 'messages' in st.session_state:
        del st.session_state['messages']
        st.session_state.messages = []

def display_chat_history():
    '''
    显示聊天记录
    '''
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message(message["role"], avatar='☺️'):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"], avatar='🤖'):
                st.markdown(message["content"])

def convert_chat_to_csv():
    '''
    将对话记录转换为CSV格式
    :return: CSV格式的对话记录
    '''
    if not st.session_state.messages:
        return ""
        
    df = pd.DataFrame(st.session_state.messages)
    df = df.applymap(lambda x: str(x).replace('\n', '').replace(',', '，'))
    return df.to_csv(index=False, encoding='utf-8', mode='w', sep=',')

def update_last_ai_message(message):
    '''
    更新最后一条AI消息
    :param message: 新的AI消息内容
    '''
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "AI":
        st.session_state.messages[-1]["content"] = message
    else:
        add_ai_message(message)