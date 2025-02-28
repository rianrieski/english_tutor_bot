import sqlite3

def check_database():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Check user_levels
    cursor.execute("SELECT * FROM user_levels;")
    users = cursor.fetchall()
    print("\nUser Levels:", users)
    
    # Check conversations
    cursor.execute("SELECT * FROM conversations;")
    convos = cursor.fetchall()
    print("\nConversations:", convos)
    
    conn.close()

if __name__ == "__main__":
    check_database() 