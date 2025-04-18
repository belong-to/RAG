import jwt
import datetime
import logging
from functools import wraps
import streamlit as st

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth')

class JWTAuth:
    """JWT认证管理类"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式确保只有一个认证管理实例"""
        if cls._instance is None:
            cls._instance = super(JWTAuth, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, secret_key=None, token_expiry=24):
        """初始化JWT认证管理器
        
        Args:
            secret_key (str): JWT签名密钥
            token_expiry (int): 令牌过期时间(小时)
        """
        if self._initialized:
            return
            
        self.secret_key = secret_key or 'your-secret-key-change-in-production'
        self.token_expiry = token_expiry
        self._initialized = True
        logger.info("JWT认证管理器初始化完成")
    
    def generate_token(self, user_id, username, role='user'):
        """生成JWT令牌
        
        Args:
            user_id (int): 用户ID
            username (str): 用户名
            role (str): 用户角色
            
        Returns:
            str: JWT令牌
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=self.token_expiry),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id,
                'username': username,
                'role': role
            }
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm='HS256'
            )
            return token
        except Exception as e:
            logger.error(f"生成令牌失败: {e}")
            raise
    
    def verify_token(self, token):
        """验证JWT令牌
        
        Args:
            token (str): JWT令牌
            
        Returns:
            dict: 令牌载荷信息
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的令牌: {e}")
            return None
    
    def refresh_token(self, token):
        """刷新JWT令牌
        
        Args:
            token (str): 原JWT令牌
            
        Returns:
            str: 新的JWT令牌
        """
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
                
            # 创建新令牌，保留原始信息
            return self.generate_token(
                payload['sub'],
                payload['username'],
                payload['role']
            )
        except Exception as e:
            logger.error(f"刷新令牌失败: {e}")
            return None

# 全局JWT认证管理器实例
jwt_auth = JWTAuth()

# Streamlit认证装饰器
def login_required(func):
    """要求用户登录的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'jwt_token' not in st.session_state:
            st.error("请先登录")
            st.stop()
            return None
            
        token = st.session_state.jwt_token
        payload = jwt_auth.verify_token(token)
        
        if not payload:
            # 令牌无效，清除会话状态
            if 'jwt_token' in st.session_state:
                del st.session_state.jwt_token
            if 'username' in st.session_state:
                del st.session_state.username
            if 'logged_in' in st.session_state:
                st.session_state.logged_in = False
                
            st.error("会话已过期，请重新登录")
            st.stop()
            return None
            
        # 令牌有效，继续执行原函数
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    """要求管理员权限的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'jwt_token' not in st.session_state:
            st.error("请先登录")
            st.stop()
            return None
            
        token = st.session_state.jwt_token
        payload = jwt_auth.verify_token(token)
        
        if not payload:
            # 令牌无效，清除会话状态
            if 'jwt_token' in st.session_state:
                del st.session_state.jwt_token
            if 'username' in st.session_state:
                del st.session_state.username
            if 'logged_in' in st.session_state:
                st.session_state.logged_in = False
                
            st.error("会话已过期，请重新登录")
            st.stop()
            return None
            
        # 检查是否为管理员
        if payload.get('role') != 'admin':
            st.error("需要管理员权限")
            st.stop()
            return None
            
        # 权限验证通过，继续执行原函数
        return func(*args, **kwargs)
    return wrapper