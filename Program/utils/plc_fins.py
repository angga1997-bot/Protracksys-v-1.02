"""
utils/plc_fins.py - Komunikasi PLC FINS TCP/IP
"""

import socket
from config import PLC_MEMORY_AREAS


class FINSCommand:
    """FINS Command codes"""
    MEMORY_READ = 0x0101
    MEMORY_WRITE = 0x0102


class PLCFinsClient:
    """Client untuk komunikasi FINS TCP/IP"""
    
    def __init__(self, config):
        self.config = config
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Membuat koneksi ke PLC"""
        try:
            conn = self.config.get("connection", {})
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(conn.get("timeout", 5))
            self.socket.connect((conn.get("plc_ip", "192.168.1.1"), conn.get("plc_port", 9600)))
            
            self.connected = True
            return True, "Koneksi berhasil"
                
        except socket.timeout:
            return False, "Connection timeout"
        except socket.error as e:
            return False, f"Socket error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def disconnect(self):
        """Menutup koneksi"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connected = False
    
    def read_memory(self, area_type, start_address, length):
        """Membaca memory dari PLC"""
        if not self.connected:
            return False, "Tidak terhubung ke PLC"
        
        return False, "Not implemented yet"
    
    def test_connection(self):
        """Test koneksi ke PLC"""
        success, message = self.connect()
        if success:
            self.disconnect()
        return success, message