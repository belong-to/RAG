import mysql.connector
import hashlib
import streamlit as st

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 用户指定的MySQL密码
    'database': 'RAG'
}

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 添加管理员用户到admins表
def add_admin_user(username, password, email, role='admin'):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查管理员账户是否已存在
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"管理员账户 {username} 已存在")
            return True  # 管理员账户已存在
        
        # 创建管理员账户
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO admins (username, password, email, role) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, email, role)
        )
        conn.commit()
        print(f"管理员账户 {username} 创建成功！")
        return True
    except mysql.connector.Error as err:
        print(f"创建管理员账户失败: {err}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# 主函数
def main():
    # 添加admin用户
    add_admin_user('admin', 'admin', 'admin@example.com')
    
    # 添加wkx用户
    add_admin_user('wkx', 'Admin123', 'wkx@example.com')

if __name__ == "__main__":
    main()
    print("完成添加管理员用户到admins表")