import streamlit as st
from langchain_community.vectorstores import Qdrant
from langchain_community.document_transformers import LongContextReorder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

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

def format_docs(docs):
    '''
    将返回的文档page_content的内容拼接为字符串，减少其他信息干扰
    :param docs: 文档对象
    :return: 拼接后的字符串
    '''
    reordering = LongContextReorder() # 实例化对象
    reordered_docs = reordering.transform_documents(docs) # 文档重排
    # 文档重排后，将内容拼接为字符串输出
    return "\n\n".join([doc.page_content for doc in reordered_docs])

def ask_and_get_answer(llm, ask, vector_store, k=3):
    '''
    问答函数
    :param llm: 大模型
    :param ask: 问题
    :param vector_store: 向量化存储的对象
    :param k: 相似度前k个文档
    :return: 答案
    '''
    if st.session_state.vs != []: # 若添加了知识库，则根据知识库回答问题
        if k>3:
            retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': k})
        else:
            retriever = vector_store.as_retriever(search_type='similarity')
        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=llm
        )

        template = '''Answer the question based only on the following context:{context}
        Please answer the question only by chinese.
        If you can't answer the question, please say "对不起，我没有找到相关的知识".
        Question:{question}
        '''
        prompt = ChatPromptTemplate.from_template(template)
        output_parser = StrOutputParser()

        chain = {"context": retriever | format_docs, "question": RunnablePassthrough()} \
                | prompt \
                | llm \
                | output_parser
        output = chain.invoke(ask)
    else: # 若没添加知识库，则根据大模型本身的认知回答问题
        template = '''Answer the question by chinese.
        Question:{question}
        '''
        prompt = ChatPromptTemplate.from_template(template)
        chain = {"question": RunnablePassthrough()}| prompt | llm | StrOutputParser()
        output = chain.invoke(ask) + '\n\n（温馨提示：以上回答是基于通用数据的回答，若想基于文档回答请先【添加知识库】）'
    return output

def clear_embedding():
    '''
    清空知识库和文档
    :return:
    '''
    for i in st.session_state.filenames: # 删除保存的文件
        try:
            delfile = os.path.join('./', i)
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