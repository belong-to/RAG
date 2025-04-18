import os
import logging
import streamlit as st
from langchain_community.vectorstores import Qdrant
from langchain_community.document_transformers import LongContextReorder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vector_store')

class EnhancedVectorStore:
    """增强的向量存储管理类"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式确保只有一个向量存储实例"""
        if cls._instance is None:
            cls._instance = super(EnhancedVectorStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化向量存储管理器"""
        if self._initialized:
            return
            
        self.vector_stores = {}
        self.default_store_name = 'default'
        self._initialized = True
        logger.info("向量存储管理器初始化完成")
    
    def create_vector_store(self, documents, embedding, store_name=None):
        """创建向量存储
        
        Args:
            documents (list): 文档列表
            embedding: 向量化模型
            store_name (str): 存储名称，默认为None使用默认名称
            
        Returns:
            vectorstore: 向量存储对象
        """
        store_name = store_name or self.default_store_name
        try:
            vectorstore = Qdrant.from_documents(
                documents=documents,
                embedding=embedding,
                location=':memory:',
                collection_name=f'collection_{store_name}'
            )
            self.vector_stores[store_name] = vectorstore
            logger.info(f"向量存储 '{store_name}' 创建成功，包含 {len(documents)} 个文档")
            return vectorstore
        except Exception as e:
            logger.error(f"创建向量存储失败: {e}")
            raise
    
    def create_vector_store_from_files(self, file_paths, embedding, document_loader, chunk_function, store_name=None):
        """从多个文件创建向量存储
        
        Args:
            file_paths (list): 文件路径列表
            embedding: 向量化模型
            document_loader: 文档加载函数，接受文件路径参数
            chunk_function: 文档切分函数，接受文档和文件名参数
            store_name (str): 存储名称，默认为None使用默认名称
            
        Returns:
            vectorstore: 向量存储对象
            processed_files (list): 成功处理的文件列表
        """
        store_name = store_name or self.default_store_name
        all_chunks = []
        processed_files = []
        
        try:
            for file_path in file_paths:
                try:
                    # 读取文档
                    documents = document_loader(file_path)
                    if not documents:
                        logger.warning(f"文件 '{file_path}' 加载失败或为空")
                        continue
                        
                    # 分割数据
                    file_name = os.path.basename(file_path)
                    chunks = chunk_function(documents, file_name=file_name)
                    all_chunks.extend(chunks)
                    processed_files.append(file_name)
                    logger.info(f"文件 '{file_name}' 处理成功，生成 {len(chunks)} 个文档块")
                except Exception as e:
                    logger.error(f"处理文件 '{file_path}' 时发生错误: {e}")
            
            # 创建向量存储
            if all_chunks:
                vectorstore = self.create_vector_store(all_chunks, embedding, store_name)
                return vectorstore, processed_files
            else:
                logger.warning("没有成功处理任何文件，无法创建向量存储")
                return None, processed_files
        except Exception as e:
            logger.error(f"批量创建向量存储失败: {e}")
            return None, processed_files
    
    def get_vector_store(self, store_name=None):
        """获取向量存储
        
        Args:
            store_name (str): 存储名称，默认为None使用默认名称
            
        Returns:
            vectorstore: 向量存储对象
        """
        store_name = store_name or self.default_store_name
        return self.vector_stores.get(store_name)
    
    def add_documents(self, documents, store_name=None):
        """向现有向量存储添加文档
        
        Args:
            documents (list): 文档列表
            store_name (str): 存储名称，默认为None使用默认名称
            
        Returns:
            bool: 是否添加成功
        """
        store_name = store_name or self.default_store_name
        vector_store = self.get_vector_store(store_name)
        
        if not vector_store:
            logger.warning(f"向量存储 '{store_name}' 不存在，无法添加文档")
            return False
            
        try:
            vector_store.add_documents(documents)
            logger.info(f"向量存储 '{store_name}' 添加了 {len(documents)} 个文档")
            return True
        except Exception as e:
            logger.error(f"向向量存储添加文档失败: {e}")
            return False
    
    def clear_vector_store(self, store_name=None):
        """清空向量存储
        
        Args:
            store_name (str): 存储名称，默认为None使用默认名称
            
        Returns:
            bool: 是否清空成功
        """
        store_name = store_name or self.default_store_name
        if store_name in self.vector_stores:
            del self.vector_stores[store_name]
            logger.info(f"向量存储 '{store_name}' 已清空")
            return True
        return False
    
    def clear_all_vector_stores(self):
        """清空所有向量存储"""
        self.vector_stores.clear()
        logger.info("所有向量存储已清空")

# 全局向量存储管理器实例
vector_store_manager = EnhancedVectorStore()

# 格式化文档函数
def format_docs(docs):
    """将返回的文档page_content的内容拼接为字符串，减少其他信息干扰
    
    Args:
        docs: 文档对象
        
    Returns:
        str: 拼接后的字符串
    """
    reordering = LongContextReorder()  # 实例化对象
    reordered_docs = reordering.transform_documents(docs)  # 文档重排
    # 文档重排后，将内容拼接为字符串输出
    return "\n\n".join([doc.page_content for doc in reordered_docs])

# 问答函数
def ask_and_get_answer(llm, question, vector_store=None, k=3, store_name=None):
    """增强的问答函数
    
    Args:
        llm: 大模型
        question (str): 问题
        vector_store: 向量存储对象，如果为None则使用管理器中的存储
        k (int): 相似度前k个文档
        store_name (str): 存储名称，默认为None使用默认名称
        
    Returns:
        str: 答案
    """
    if vector_store is None:
        vector_store = vector_store_manager.get_vector_store(store_name)
    
    if vector_store:  # 若有知识库，则根据知识库回答问题
        try:
            # 配置检索器
            if k > 3:
                retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': k})
            else:
                retriever = vector_store.as_retriever(search_type='similarity')
                
            # 使用多查询检索器增强检索效果
            retriever_from_llm = MultiQueryRetriever.from_llm(
                retriever=retriever, llm=llm
            )

            # 设置提示模板
            template = '''根据以下上下文回答问题，只使用提供的信息：
            {context}
            
            请用中文回答问题。
            如果无法根据上下文回答问题，请回答"对不起，我没有找到相关的知识"。
            问题:{question}
            '''
            prompt = ChatPromptTemplate.from_template(template)
            output_parser = StrOutputParser()

            chain = {"context": retriever_from_llm | format_docs, "question": RunnablePassthrough()} \
                    | prompt \
                    | llm \
                    | output_parser
            output = chain.invoke(question)
        except Exception as e:
            logger.error(f"问答过程发生错误: {e}")
            output = f"处理您的问题时发生错误，请稍后再试。错误信息: {str(e)}"
    else:  # 若没添加知识库，则根据大模型本身的认知回答问题
        try:
            template = '''请用中文回答以下问题：
            问题:{question}
            '''
            prompt = ChatPromptTemplate.from_template(template)
            chain = {"question": RunnablePassthrough()} | prompt | llm | StrOutputParser()
            output = chain.invoke(question) + '\n\n（温馨提示：以上回答是基于通用数据的回答，若想基于文档回答请先添加知识库）'
        except Exception as e:
            logger.error(f"问答过程发生错误: {e}")
            output = f"处理您的问题时发生错误，请稍后再试。错误信息: {str(e)}"
    
    return output

# 创建向量存储的便捷函数
def create_vector_store(documents, embedding, store_name=None):
    """创建向量存储的便捷函数
    
    Args:
        documents (list): 文档列表
        embedding: 向量化模型
        store_name (str): 存储名称
        
    Returns:
        vectorstore: 向量存储对象
    """
    return vector_store_manager.create_vector_store(documents, embedding, store_name)

# 清空向量存储的便捷函数
def clear_vector_store(store_name=None):
    """清空向量存储的便捷函数
    
    Args:
        store_name (str): 存储名称
        
    Returns:
        bool: 是否清空成功
    """
    return vector_store_manager.clear_vector_store(store_name)

# 清空所有向量存储的便捷函数
def clear_all_vector_stores():
    """清空所有向量存储的便捷函数"""
    vector_store_manager.clear_all_vector_stores()