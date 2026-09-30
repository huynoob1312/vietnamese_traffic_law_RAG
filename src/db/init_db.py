import sys
import pymysql
from src.utils.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
from src.db.database import engine, Base
import src.db.models  # Ensure models are loaded

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def create_database_if_not_exists():
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4"
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        connection.commit()
        print(f"✅ Cơ sở dữ liệu '{MYSQL_DB}' đã sẵn sàng.")
    finally:
        connection.close()

def init_tables():
    print("⏳ Đang khởi tạo các bảng MySQL (users, chat_sessions, chat_messages)...")
    create_database_if_not_exists()
    Base.metadata.create_all(bind=engine)
    print("✅ Đã khởi tạo thành công các bảng trong CSDL MySQL!")

if __name__ == "__main__":
    init_tables()
