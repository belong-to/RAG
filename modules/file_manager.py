import os
import logging
import streamlit as st

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('file_manager')

def get_all_uploaded_files(upload_dir='./uploads'):
    """
    获取上传文件夹中的所有文件
    
    Args:
        upload_dir (str): 上传文件夹路径
        
    Returns:
        list: 文件路径列表
    """
    try:
        # 确保上传文件夹存在
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            logger.info(f"创建上传文件夹: {upload_dir}")
            return []
        
        # 获取所有文件
        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                # 只返回支持的文件类型
                name, extension = os.path.splitext(filename)
                if extension.lower() in ['.pdf', '.docx', '.txt', '.doc']:
                    files.append(file_path)
        
        logger.info(f"找到 {len(files)} 个文件在上传文件夹中")
        return files
    except Exception as e:
        logger.error(f"获取上传文件列表失败: {e}")
        return []

def save_uploaded_files(uploaded_files, upload_dir='./uploads'):
    """
    保存上传的文件到指定文件夹
    
    Args:
        uploaded_files (list): Streamlit上传的文件对象列表
        upload_dir (str): 上传文件夹路径
        
    Returns:
        list: 保存的文件名列表
    """
    saved_files = []
    
    try:
        # 确保上传文件夹存在
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            logger.info(f"创建上传文件夹: {upload_dir}")
        
        # 处理每个上传的文件
        for uploaded_file in uploaded_files:
            try:
                # 读取文件内容
                bytes_data = uploaded_file.read()
                
                # 保存文件
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(bytes_data)
                
                saved_files.append(uploaded_file.name)
                logger.info(f"文件保存成功: {uploaded_file.name}")
            except Exception as e:
                logger.error(f"保存文件 {uploaded_file.name} 失败: {e}")
    except Exception as e:
        logger.error(f"保存上传文件过程中发生错误: {e}")
    
    return saved_files

def clear_uploaded_files(filenames, upload_dir='./uploads'):
    """
    清理上传的文件
    
    Args:
        filenames (list): 文件名列表
        upload_dir (str): 上传文件夹路径
        
    Returns:
        bool: 是否全部清理成功
    """
    success = True
    
    for filename in filenames:
        try:
            file_path = os.path.join(upload_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件删除成功: {filename}")
            else:
                logger.warning(f"文件不存在，无法删除: {filename}")
                success = False
        except Exception as e:
            logger.error(f"删除文件 {filename} 失败: {e}")
            success = False
    
    return success