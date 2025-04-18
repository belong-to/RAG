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
DEEPSEEK_API_KEY = "sk-68b772163d5347829592346cb4d7233a"  # DeepSeek API Key
DASHSCOPE_API_KEY = "sk-d01cdfe592b9483ab56cf94172e157db"  # 阿里通义千问 API Key

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