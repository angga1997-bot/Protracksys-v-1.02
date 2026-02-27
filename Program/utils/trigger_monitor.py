"""
utils/trigger_monitor.py - Monitor trigger dari PLC
"""

import threading
import time
from datetime import datetime


class TriggerMonitor:
    """Class untuk memonitor trigger dari PLC"""
    
    def __init__(self, plc_client, config, callback):
        """
        Args:
            plc_client: Instance PLCFinsClient
            config: Konfigurasi trigger
            callback: Function yang dipanggil saat trigger terdeteksi
        """
        self.plc_client = plc_client
        self.config = config
        self.callback = callback
        
        self.running = False
        self.thread = None
        self.last_values = {}
        self.poll_interval = 0.1  # 100ms
    
    def start(self):
        """Mulai monitoring"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Loop utama monitoring"""
        while self.running:
            try:
                self._check_triggers()
            except Exception as e:
                print(f"Trigger monitor error: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_triggers(self):
        """Cek semua trigger"""
        if not self.config.get("enabled", False):
            return
        
        # Cek main trigger
        main_trigger = self.config.get("trigger_address", {})
        if main_trigger:
            triggered = self._check_single_trigger(
                "main",
                main_trigger,
                self.config.get("trigger_type", "rising")
            )
            
            if triggered:
                self._on_trigger("main", self.config.get("action", "save_data"))
        
        # Cek image triggers
        for idx, img_trigger in enumerate(self.config.get("image_triggers", [])):
            if img_trigger.get("enabled", False):
                key = f"image_{idx}"
                triggered = self._check_single_trigger(
                    key,
                    img_trigger.get("address", {}),
                    img_trigger.get("trigger_type", "rising")
                )
                
                if triggered:
                    self._on_trigger(key, "capture_image", img_trigger)
    
    def _check_single_trigger(self, key, address_config, trigger_type):
        """
        Cek satu trigger
        
        Returns:
            bool: True jika trigger terdeteksi
        """
        if not self.plc_client or not self.plc_client.connected:
            return False
        
        area_type = address_config.get("area_type", "DM")
        address = address_config.get("address", 0)
        bit = address_config.get("bit", 0)
        
        # Baca nilai
        success, data = self.plc_client.read_memory(area_type, address, 1)
        
        if not success or not data:
            return False
        
        # Get current value (word atau bit)
        current_word = data[0] if data else 0
        
        # Jika bit specified, ambil bit tersebut
        if bit is not None and bit >= 0:
            current_value = (current_word >> bit) & 1
        else:
            current_value = 1 if current_word != 0 else 0
        
        # Get last value
        last_value = self.last_values.get(key, 0)
        
        # Update last value
        self.last_values[key] = current_value
        
        # Check trigger condition
        if trigger_type == "rising":
            return last_value == 0 and current_value == 1
        elif trigger_type == "falling":
            return last_value == 1 and current_value == 0
        elif trigger_type == "level_on":
            return current_value == 1
        elif trigger_type == "level_off":
            return current_value == 0
        
        return False
    
    def _on_trigger(self, trigger_key, action, extra_config=None):
        """Handle trigger event"""
        event = {
            "trigger_key": trigger_key,
            "action": action,
            "timestamp": datetime.now(),
            "config": extra_config
        }
        
        # Call callback di main thread
        if self.callback:
            self.callback(event)
    
    def read_trigger_value(self, address_config):
        """Baca nilai trigger saat ini"""
        if not self.plc_client or not self.plc_client.connected:
            return None
        
        area_type = address_config.get("area_type", "DM")
        address = address_config.get("address", 0)
        bit = address_config.get("bit")
        
        success, data = self.plc_client.read_memory(area_type, address, 1)
        
        if not success or not data:
            return None
        
        word_value = data[0] if data else 0
        
        if bit is not None and bit >= 0:
            return (word_value >> bit) & 1
        
        return word_value