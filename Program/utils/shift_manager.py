"""
utils/shift_manager.py - Shift Management
"""

from datetime import datetime, date, time, timedelta
from config import DAYS_OF_WEEK, DAYS_MAP, DEFAULT_SHIFT_SCHEDULE


class ShiftManager:
    """Manager for shift schedules"""
    
    def __init__(self, database):
        self.db = database
        self._schedule = None
        self._load_schedule()
    
    def _load_schedule(self):
        """Load schedule from database"""
        self._schedule = self.db.get_shift_schedule()
        
        # Use default if empty
        if not self._schedule or len(self._schedule) < 2:
            self._schedule = DEFAULT_SHIFT_SCHEDULE.copy()
            self.db.save_shift_schedule(self._schedule)
    
    def reload_schedule(self):
        """Reload schedule from database"""
        self._load_schedule()
    
    def get_schedule(self):
        """Get current schedule"""
        return self._schedule
    
    def save_schedule(self, schedule_dict):
        """Save schedule"""
        self._schedule = schedule_dict
        self.db.save_shift_schedule(schedule_dict)
    
    def get_current_shift(self):
        """
        Get current shift based on time
        
        Returns:
            dict: {name, shift_key, start, end} or None if no shift
        """
        now = datetime.now()
        current_day = DAYS_OF_WEEK[now.weekday()]
        current_time = now.time()
        
        for shift_key in ["shift_1", "shift_2"]:
            shift_data = self._schedule.get(shift_key, {})
            day_config = shift_data.get(current_day, {})
            
            if not day_config.get("enabled", False):
                continue
            
            start_str = day_config.get("start", "00:00")
            end_str = day_config.get("end", "00:00")
            
            try:
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                
                # Handle overnight shift
                if end_time < start_time:
                    # Night shift (e.g., 19:30 - 07:30)
                    if current_time >= start_time or current_time < end_time:
                        return {
                            "name": shift_data.get("name", shift_key),
                            "shift_key": shift_key,
                            "start": start_str,
                            "end": end_str,
                            "day": current_day
                        }
                else:
                    # Day shift
                    if start_time <= current_time < end_time:
                        return {
                            "name": shift_data.get("name", shift_key),
                            "shift_key": shift_key,
                            "start": start_str,
                            "end": end_str,
                            "day": current_day
                        }
            except:
                continue
        
        return None
    
    def get_shift_date(self, shift_info=None):
        """
        Get shift date (for overnight shifts, use start date)
        """
        if shift_info is None:
            shift_info = self.get_current_shift()
        
        if not shift_info:
            return date.today()
        
        now = datetime.now()
        current_time = now.time()
        
        try:
            start_time = datetime.strptime(shift_info["start"], "%H:%M").time()
            end_time = datetime.strptime(shift_info["end"], "%H:%M").time()
            
            # Night shift after midnight
            if end_time < start_time and current_time < end_time:
                return (now - timedelta(days=1)).date()
        except:
            pass
        
        return now.date()
    
    def format_shift_display(self, shift_info):
        """Format shift info for display"""
        if not shift_info:
            return "No Active Shift"
        
        return f"{shift_info['name']} ({shift_info['start']} - {shift_info['end']})"