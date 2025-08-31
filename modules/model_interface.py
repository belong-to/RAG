import os
import json
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import Tongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ErnieBotChat
from langchain_community.embeddings import ErnieEmbeddings

# 默认API密钥
DEEPSEEK_API_KEY = ""  # DeepSeek API Key
DASHSCOPE_API_KEY = ""  # 阿里通义千问 API Key

def load_api_keys(config_file=None):
    """
    从配置文件加载API密钥
    :param config_file: 配置文件路径
    :return: API密钥字典
    """
    api_keys = {
        "deepseek": DEEPSEEK_API_KEY,
        "dashscope": DASHSCOPE_API_KEY,
        "ernie": {"client_id": "", "client_secret": ""}
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'deepseek' in config:
                    api_keys['deepseek'] = config['deepseek']
                if 'dashscope' in config:
                    api_keys['dashscope'] = config['dashscope']
                if 'ernie' in config:
                    api_keys['ernie']['client_id'] = config['ernie'].get('client_id', '')
                    api_keys['ernie']['client_secret'] = config['ernie'].get('client_secret', '')
        except Exception as e:
            st.warning(f"加载API配置文件失败: {e}")
    
    return api_keys

def get_llm_model(model_name, api_keys=None):
    """
    获取大语言模型
    :param model_name: 模型名称
    :param api_keys: API密钥字典
    :return: LLM模型实例
    """
    if api_keys is None:
        api_keys = load_api_keys()
        
    if model_name == 'DeepSeek':
        return ChatOpenAI(
            api_key=api_keys['deepseek'],
            model_name="deepseek-chat",
            temperature=1,
            base_url="https://api.deepseek.ai/v1"
        )
    elif model_name == '阿里通义千问':
        return Tongyi(
            model_name='qwen-turbo',
            temperature=1, 
            dashscope_api_key=api_keys['dashscope']
        )
    elif model_name == '百度文心':
        if api_keys['ernie']['client_id'] and api_keys['ernie']['client_secret']:
            return ErnieBotChat(
                ernie_client_id=api_keys['ernie']['client_id'],
                ernie_client_secret=api_keys['ernie']['client_secret']
            )
        else:
            st.error("未配置百度文心API密钥")
            return None
    else:
        st.error(f"不支持的模型: {model_name}")
        return None

def get_embedding_model(model_name, api_keys=None):
    """
    获取Embedding模型
    :param model_name: 模型名称
    :param api_keys: API密钥字典
    :return: Embedding模型实例
    """
    if api_keys is None:
        api_keys = load_api_keys()
        
    if model_name == 'DeepSeek':
        return OpenAIEmbeddings(
            api_key=api_keys['deepseek'],
            model="text-embedding-ada-002",
            base_url="https://api.deepseek.ai/v1"
        )
    elif model_name == '阿里通义千问':
        return DashScopeEmbeddings(
            model="text-embedding-v2", 
            dashscope_api_key=api_keys['dashscope']
        )
    elif model_name == '百度文心':
        if api_keys['ernie']['client_id'] and api_keys['ernie']['client_secret']:
            return ErnieEmbeddings(
                ernie_client_id=api_keys['ernie']['client_id'],
                ernie_client_secret=api_keys['ernie']['client_secret']
            )
        else:
            st.error("未配置百度文心API密钥")
            return None
    else:
        st.error(f"不支持的Embedding模型: {model_name}")
        return None

def get_available_models():
    """
    获取可用的模型列表
    :return: 模型名称列表
    """
    return ['DeepSeek', '阿里通义千问', '百度文心']

def get_realtime_info(query):
    """
    获取实时信息，如日期、时间等
    :param query: 用户查询
    :return: 实时信息回答
    """
    import datetime
    import re
    import calendar
    
    # 获取当前日期时间
    now = datetime.datetime.now()
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']
    weekday_name = weekday_names[now.weekday()]
    
    # 日期相关问题模式
    date_patterns = [
        r'今天(是?)(几号|什么日期|日期)',
        r'(现在|当前)(是?)(几号|什么日期|日期)',
        r'今天(是?)(星期几|周几|礼拜几)',
        r'(现在|当前)(是?)(星期几|周几|礼拜几)',
        r'(今天|现在)(是?)(哪一?年|几年)',
        r'(今天|现在)(是?)(哪个?月|几月)',
        r'(今天|现在|当前)(是?)(什么时候|哪天)',
        r'(星期几|周几|礼拜几)'
    ]
    
    # 时间相关问题模式
    time_patterns = [
        r'(现在|当前)(是?)(几点|什么时间|时间)',
        r'(现在|当前)(的?)时间',
        r'几点了'
    ]
    
    # 检查是否是日期相关问题
    for pattern in date_patterns:
        if re.search(pattern, query):
            if '号' in query or '日期' in query:
                return f"今天是{now.year}年{now.month}月{now.day}日"
            elif '星期' in query or '周' in query or '礼拜' in query:
                return f"今天是星期{weekday_name}"
            elif '年' in query:
                return f"现在是{now.year}年"
            elif '月' in query:
                return f"现在是{now.month}月"
            elif '什么时候' in query or '哪天' in query:
                return f"今天是{now.year}年{now.month}月{now.day}日，星期{weekday_name}"
    
    # 检查是否是时间相关问题
    for pattern in time_patterns:
        if re.search(pattern, query):
            return f"现在的时间是{now.hour}点{now.minute}分{now.second}秒"
    
    # 如果是其他实时信息问题，返回完整日期时间
    if '日期' in query and '时间' in query:
        return f"现在是{now.year}年{now.month}月{now.day}日 {now.hour}点{now.minute}分{now.second}秒，星期{weekday_name}"
    
    # 简单的问题匹配
    simple_patterns = {
        '今天': f"今天是{now.year}年{now.month}月{now.day}日，星期{weekday_name}",
        '现在': f"现在是{now.year}年{now.month}月{now.day}日 {now.hour}点{now.minute}分{now.second}秒，星期{weekday_name}",
        '日期': f"今天是{now.year}年{now.month}月{now.day}日",
        '时间': f"现在的时间是{now.hour}点{now.minute}分{now.second}秒",
        '星期': f"今天是星期{weekday_name}",
        '周几': f"今天是星期{weekday_name}"
    }
    
    for key, response in simple_patterns.items():
        if key in query:
            return response
    
    # 不是实时信息问题
    return None
