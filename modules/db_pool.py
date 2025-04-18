import mysql.connector
from mysql.connector import pooling
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_pool')

class DatabasePool:
    """数据库连接池管理类"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式确保只有一个连接池实例"""
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config=None, pool_size=5, pool_name='rag_pool'):
        """初始化连接池
        
        Args:
            config (dict): 数据库配置信息
            pool_size (int): 连接池大小
            pool_name (str): 连接池名称
        """
        if self._initialized:
            return
            
        self.config = config or {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'RAG'
        }
        self.pool_size = pool_size
        self.pool_name = pool_name
        self._pool = None
        self._create_pool()
        self._initialized = True
        logger.info(f"数据库连接池初始化完成，池大小: {pool_size}")
    
    def _create_pool(self):
        """创建数据库连接池"""
        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.pool_name,
                pool_size=self.pool_size,
                **self.config
            )
            logger.info("数据库连接池创建成功")
        except Exception as e:
            logger.error(f"创建数据库连接池失败: {e}")
            raise
    
    def get_connection(self, max_retries=3, retry_delay=1):
        """从连接池获取连接，支持重试机制
        
        Args:
            max_retries (int): 最大重试次数
            retry_delay (int): 重试延迟时间(秒)
            
        Returns:
            connection: 数据库连接对象
        """
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                connection = self._pool.get_connection()
                return connection
            except Exception as e:
                last_error = e
                logger.warning(f"获取数据库连接失败 (尝试 {retries+1}/{max_retries}): {e}")
                retries += 1
                if retries < max_retries:
                    time.sleep(retry_delay)
        
        logger.error(f"获取数据库连接失败，已达到最大重试次数: {last_error}")
        raise last_error
    
    def execute_query(self, query, params=None, commit=False):
        """执行SQL查询
        
        Args:
            query (str): SQL查询语句
            params (tuple): 查询参数
            commit (bool): 是否提交事务
            
        Returns:
            result: 查询结果
        """
        connection = None
        cursor = None
        result = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                
            if commit:
                connection.commit()
                
            return result
        except Exception as e:
            if connection and commit:
                connection.rollback()
            logger.error(f"执行查询失败: {e}, 查询: {query}, 参数: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_many(self, query, params_list):
        """批量执行SQL语句
        
        Args:
            query (str): SQL查询语句
            params_list (list): 参数列表
            
        Returns:
            int: 影响的行数
        """
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.executemany(query, params_list)
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"批量执行查询失败: {e}, 查询: {query}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

# 全局数据库连接池实例
db_pool = DatabasePool()

# 辅助函数，用于在应用中方便地执行查询
def query(sql, params=None, commit=False):
    """执行SQL查询的便捷函数"""
    return db_pool.execute_query(sql, params, commit)

def query_one(sql, params=None):
    """执行SQL查询并返回第一条结果的便捷函数"""
    result = db_pool.execute_query(sql, params)
    return result[0] if result else None

def execute(sql, params=None):
    """执行SQL更新操作的便捷函数"""
    return db_pool.execute_query(sql, params, commit=True)

def execute_many(sql, params_list):
    """批量执行SQL操作的便捷函数"""
    return db_pool.execute_many(sql, params_list)