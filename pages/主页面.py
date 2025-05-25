import os
import pandas as pd
import streamlit as st
from langchain_community.vectorstores import Qdrant
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import re
import warnings

# 导入文件管理模块
from modules.file_manager import get_all_uploaded_files, save_uploaded_files, clear_uploaded_files
# 导入增强检索模块
from modules.enhanced_retrieval import enhanced_retrieval
# 导入模型接口
from modules.model_interface import get_llm_model, get_embedding_model, load_api_keys
# 导入搜索引擎模块
from modules.search_engine import get_search_engine, format_search_results

warnings.filterwarnings("ignore")

#-----------------------模型准备------------------------

# 读取API Key配置文件
api_keys = load_api_keys()

# 大模型配置
llm1 = get_llm_model('DeepSeek', api_keys)
llm2 = get_llm_model('阿里通义千问', api_keys)

# Embedding配置
embedding1 = get_embedding_model('DeepSeek', api_keys)
embedding2 = get_embedding_model('阿里通义千问', api_keys)

# -----------------------数据读取、切分、向量化函数------------------------

def load_document(file):
    '''
    导入文档，支持 PDF, DOCX and TXT 文件
    :param file: 文件路径
    :return: 文本数据
    '''
    name, extension = os.path.splitext(file)
    if extension == '.pdf':
        loader = PyPDFLoader(file)
        documents = loader.load()
    elif extension == '.docx':
        loader = Docx2txtLoader(file)
        documents = loader.load()
    elif extension == '.txt':
        try:
            loader = TextLoader(file, encoding='utf8')
            documents = loader.load()
        except:
            loader = TextLoader(file, encoding='gbk')
            documents = loader.load()
    else:
        st.error('不支持的文件格式，仅支持PDF、DOCX、TXT文件')
        documents = ''
    # 文档预处理
    if documents and len(documents) > 0:
        documents[0].page_content = re.sub(r'\n{2,}', '\n', documents[0].page_content)
        documents[0].page_content = re.sub(r'\t', '', documents[0].page_content)
    return documents


def create_embeddings(documents, embedding):
    '''
    文档向量化和存储
    :param documents: 切分好的文档
    :param embedding: 向量化模型
    :return: 向量化存储的对象
    '''
    vectorstore = Qdrant.from_documents(
        documents=documents,
        embedding=embedding,
        location=':memory:',
        collection_name='my_documents')
    return vectorstore


def chunk_data(data, file_name='a.txt', chunk_size=256, chunk_overlap=100):
    '''
    文档切分
    :param data: 待切分的文档
    :param file_name: 文件名
    :param chunk_size: 切块大小
    :param chunk_overlap: 切块重叠大小
    :return: 切分后的文档对象
    '''
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(data)
    file_name = file_name.split('.')[0] # 去除文件名后缀
    for i in chunks: # 给每个分块添加对于的来源文件名，便于检索更精确
        i.page_content = file_name+'。'+i.page_content
    return chunks


# 清空对话记录
def clear_chat_history():
    '''
    清空对话记录
    :return:
    '''
    if 'messages' in st.session_state:
        del st.session_state['messages']

def clear_embedding():
    '''
    清空知识库和文档
    :return:
    '''
    for i in st.session_state.filenames: # 删除保存的文件
        try:
            delfile = os.path.join('./uploads', i)
            os.remove(delfile)
        except:
            pass
    st.session_state.vs = [] # 清空向量
    st.session_state.filenames = [] # 清空保存的文件名
    st.info('知识库已清空，可以新增知识库后继续。')
    global file_name
    try:
        del file_name # 删除文件名变量
    except:
        pass

def convert_df():
    '''
    将对话记录转换为csv文件
    :return:
    '''
    df = pd.DataFrame(st.session_state.messages)
    df = df.applymap(lambda x: str(x).replace('\n', '').replace(',', '，'))
    return df.to_csv(index=False, encoding='utf-8', mode='w', sep=',')

# -------------------------主页面设置------------------------

st.set_page_config(page_title='增强型RAG文档检索系统', page_icon=':robot:', layout='wide')

# 加载自定义CSS
try:
    # 加载增强样式
    css_path = os.path.join(os.path.dirname(__file__), 'style_enhanced.css')
    with open(css_path, encoding='utf-8') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    
    # 加载新的增强UI样式
    enhanced_css_path = os.path.join(os.path.dirname(__file__), 'enhanced_ui.css')
    with open(enhanced_css_path, encoding='utf-8') as f:
        enhanced_css_content = f.read()
        st.markdown(f'<style>{enhanced_css_content}</style>', unsafe_allow_html=True)
    
    # 加载动画样式
    animations_css_path = os.path.join(os.path.dirname(__file__), 'animations.css')
    with open(animations_css_path, encoding='utf-8') as f:
        animations_css_content = f.read()
        st.markdown(f'<style>{animations_css_content}</style>', unsafe_allow_html=True)
except UnicodeDecodeError:
    css_path = os.path.join(os.path.dirname(__file__), 'style_enhanced.css')
    with open(css_path, encoding='latin-1') as f:
        css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

# 加载JavaScript文件
try:
    # 加载主题切换JavaScript
    js_path = os.path.join(os.path.dirname(__file__), 'theme_switcher.js')
    with open(js_path, encoding='utf-8') as f:
        js_content = f.read()
        st.markdown(f'<script>{js_content}</script>', unsafe_allow_html=True)
    
    # 加载动画JavaScript
    animations_js_path = os.path.join(os.path.dirname(__file__), 'animations.js')
    with open(animations_js_path, encoding='utf-8') as f:
        animations_js_content = f.read()
        st.markdown(f'<script>{animations_js_content}</script>', unsafe_allow_html=True)
    
    # 加载UI增强JavaScript
    ui_enhancer_js_path = os.path.join(os.path.dirname(__file__), 'ui_enhancer.js')
    with open(ui_enhancer_js_path, encoding='utf-8') as f:
        ui_enhancer_js_content = f.read()
        st.markdown(f'<script>{ui_enhancer_js_content}</script>', unsafe_allow_html=True)
except Exception as e:
    st.error(f'加载JavaScript脚本失败: {e}')

# 添加卡片容器类
st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
st.markdown("<h1 class='main-title'>增强型RAG文档检索系统 <span class='emoji-title'>🤖</span></h1>", unsafe_allow_html=True)
st.markdown('<div class="gradient-line"></div>', unsafe_allow_html=True)

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

#  初始化知识库
if "vs" not in st.session_state:
    st.session_state.vs = []

#  初始化导入的文件名
if "filenames" not in st.session_state:
    st.session_state.filenames = []

# 初始化搜索引擎设置
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False

if "search_engine" not in st.session_state:
    st.session_state.search_engine = "Mock"

if st.session_state.filenames == [] and not st.session_state.use_web_search:
    st.warning("您还没有添加知识库或启用网络搜索，模型的回答将基于通用知识。")

# 展示聊天记录
st.markdown("<div class='chat-container glass-effect'>", unsafe_allow_html=True)
if st.session_state.messages:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message(message["role"], avatar='👤'):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"], avatar='🤖'):
                st.markdown(message["content"])
else:
    st.markdown("<div class='empty-chat-message'>请在下方输入您的问题开始对话...</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 关闭卡片容器
st.markdown('</div>', unsafe_allow_html=True)


# ---------------------侧边栏设置-----------------------

# 初始化登录状态
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
if 'username' not in st.session_state:
    st.session_state.username = ""

# 退出登录函数
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "login"  # 确保页面状态被重置
    # 重定向到登录页面
    st.markdown(f'''
    <meta http-equiv="refresh" content="0;url=http://localhost:8501">
    ''', unsafe_allow_html=True)
    st.stop()

# 添加退出登录按钮
st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3>👤 用户操作</h3>", unsafe_allow_html=True)
if st.sidebar.button("退出登录", use_container_width=True):
    logout()

# 文档上传
st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3>📁 上传知识库</h3>", unsafe_allow_html=True)
uploaded_files = st.sidebar.file_uploader('文件上传:', type=['pdf', 'docx', 'txt', 'doc'], accept_multiple_files=True, help="支持PDF、DOCX、TXT文件格式")

if not uploaded_files:
    # 检查uploads文件夹中是否已有文件
    existing_files = get_all_uploaded_files()
    if existing_files:
        st.sidebar.success(f'已有{len(existing_files)}个文件在知识库中，可直接【添加知识库】')
else:
    st.sidebar.warning(f'上传成功！共{len(uploaded_files)}个文件，注意【添加知识库】')

# 分块参数
st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3>⚙️ 参数设置</h3>", unsafe_allow_html=True)
chunk_size = st.sidebar.slider('📄 分块大小', min_value=100, max_value=2048, value=1024, step=50, help="较大的分块大小可能包含更多上下文，但可能降低检索精度")
st.sidebar.caption(f"当前分块大小: {chunk_size} 字符")

# 搜索文档参数
k = st.sidebar.slider('🔍 搜索返回文档数', min_value=1, max_value=100, value=10, step=1, help="增加返回文档数可能提高召回率，但可能降低精确度")
st.sidebar.caption(f"当前返回文档数: {k} 个")

# 模型选择参数
myllm = st.sidebar.selectbox('模型选择', ['阿里通义千问', 'DeepSeek'], help="选择不同的大语言模型可能会影响回答质量和风格")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# 根据选择的模型，添加对应的Embedding模型
if myllm == 'DeepSeek':
    llm = llm1
    embedding = embedding1
elif myllm == '阿里通义千问':
    llm = llm2
    embedding = embedding2
else:
    pass

# 知识库管理参数
st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3>📚 知识库管理</h3>", unsafe_allow_html=True)
add_or_no = st.sidebar.radio('知识库管理', ['合并新增知识库', '仅使用当前知识库'], help="选择是否保留之前的知识库")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# 搜索引擎设置
st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3>🔍 搜索引擎设置</h3>", unsafe_allow_html=True)
st.session_state.use_web_search = st.sidebar.checkbox('启用网络搜索', value=st.session_state.use_web_search, help="启用后可以从互联网获取信息")

if st.session_state.use_web_search:
    st.session_state.search_engine = st.sidebar.selectbox(
        '选择搜索引擎', 
        ['Mock', 'SerpApi', 'Bing'],
        index=['Mock', 'SerpApi', 'Bing'].index(st.session_state.search_engine),
        help="Mock为模拟搜索，SerpApi和Bing需要API密钥"
    )
    
    num_web_results = st.sidebar.slider('网络搜索结果数量', min_value=1, max_value=10, value=3, help="增加结果数量可能提供更多信息，但可能增加处理时间")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # 如果选择了真实搜索引擎，显示API密钥配置
    if st.session_state.search_engine != 'Mock':
        with st.sidebar.expander("搜索引擎API配置"):
            if st.session_state.search_engine == 'SerpApi':
                serpapi_key = st.text_input("SerpApi Key", type="password")
                if serpapi_key:
                    api_keys['serpapi'] = serpapi_key
            elif st.session_state.search_engine == 'Bing':
                bing_key = st.text_input("Bing API Key", type="password")
                if bing_key:
                    api_keys['bing'] = bing_key

# 点击导入文件后，将文件内容写入本地
if uploaded_files:  # if the user browsed files
    with st.spinner('正在读取文件 ...'):
        # 清理文件列表
        if add_or_no == '仅使用当前知识库':
            # 清空之前的文件记录
            st.session_state.filenames = []
            # 清空uploads文件夹中的文件
            clear_uploaded_files(st.session_state.filenames)
            
        # 保存上传的文件
        saved_files = save_uploaded_files(uploaded_files)
        st.session_state.filenames.extend(saved_files)

# ---------------------对话栏对话设置-----------------------

if prompt := st.chat_input('请输入你的问题'):
    # 输入问题
    with st.chat_message('user', avatar='☺️'):
        st.markdown(prompt)
    # 在历史对话中添加用户的问题
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    
    # 调用增强检索函数，获取回答
    with st.spinner('正在检索，请稍后 ...'):
        response = enhanced_retrieval(
            llm=llm, 
            query=prompt, 
            vector_store=st.session_state.vs, 
            search_engine_name=st.session_state.search_engine if st.session_state.use_web_search else None,
            use_web_search=st.session_state.use_web_search,
            k=k,
            num_web_results=num_web_results if st.session_state.use_web_search else 0
        )
    
    # 输出答案
    with st.chat_message('AI', avatar='🤖'):
        st.markdown(response)
    # 在历史对话中添加问题的答案
    st.session_state.messages.append({'role': 'AI', 'content': response})


# ---------------------对话栏清空对话、导入知识库等设置-----------------------
st.markdown("<div class='action-buttons-container'>", unsafe_allow_html=True)
st.markdown("<h3 class='action-title'>操作面板</h3>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    add = st.button('添加知识库 📚', use_container_width=True)

with col2:
    drop_embedding = st.button('清空知识库 🗑️', use_container_width=True)
if drop_embedding:
    clear_embedding()
    st.toast(':red[知识库已清空！]', icon='🤖')

with col3:
    if st.button("清除对话历史 🔄", on_click=clear_chat_history, use_container_width = True):
        st.session_state["messages"] = []
        st.toast(':red[对话历史已清除！]', icon='🤖')

with col4:
    download_button = st.download_button(label="导出对话记录 📥",
                                         data=convert_df(), # 导出函数
                                         file_name='chat_history.csv', # 文件名
                                         mime='text/csv',  # 文件类型
                                         use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# 关闭卡片容器
st.markdown('</div>', unsafe_allow_html=True)
if add:
    with st.spinner("知识库生成中..."):
        # 清空现有知识库（如果选择了仅使用当前知识库）
        if add_or_no == '仅使用当前知识库':
            st.session_state.vs = []
            
        # 获取所有需要处理的文件
        all_files = []
        if st.session_state.filenames:  # 如果有通过上传组件上传的文件
            all_files = [os.path.join('./uploads', file_name) for file_name in st.session_state.filenames]
        else:  # 否则获取uploads文件夹中的所有文件
            all_files = get_all_uploaded_files()
            # 更新文件名列表
            st.session_state.filenames = [os.path.basename(file_path) for file_path in all_files]
            
        # 处理每个文件
        all_chunks = []
        for file_path in all_files:
            # 读取文档
            data = load_document(file_path)
            # 分割数据
            file_name = os.path.basename(file_path)
            chunks = chunk_data(data, file_name=file_name, chunk_size=chunk_size)
            all_chunks.extend(chunks)
            
        # 创建知识库的嵌入向量
        if all_chunks:
            vector_store = create_embeddings(all_chunks, embedding)
            st.toast(':red[知识库添加成功！]', icon='🤖')
            
            # 保存知识库
            if add_or_no == '合并新增知识库' and st.session_state.vs != []:
                st.session_state.vs.add_documents(all_chunks)  # 添加新的文档
            else:
                st.session_state.vs = vector_store
                
            # 添加知识库名称
            files = '；'.join(list(set(st.session_state.filenames)))
            st.success(f'添加成功！已有知识库：{files}')
            if st.session_state.messages == []:
                st.session_state.messages.append({'role': 'AI', 'content': f'已有知识库：{files}'})
            else:
                st.session_state.messages[-1] = {'role': 'AI', 'content': f'已有知识库：{files}'}
            with st.chat_message('AI', avatar='🤖'):
                st.markdown(st.session_state.messages[-1]['content'])