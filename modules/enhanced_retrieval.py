import streamlit as st
import logging
from typing import List, Dict, Any, Optional, Union
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_transformers import LongContextReorder
from langchain.retrievers.multi_query import MultiQueryRetriever
from modules.search_engine import get_search_engine, format_search_results, SearchResult
from modules.vector_store import format_docs
from modules.model_interface import get_realtime_info

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_retrieval')

def enhanced_retrieval(llm, query, vector_store=None, search_engine_name=None, 
                      use_web_search=False, k=3, num_web_results=5):
    """
    增强版检索函数，结合文档检索和网络搜索，并支持回答实时问题
    
    Args:
        llm: 大语言模型
        query: 用户查询
        vector_store: 向量存储对象
        search_engine_name: 搜索引擎名称
        use_web_search: 是否使用网络搜索
        k: 文档检索返回的文档数量
        num_web_results: 网络搜索返回的结果数量
        
    Returns:
        str: 回答
    """
    # 首先检查是否是实时问题（如日期、时间等）
    realtime_answer = get_realtime_info(query)
    if realtime_answer:
        return realtime_answer
        
    # 初始化上下文和来源信息
    context = ""
    sources = []
    
    # 1. 从本地知识库检索
    if vector_store is not None and st.session_state.vs != []:
        if k > 3:
            retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': k})
        else:
            retriever = vector_store.as_retriever(search_type='similarity')
        
        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=llm
        )
        
        # 获取文档并格式化
        docs = retriever_from_llm.get_relevant_documents(query)
        if docs:
            context += "\n\n本地知识库信息:\n" + format_docs(docs)
            sources.append("本地知识库")
    
    # 2. 从网络搜索获取信息
    if use_web_search and search_engine_name:
        try:
            # 获取搜索引擎实例
            search_engine = get_search_engine(search_engine_name)
            
            # 执行搜索
            search_results = search_engine.search(query, num_results=num_web_results)
            
            if search_results:
                # 格式化搜索结果
                web_context = format_search_results(search_results)
                context += "\n\n网络搜索结果:\n" + web_context
                sources.append(f"{search_engine_name}搜索")
        except Exception as e:
            logger.error(f"网络搜索失败: {e}")
            st.warning(f"网络搜索失败: {e}")
    
    # 3. 根据检索到的信息生成回答
    if context:
        # 有上下文信息时，基于上下文回答
        template = '''
        请基于以下信息回答用户的问题。如果提供的信息不足以回答问题，请明确指出。
        请使用中文回答。
        
        信息来源:
        {context}
        
        用户问题: {question}
        '''
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = {"context": lambda _: context, "question": RunnablePassthrough()} \
                | prompt \
                | llm \
                | StrOutputParser()
        
        output = chain.invoke(query)
        
        # 添加来源信息
        if sources:
            output += f"\n\n(信息来源: {', '.join(sources)})"
    else:
        # 没有上下文信息时，使用模型本身的知识回答
        template = '''请用中文回答以下问题:
        问题: {question}
        '''
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = {"question": RunnablePassthrough()} | prompt | llm | StrOutputParser()
        
        output = chain.invoke(query) + '\n\n(温馨提示: 以上回答基于模型的通用知识。若需基于特定文档回答，请先添加知识库或启用网络搜索)'
    
    return output