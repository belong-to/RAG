import os
import re
import streamlit as st
import threading
import queue
import time
import logging
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('document_processor')

class AsyncDocumentProcessor:
    """异步文档处理器，支持大文件处理和进度跟踪"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式确保只有一个处理器实例"""
        if cls._instance is None:
            cls._instance = super(AsyncDocumentProcessor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化异步文档处理器"""
        if self._initialized:
            return
            
        self.processing_queue = queue.Queue()
        self.results = {}
        self.processing_status = {}
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._initialized = True
        self._start_worker()
        logger.info("异步文档处理器初始化完成")
    
    def _start_worker(self):
        """启动工作线程处理队列中的任务"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._process_queue)
            self._worker_thread.daemon = True
            self._worker_thread.start()
            logger.info("文档处理工作线程已启动")
    
    def _process_queue(self):
        """处理队列中的文档任务"""
        while not self._stop_event.is_set():
            try:
                if not self.processing_queue.empty():
                    task_id, file_path, chunk_size, chunk_overlap = self.processing_queue.get(block=False)
                    self.processing_status[task_id] = {
                        'status': 'processing',
                        'progress': 0,
                        'message': '正在处理文档...',
                        'start_time': time.time()
                    }
                    
                    try:
                        # 加载文档
                        self.processing_status[task_id]['message'] = '正在加载文档...'
                        self.processing_status[task_id]['progress'] = 10
                        documents = self._load_document(file_path)
                        
                        # 文档切分
                        self.processing_status[task_id]['message'] = '正在切分文档...'
                        self.processing_status[task_id]['progress'] = 50
                        chunks = self._chunk_data(documents, file_path, chunk_size, chunk_overlap)
                        
                        # 保存结果
                        self.results[task_id] = chunks
                        self.processing_status[task_id] = {
                            'status': 'completed',
                            'progress': 100,
                            'message': '文档处理完成',
                            'end_time': time.time(),
                            'duration': time.time() - self.processing_status[task_id]['start_time']
                        }
                        logger.info(f"文档处理完成: {file_path}, 任务ID: {task_id}")
                    except Exception as e:
                        self.processing_status[task_id] = {
                            'status': 'failed',
                            'progress': 0,
                            'message': f'处理失败: {str(e)}',
                            'error': str(e),
                            'end_time': time.time()
                        }
                        logger.error(f"文档处理失败: {file_path}, 任务ID: {task_id}, 错误: {e}")
                    
                    self.processing_queue.task_done()
                else:
                    # 队列为空，等待新任务
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"处理队列时发生错误: {e}")
                time.sleep(1)
    
    def process_document(self, file_path, chunk_size=256, chunk_overlap=100):
        """异步处理文档
        
        Args:
            file_path (str): 文件路径
            chunk_size (int): 切块大小
            chunk_overlap (int): 切块重叠大小
            
        Returns:
            str: 任务ID
        """
        task_id = f"task_{int(time.time())}_{os.path.basename(file_path)}"
        self.processing_queue.put((task_id, file_path, chunk_size, chunk_overlap))
        self.processing_status[task_id] = {
            'status': 'queued',
            'progress': 0,
            'message': '等待处理...',
            'file_path': file_path,
            'queue_time': time.time()
        }
        logger.info(f"文档已加入处理队列: {file_path}, 任务ID: {task_id}")
        return task_id
    
    def get_task_status(self, task_id):
        """获取任务处理状态
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            dict: 任务状态信息
        """
        return self.processing_status.get(task_id, {'status': 'not_found', 'message': '任务不存在'})
    
    def get_result(self, task_id):
        """获取处理结果
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            list: 处理后的文档块
        """
        return self.results.get(task_id)
    
    def _load_document(self, file_path):
        """加载文档
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            list: 文档对象列表
        """
        name, extension = os.path.splitext(file_path)
        if extension == '.pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif extension == '.docx':
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
        elif extension == '.txt':
            try:
                loader = TextLoader(file_path, encoding='utf8')
                documents = loader.load()
            except:
                loader = TextLoader(file_path, encoding='gbk')
                documents = loader.load()
        else:
            raise ValueError(f"不支持的文件格式: {extension}，仅支持PDF、DOCX、TXT文件")
        
        # 文档预处理
        if documents and len(documents) > 0:
            documents[0].page_content = re.sub(r'\n{2,}', '\n', documents[0].page_content)
            documents[0].page_content = re.sub(r'\t', '', documents[0].page_content)
        
        return documents
    
    def _chunk_data(self, data, file_path, chunk_size=256, chunk_overlap=100):
        """文档切分
        
        Args:
            data (list): 待切分的文档
            file_path (str): 文件路径
            chunk_size (int): 切块大小
            chunk_overlap (int): 切块重叠大小
            
        Returns:
            list: 切分后的文档对象
        """
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = text_splitter.split_documents(data)
        file_name = os.path.basename(file_path).split('.')[0]  # 去除文件名后缀
        for i in chunks:  # 给每个分块添加对应的来源文件名，便于检索更精确
            i.page_content = file_name + '。' + i.page_content
        return chunks
    
    def stop(self):
        """停止处理器"""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2)
        logger.info("异步文档处理器已停止")

# 全局异步文档处理器实例
document_processor = AsyncDocumentProcessor()

# 兼容原有API的函数
def load_document(file_path):
    """同步加载文档（兼容原有API）
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        list: 文档对象列表
    """
    return document_processor._load_document(file_path)

def chunk_data(data, file_name='a.txt', chunk_size=256, chunk_overlap=100):
    """同步文档切分（兼容原有API）
    
    Args:
        data (list): 待切分的文档
        file_name (str): 文件名
        chunk_size (int): 切块大小
        chunk_overlap (int): 切块重叠大小
        
    Returns:
        list: 切分后的文档对象
    """
    return document_processor._chunk_data(data, file_name, chunk_size, chunk_overlap)

def save_uploaded_file(uploaded_file):
    """保存上传的文件到本地
    
    Args:
        uploaded_file: Streamlit上传的文件对象
        
    Returns:
        str: 保存的文件路径
    """
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
    """清理本地保存的文件
    
    Args:
        filenames (list): 文件名列表
    """
    for filename in filenames:
        try:
            delfile = os.path.join('./', filename)
            os.remove(delfile)
        except Exception as e:
            logger.warning(f"删除文件 {filename} 失败: {e}")
            st.warning(f"删除文件 {filename} 失败: {e}")

# 异步处理文档的便捷函数
def process_document_async(file_path, chunk_size=256, chunk_overlap=100):
    """异步处理文档的便捷函数
    
    Args:
        file_path (str): 文件路径
        chunk_size (int): 切块大小
        chunk_overlap (int): 切块重叠大小
        
    Returns:
        str: 任务ID
    """
    return document_processor.process_document(file_path, chunk_size, chunk_overlap)

def get_processing_status(task_id):
    """获取文档处理状态的便捷函数
    
    Args:
        task_id (str): 任务ID
        
    Returns:
        dict: 任务状态信息
    """
    return document_processor.get_task_status(task_id)

def get_processed_document(task_id):
    """获取处理结果的便捷函数
    
    Args:
        task_id (str): 任务ID
        
    Returns:
        list: 处理后的文档块
    """
    return document_processor.get_result(task_id)