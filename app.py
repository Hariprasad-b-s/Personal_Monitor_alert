from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL', 'daily_tracker.db')

def get_db():
    """Get database connection (SQLite or PostgreSQL)"""
    if DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://'):
        # Fix for Render/Heroku which sometimes provides 'postgres://' instead of 'postgresql://'
        url = DATABASE_URL
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(url)
        return conn
    else:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if we are using PostgreSQL
    is_postgres = hasattr(conn, 'tpc_prepare') or not hasattr(conn, 'row_factory')
    
    # Serial/Autoincrement differences
    id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Create tasks table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS tasks (
            id {id_type},
            name TEXT NOT NULL,
            parent_id INTEGER,
            time_minutes INTEGER DEFAULT 0,
            position INTEGER DEFAULT 0
        )
    ''')
    
    # Create daily_progress table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS daily_progress (
            id {id_type},
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completed BOOLEAN DEFAULT false,
            time_spent INTEGER DEFAULT 0,
            UNIQUE(task_id, date)
        )
    ''')
    
    # Create timer_sessions table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS timer_sessions (
            id {id_type},
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            duration INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if tasks exist, if not, populate with default tasks
    cursor.execute('SELECT COUNT(*) FROM tasks')
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_tasks = [
            (1, '25 Apps (Time - 2.5 hrs)', None, 150, 1),
            (2, '15 with claude and Linkedin 15 connections for each app', 1, 90, 1),
            (3, '10 generics', 1, 60, 2),
            (4, 'Leetcode Min- 2 to 5 (Time 1.5 to 2 hrs)', None, 90, 2),
            (5, 'Projects (Data engineer (Resume), AI, ML) and push to Github - 2 hrs', None, 120, 3),
            (6, 'Learn AI (Andrew NG) 30 mins', None, 30, 4),
            (7, 'Learn Data Engineering other tools 1 hr', None, 60, 5),
            (8, 'Learn ML - 1 hr', None, 60, 6),
            (9, 'Learn MLOPS - 30 mins', None, 30, 7),
        ]
        
        # PostgreSQL handles many-insert differently if specifying IDs
        for task in default_tasks:
            cursor.execute('''
                INSERT INTO tasks (id, name, parent_id, time_minutes, position)
                VALUES (%s, %s, %s, %s, %s)
            ''' if is_postgres else '''
                INSERT INTO tasks (id, name, parent_id, time_minutes, position)
                VALUES (?, ?, ?, ?, ?)
            ''', task)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

def query_db(query, args=(), one=False):
    """Helper for fetching results from both DB types"""
    conn = get_db()
    is_postgres = not hasattr(conn, 'row_factory')
    
    # Adjust placeholders for PostgreSQL (%) vs SQLite (?)
    if is_postgres:
        query = query.replace('?', '%s')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    
    cursor.execute(query, args)
    rv = cursor.fetchall()
    
    # Convert to list of dicts for SQLite/psycopg2 uniformity
    if not is_postgres:
        results = [dict(row) for row in rv]
    else:
        results = [dict(row) for row in rv]
        
    conn.close()
    return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    """Helper for executing updates/inserts"""
    conn = get_db()
    is_postgres = not hasattr(conn, 'row_factory')
    
    if is_postgres:
        query = query.replace('?', '%s')
    
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()
    return True

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with hierarchy"""
    tasks = query_db('''
        SELECT id, name, parent_id, time_minutes, position
        FROM tasks
        ORDER BY position, id
    ''')
    return jsonify(tasks)

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task time"""
    data = request.json
    execute_db('''
        UPDATE tasks
        SET time_minutes = ?
        WHERE id = ?
    ''', (data.get('time_minutes'), task_id))
    return jsonify({'success': True})

@app.route('/api/progress/today', methods=['GET'])
def get_today_progress():
    """Get today's progress"""
    today = date.today().isoformat()
    rows = query_db('''
        SELECT task_id, completed, time_spent
        FROM daily_progress
        WHERE date = ?
    ''', (today,))
    
    progress = {row['task_id']: row for row in rows}
    return jsonify(progress)

@app.route('/api/progress/toggle', methods=['POST'])
def toggle_progress():
    """Toggle task completion"""
    data = request.json
    task_id = data.get('task_id')
    today = date.today().isoformat()
    
    row = query_db('''
        SELECT completed FROM daily_progress
        WHERE task_id = ? AND date = ?
    ''', (task_id, today), one=True)
    
    if row:
        new_status = not row['completed']
        execute_db('''
            UPDATE daily_progress
            SET completed = ?
            WHERE task_id = ? AND date = ?
        ''', (new_status, task_id, today))
    else:
        execute_db('''
            INSERT INTO daily_progress (task_id, date, completed)
            VALUES (?, ?, true)
        ''', (task_id, today))
    
    return jsonify({'success': True})

@app.route('/api/timer/session', methods=['POST'])
def save_timer_session():
    """Save timer session"""
    data = request.json
    task_id = data.get('task_id')
    duration = data.get('duration')
    today = date.today().isoformat()
    
    # Save timer session
    execute_db('''
        INSERT INTO timer_sessions (task_id, date, duration)
        VALUES (?, ?, ?)
    ''', (task_id, today, duration))
    
    # Update daily progress using ON CONFLICT (specific to DB type, but we'll use a safer approach)
    row = query_db('SELECT id FROM daily_progress WHERE task_id = ? AND date = ?', (task_id, today), one=True)
    if row:
        execute_db('''
            UPDATE daily_progress
            SET time_spent = time_spent + ?
            WHERE task_id = ? AND date = ?
        ''', (duration, task_id, today))
    else:
        execute_db('''
            INSERT INTO daily_progress (task_id, date, time_spent)
            VALUES (?, ?, ?)
        ''', (task_id, today, duration))
    
    return jsonify({'success': True})

@app.route('/api/stats/weekly', methods=['GET'])
def get_weekly_stats():
    """Get weekly statistics for chart"""
    # PostgreSQL requires slightly different date functions than SQLite
    conn = get_db()
    is_postgres = not hasattr(conn, 'row_factory')
    conn.close()
    
    date_query = "date::date >= CURRENT_DATE - INTERVAL '7 days'" if is_postgres else "date >= date('now', '-7 days')"
    
    stats = query_db(f'''
        SELECT 
            date,
            COUNT(DISTINCT task_id) as tasks_completed,
            SUM(time_spent) as total_time
        FROM daily_progress
        WHERE completed = {'true' if is_postgres else '1'}
        AND {date_query}
        GROUP BY date
        ORDER BY date
    ''')
    
    return jsonify(stats)

@app.route('/api/stats/daily', methods=['GET'])
def get_daily_stats():
    """Get daily statistics for the last 30 days"""
    conn = get_db()
    is_postgres = not hasattr(conn, 'row_factory')
    conn.close()
    
    date_query = "date::date >= CURRENT_DATE - INTERVAL '30 days'" if is_postgres else "date >= date('now', '-30 days')"
    
    # CASE WHEN syntax for SQLite and PG
    stats = query_db(f'''
        SELECT 
            date,
            COUNT(DISTINCT CASE WHEN completed = {'true' if is_postgres else '1'} THEN task_id END) as completed_tasks,
            COUNT(DISTINCT task_id) as total_tasks,
            SUM(time_spent) as total_time_seconds
        FROM daily_progress
        WHERE {date_query}
        GROUP BY date
        ORDER BY date
    ''')
    
    return jsonify(stats)

# Initialize DB on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
