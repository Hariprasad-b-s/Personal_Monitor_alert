from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, date
import json

app = Flask(__name__)
CORS(app)

DATABASE = 'daily_tracker.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            time_minutes INTEGER DEFAULT 0,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (parent_id) REFERENCES tasks(id)
        )
    ''')
    
    # Create daily_progress table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            UNIQUE(task_id, date)
        )
    ''')
    
    # Create timer_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            duration INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    
    # Check if tasks exist, if not, populate with default tasks
    cursor.execute('SELECT COUNT(*) as count FROM tasks')
    if cursor.fetchone()['count'] == 0:
        default_tasks = [
            (None, '25 Apps (Time - 2.5 hrs)', None, 150, 1),
            (None, '15 with claude and Linkedin 15 connections for each app', 1, 90, 1),
            (None, '10 generics', 1, 60, 2),
            (None, 'Leetcode Min- 2 to 5 (Time 1.5 to 2 hrs)', None, 90, 2),
            (None, 'Projects (Data engineer (Resume), AI, ML) and push to Github - 2 hrs', None, 120, 3),
            (None, 'Learn AI (Andrew NG) 30 mins', None, 30, 4),
            (None, 'Learn Data Engineering other tools 1 hr', None, 60, 5),
            (None, 'Learn ML - 1 hr', None, 60, 6),
            (None, 'Learn MLOPS - 30 mins', None, 30, 7),
        ]
        
        cursor.executemany('''
            INSERT INTO tasks (id, name, parent_id, time_minutes, position)
            VALUES (?, ?, ?, ?, ?)
        ''', default_tasks)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks with hierarchy"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, parent_id, time_minutes, position
        FROM tasks
        ORDER BY position, id
    ''')
    
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(tasks)

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task time"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE tasks
        SET time_minutes = ?
        WHERE id = ?
    ''', (data.get('time_minutes'), task_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/progress/today', methods=['GET'])
def get_today_progress():
    """Get today's progress"""
    today = date.today().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_id, completed, time_spent
        FROM daily_progress
        WHERE date = ?
    ''', (today,))
    
    progress = {row['task_id']: dict(row) for row in cursor.fetchall()}
    conn.close()
    
    return jsonify(progress)

@app.route('/api/progress/toggle', methods=['POST'])
def toggle_progress():
    """Toggle task completion"""
    data = request.json
    task_id = data.get('task_id')
    today = date.today().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if progress exists
    cursor.execute('''
        SELECT completed FROM daily_progress
        WHERE task_id = ? AND date = ?
    ''', (task_id, today))
    
    row = cursor.fetchone()
    
    if row:
        # Toggle completion
        new_status = not row['completed']
        cursor.execute('''
            UPDATE daily_progress
            SET completed = ?
            WHERE task_id = ? AND date = ?
        ''', (new_status, task_id, today))
    else:
        # Create new progress entry
        cursor.execute('''
            INSERT INTO daily_progress (task_id, date, completed)
            VALUES (?, ?, 1)
        ''', (task_id, today))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/timer/session', methods=['POST'])
def save_timer_session():
    """Save timer session"""
    data = request.json
    task_id = data.get('task_id')
    duration = data.get('duration')  # in seconds
    today = date.today().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Save timer session
    cursor.execute('''
        INSERT INTO timer_sessions (task_id, date, duration)
        VALUES (?, ?, ?)
    ''', (task_id, today, duration))
    
    # Update daily progress time_spent
    cursor.execute('''
        INSERT INTO daily_progress (task_id, date, time_spent)
        VALUES (?, ?, ?)
        ON CONFLICT(task_id, date) DO UPDATE SET
        time_spent = time_spent + ?
    ''', (task_id, today, duration, duration))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/stats/weekly', methods=['GET'])
def get_weekly_stats():
    """Get weekly statistics for chart"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get last 7 days of data
    cursor.execute('''
        SELECT 
            date,
            COUNT(DISTINCT task_id) as tasks_completed,
            SUM(time_spent) as total_time
        FROM daily_progress
        WHERE completed = 1
        AND date >= date('now', '-7 days')
        GROUP BY date
        ORDER BY date
    ''')
    
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(stats)

@app.route('/api/stats/daily', methods=['GET'])
def get_daily_stats():
    """Get daily statistics for the last 30 days"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            date,
            COUNT(DISTINCT CASE WHEN completed = 1 THEN task_id END) as completed_tasks,
            COUNT(DISTINCT task_id) as total_tasks,
            SUM(time_spent) as total_time_seconds
        FROM daily_progress
        WHERE date >= date('now', '-30 days')
        GROUP BY date
        ORDER BY date
    ''')
    
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(stats)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
