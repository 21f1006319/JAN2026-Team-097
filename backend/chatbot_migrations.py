"""
Chatbot Migration Script for Workforce & Payroll Management System
Adds tables for prompt-SQL pairs and chat history
"""
import sqlite3
import os

def run_migrations():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 1. Prompt-SQL Pairs table (for RAG vector search)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_sql_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_template TEXT NOT NULL,
            prompt_keywords TEXT NOT NULL,
            sql_query TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL CHECK(category IN ('employee', 'attendance', 'payroll', 'incentives', 'penalties', 'advances', 'stores', 'general')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Chat History table (for user-based chat history persistence)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL CHECK(message_type IN ('user', 'bot')),
            message TEXT NOT NULL,
            sql_query TEXT,
            query_results TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create index for faster user chat history retrieval
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_history_user_session 
        ON chat_history(user_id, session_id)
    ''')
    
    conn.commit()
    conn.close()
    print(f"Chatbot migrations completed successfully at: {db_path}")
    print("Created tables:")
    print("  - prompt_sql_pairs: Stores prompt-SQL mappings for RAG")
    print("  - chat_history: Stores user chat history")

if __name__ == '__main__':
    run_migrations()
