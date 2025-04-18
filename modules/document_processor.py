import os
import re
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

def save_uploaded_file(uploaded_file):
    '''
    保存上传的文件到本地
    :param uploaded_file: Streamlit上传的文件对象
    :return: 保存的文件路径
    '''
    if uploaded_file is None:
        return None
        
    with st.spinner('正在读取文件 ...'):
        # streamlit框架读取文件对象
        bytes_data = uploaded_file.read()

        # 文件写出
        file_path = os.path.join('./', uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(bytes_data)
        
        return file_path

def clear_files(filenames):
    '''
    清理本地保存的文件
    :param filenames: 文件名列表
    '''
    for filename in filenames:
        try:
            delfile = os.path.join('./', filename)
            os.remove(delfile)
        except Exception as e:
            st.warning(f"删除文件 {filename} 失败: {e}")