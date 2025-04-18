import mysql.connector
import sys

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'rag'
}

def check_database_structure():
    try:
        # 连接MySQL服务器
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        print(f"可用数据库: {databases}")
        
        if db_config['database'] not in databases:
            print(f"数据库 {db_config['database']} 不存在，需要初始化数据库")
            return
        
        # 使用数据库
        cursor.execute(f"USE {db_config['database']}")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"数据库中的表: {tables}")
        
        if 'users' not in tables:
            print("users表不存在，需要创建表")
            return
        
        # 检查users表结构
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("\nusers表结构:")
        for column in columns:
            print(f"字段名: {column[0]}, 类型: {column[1]}, 是否为空: {column[2]}, 键: {column[3]}, 默认值: {column[4]}, 额外信息: {column[5]}")
        
        # 检查是否存在email_verified字段
        column_names = [column[0] for column in columns]
        if 'email_verified' not in column_names:
            print("\n警告: users表中不存在email_verified字段，这可能导致查询错误")
            print("建议添加email_verified字段或修改查询语句")
        else:
            print("\nusers表中存在email_verified字段")
        
    except mysql.connector.Error as err:
        print(f"数据库操作失败: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    check_database_structure()