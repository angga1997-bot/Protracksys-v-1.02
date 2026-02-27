"""
utils/database.py - SQLite Database Manager
"""

import sqlite3
import os
import json
from datetime import datetime, date
from config import DATABASE_FILE, DATA_DIR


class Database:
    """SQLite Database Manager"""
    
    def __init__(self):
        self.db_file = DATABASE_FILE
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Production data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS production_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                shift_name TEXT,
                shift_date DATE,
                product_no INTEGER,
                data_json TEXT,
                images_json TEXT
            )
        ''')
        
        # Members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                photo TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        ''')
        
        # Shift schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shift_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_key TEXT NOT NULL,
                day_name TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                enabled INTEGER DEFAULT 1,
                UNIQUE(shift_key, day_name)
            )
        ''')
        
        # Config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Daily summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_date DATE,
                shift_name TEXT,
                total_count INTEGER DEFAULT 0,
                last_product_no INTEGER DEFAULT 0,
                UNIQUE(summary_date, shift_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ===== Production Data Methods =====
    
    def insert_production(self, shift_name, shift_date, product_no, data_dict, images_list=None):
        """Insert production data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO production_data (shift_name, shift_date, product_no, data_json, images_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            shift_name,
            shift_date,
            product_no,
            json.dumps(data_dict, ensure_ascii=False),
            json.dumps(images_list or [], ensure_ascii=False)
        ))
        
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return last_id
    
    def get_production_history(self, start_date=None, end_date=None, shift=None, limit=100, offset=0):
        """Get production history with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM production_data WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND DATE(created_at) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(created_at) <= ?"
            params.append(end_date)
        
        if shift:
            query += " AND shift_name = ?"
            params.append(shift)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            item = dict(row)
            item['data'] = json.loads(item['data_json']) if item['data_json'] else {}
            item['images'] = json.loads(item['images_json']) if item['images_json'] else []
            result.append(item)
        
        conn.close()
        return result
    
    def get_production_count(self, start_date=None, end_date=None, shift=None):
        """Get total count of production records"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) as count FROM production_data WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND DATE(created_at) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(created_at) <= ?"
            params.append(end_date)
        
        if shift:
            query += " AND shift_name = ?"
            params.append(shift)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        conn.close()
        return result['count'] if result else 0
    
    def delete_production(self, record_id):
        """Delete production record"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM production_data WHERE id = ?", (record_id,))
        
        conn.commit()
        conn.close()
    
    # ===== Summary Methods =====
    
    def get_daily_summary(self, summary_date, shift_name):
        """Get daily summary for a shift"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_summary 
            WHERE summary_date = ? AND shift_name = ?
        ''', (summary_date, shift_name))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_daily_summary(self, summary_date, shift_name, total_count, last_product_no):
        """Update or insert daily summary"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO daily_summary (summary_date, shift_name, total_count, last_product_no)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(summary_date, shift_name) 
            DO UPDATE SET total_count = ?, last_product_no = ?
        ''', (summary_date, shift_name, total_count, last_product_no, total_count, last_product_no))
        
        conn.commit()
        conn.close()
    
    def get_today_count(self, shift_name=None):
        """Get today's production count"""
        today = date.today().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if shift_name:
            cursor.execute('''
                SELECT COUNT(*) as count FROM production_data 
                WHERE DATE(created_at) = ? AND shift_name = ?
            ''', (today, shift_name))
        else:
            cursor.execute('''
                SELECT COUNT(*) as count FROM production_data 
                WHERE DATE(created_at) = ?
            ''', (today,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def get_shift_count(self, shift_name, shift_date=None):
        """Get count for specific shift"""
        if shift_date is None:
            shift_date = date.today().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM production_data 
            WHERE shift_date = ? AND shift_name = ?
        ''', (shift_date, shift_name))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def get_next_product_no(self, shift_name, shift_date=None):
        """Get next product number for shift"""
        if shift_date is None:
            shift_date = date.today().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(product_no) as max_no FROM production_data 
            WHERE shift_date = ? AND shift_name = ?
        ''', (shift_date, shift_name))
        
        result = cursor.fetchone()
        conn.close()
        
        max_no = result['max_no'] if result and result['max_no'] else 0
        return max_no + 1
    
    # ===== Members Methods =====
    
    def add_member(self, id_number, name, photo=None):
        """Add new member"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO members (id_number, name, photo)
                VALUES (?, ?, ?)
            ''', (id_number, name, photo))
            
            conn.commit()
            conn.close()
            return True, "Member added successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "ID already registered!"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def update_member(self, id_number, name=None, photo=None):
        """Update member"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        
        if photo:
            updates.append("photo = ?")
            params.append(photo)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            query = f"UPDATE members SET {', '.join(updates)} WHERE id_number = ?"
            params.append(id_number)
            
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return True, "Member updated successfully!"
    
    def delete_member(self, id_number):
        """Delete member"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM members WHERE id_number = ?", (id_number,))
        
        conn.commit()
        conn.close()
        return True, "Member deleted successfully!"
    
    def get_member(self, id_number):
        """Get member by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM members WHERE id_number = ?", (id_number,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def get_all_members(self, search=None):
        """Get all members"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if search:
            cursor.execute('''
                SELECT * FROM members 
                WHERE id_number LIKE ? OR name LIKE ?
                ORDER BY name
            ''', (f'%{search}%', f'%{search}%'))
        else:
            cursor.execute("SELECT * FROM members ORDER BY name")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ===== Shift Schedule Methods =====
    
    def get_shift_schedule(self):
        """Get all shift schedules"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM shift_schedule ORDER BY shift_key, day_name")
        rows = cursor.fetchall()
        
        conn.close()
        
        # Convert to nested dict
        schedule = {"shift_1": {"name": "Shift 1"}, "shift_2": {"name": "Shift 2"}}
        
        for row in rows:
            r = dict(row)
            shift_key = r['shift_key']
            day_name = r['day_name']
            
            if shift_key not in schedule:
                schedule[shift_key] = {"name": shift_key.replace("_", " ").title()}
            
            schedule[shift_key][day_name] = {
                "start": r['start_time'],
                "end": r['end_time'],
                "enabled": bool(r['enabled'])
            }
        
        return schedule
    
    def save_shift_schedule(self, schedule_dict):
        """Save shift schedule"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for shift_key, shift_data in schedule_dict.items():
            for day_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if day_name in shift_data and isinstance(shift_data[day_name], dict):
                    day_config = shift_data[day_name]
                    
                    cursor.execute('''
                        INSERT INTO shift_schedule (shift_key, day_name, start_time, end_time, enabled)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(shift_key, day_name)
                        DO UPDATE SET start_time = ?, end_time = ?, enabled = ?
                    ''', (
                        shift_key, day_name,
                        day_config.get("start", "07:30"),
                        day_config.get("end", "19:30"),
                        1 if day_config.get("enabled", True) else 0,
                        day_config.get("start", "07:30"),
                        day_config.get("end", "19:30"),
                        1 if day_config.get("enabled", True) else 0
                    ))
        
        conn.commit()
        conn.close()
    
    # ===== Config Methods =====
    
    def get_config(self, key, default=None):
        """Get config value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        
        return default
    
    def set_config(self, key, value):
        """Set config value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO app_config (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
        ''', (key, value, value))
        
        conn.commit()
        conn.close()