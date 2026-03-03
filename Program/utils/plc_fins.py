"""
utils/plc_fins.py - Komunikasi PLC FINS TCP/IP (Omron)

Menggunakan library 'fins' (pip install fins) oleh Joseph Ryan
GitHub: https://github.com/aphyt/omron_fins

Wrapper ini menyesuaikan interface fins.TCPFinsConnection
dengan interface PLCFinsClient yang digunakan di seluruh aplikasi.
"""

import struct
import sys
import os

# Tambahkan site-packages yang mungkin berbeda (system venv)
_SYSTEM_VENV = r"C:\Users\jk2161203\Documents\D-CONDA\d-conda\venv\Lib\site-packages"
if _SYSTEM_VENV not in sys.path and os.path.isdir(_SYSTEM_VENV):
    sys.path.insert(0, _SYSTEM_VENV)

try:
    from fins.tcp import TCPFinsConnection
    from fins.fins_common import FinsPLCMemoryAreas
    _FINS_LIB_AVAILABLE = True
except ImportError:
    _FINS_LIB_AVAILABLE = False


# ─── Memory area code mapping ──────────────────────────────────────
# Maps config string (e.g. "DM") → fins library attribute name
_AREA_MAP = {
    "DM":  "DATA_MEMORY_WORD",   # 0x82
    "CIO": "CIO_WORD",           # 0xB0
    "WR":  "WORK_WORD",          # 0xB1
    "HR":  "HOLDING_WORD",       # 0xB2
    "AR":  "AUXILIARY_WORD",     # 0xB3
}

from config import PLC_MEMORY_AREAS  # fallback area codes


# ─── Main Client Class ─────────────────────────────────────────────
class PLCFinsClient:
    """
    Wrapper yang menyatukan interface fins.TCPFinsConnection
    dengan interface yang digunakan di dashboard, trigger, dan settings.
    """

    def __init__(self, config: dict):
        self.config    = config
        self.connected = False
        self._conn     = None          # TCPFinsConnection instance

    # ---------------------------------------------------------------
    def connect(self) -> tuple:
        """
        Buka koneksi TCP ke PLC dan lakukan FINS handshake.

        Returns:
            (True,  info_str)   on success
            (False, error_str)  on failure
        """
        conn_cfg = self.config.get("connection", {})
        ip       = conn_cfg.get("plc_ip",   "192.168.1.1")
        port     = int(conn_cfg.get("plc_port", 9600))
        timeout  = conn_cfg.get("timeout", 5)

        if not _FINS_LIB_AVAILABLE:
            # Fallback: use our own raw FINS/TCP implementation
            return self._connect_raw(ip, port, timeout)

        try:
            self._conn = TCPFinsConnection()
            self._conn.fins_socket.settimeout(timeout)
            self._conn.connect(ip_address=ip, port=port, bind_port=0)
            self.connected = True
            src = self._conn.srce_node_add
            dst = self._conn.dest_node_add
            return True, (
                f"Connected to {ip}:{port} "
                f"(src_node={src}, dst_node={dst})"
            )
        except Exception as e:
            self._conn = None
            self.connected = False
            return False, f"Connection failed: {e}"

    # ---------------------------------------------------------------
    def disconnect(self):
        """Tutup koneksi."""
        self.connected = False
        if self._conn:
            try:
                self._conn.fins_socket.close()
            except Exception:
                pass
            self._conn = None

    # ---------------------------------------------------------------
    def read_memory(self, area_type: str, start_address: int, length: int) -> tuple:
        """
        Baca 'length' words dari memori PLC.

        Returns:
            (True,  [int, int, ...])   list of word values on success
            (False, error_str)         on failure
        """
        if not self.connected or self._conn is None:
            return False, "Not connected to PLC"

        if not _FINS_LIB_AVAILABLE:
            return self._read_memory_raw(area_type, start_address, length)

        # ── Get area code bytes from fins library ──────────────────
        attr_name = _AREA_MAP.get(area_type)
        if attr_name is None:
            return False, f"Unknown memory area: {area_type}"

        mem_areas  = FinsPLCMemoryAreas()
        area_bytes = getattr(mem_areas, attr_name)   # e.g. b'\x82' for DM

        # ── Build the beginning address (3 bytes: word_hi, word_lo, bit) ──
        begin_addr = start_address.to_bytes(2, 'big') + b'\x00'

        try:
            raw = self._conn.memory_area_read(
                memory_area_code  = area_bytes,
                beginning_address = begin_addr,
                number_of_items   = length
            )
        except Exception as e:
            self.connected = False
            return False, f"Read error: {e}"

        # ── Parse raw response ─────────────────────────────────────
        # raw = full FINS response frame bytes (returned by fins lib)
        # Layout: 10b header + 2b cmd + 2b end_code + 2*N word data
        if raw is None or len(raw) < 14:
            return False, f"Response too short or empty ({type(raw).__name__}: {raw!r})"

        # Check end code
        end_code = struct.unpack(">H", raw[12:14])[0]
        if end_code != 0x0000:
            return False, _fins_end_code_desc(end_code)

        word_bytes = raw[14:]
        num_words  = len(word_bytes) // 2

        if num_words == 0:
            return False, "PLC returned 0 words"

        words = [
            struct.unpack(">H", word_bytes[i*2 : i*2+2])[0]
            for i in range(min(num_words, length))
        ]
        return True, words

    # ---------------------------------------------------------------
    def test_connection(self) -> tuple:
        """Test koneksi saja (connect lalu disconnect)."""
        ok, msg = self.connect()
        if ok:
            self.disconnect()
        return ok, msg

    # ===================================================================
    # Raw FINS/TCP fallback (used when 'fins' library is not available)
    # ===================================================================

    def _connect_raw(self, ip, port, timeout):
        import socket as _sock
        try:
            s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            self._raw_socket = s

            # Handshake: magic + length(12) + cmd(0) + err(0) + node(0)
            hs = struct.pack(">4sIIII", b"FINS", 12, 0, 0, 0)
            s.sendall(hs)
            resp = self._recv_exact_raw(24)
            if resp is None or len(resp) < 24:
                s.close()
                return False, "Handshake failed"
            if resp[0:4] != b"FINS":
                s.close()
                return False, "Bad magic in handshake"
            err = struct.unpack(">I", resp[12:16])[0]
            if err != 0:
                s.close()
                return False, f"Handshake error 0x{err:08X}"
            self._client_node = struct.unpack(">I", resp[16:20])[0]
            self._server_node = struct.unpack(">I", resp[20:24])[0]
            self.connected = True
            return True, f"Connected (raw) to {ip}:{port}"
        except Exception as e:
            self.connected = False
            return False, str(e)

    def _recv_exact_raw(self, n):
        buf = b""
        while len(buf) < n:
            try:
                chunk = self._raw_socket.recv(n - len(buf))
            except Exception:
                return None
            if not chunk:
                return None
            buf += chunk
        return buf

    def _read_memory_raw(self, area_type, start_address, length):
        area_info = PLC_MEMORY_AREAS.get(area_type)
        if area_info is None:
            return False, f"Unknown area: {area_type}"
        area_code = area_info["code"]

        try:
            cn = getattr(self, "_client_node", 0) & 0xFF
            sn = getattr(self, "_server_node", 0) & 0xFF
            fins = bytearray([
                0x80, 0x00, 0x02,
                0x00, sn, 0x00,
                0x00, cn, 0x00, 0x00,
                0x01, 0x01,          # MRC SRC
                area_code & 0xFF,
            ])
            fins += struct.pack(">H", start_address)
            fins += b'\x00'
            fins += struct.pack(">H", length)

            pkt_len = 4 + 4 + len(fins)
            pkt = struct.pack(">4sIII", b"FINS", pkt_len, 2, 0) + bytes(fins)
            self._raw_socket.sendall(pkt)

            hdr = self._recv_exact_raw(16)
            if not hdr or hdr[0:4] != b"FINS":
                return False, "Bad response header"
            resp_len = struct.unpack(">I", hdr[4:8])[0]
            body = self._recv_exact_raw(resp_len - 8)
            if not body or len(body) < 14:
                return False, "Response too short"
            end_code = struct.unpack(">H", body[12:14])[0]
            if end_code != 0:
                return False, f"FINS error 0x{end_code:04X}"
            wd = body[14:]
            nw = len(wd) // 2
            return True, [struct.unpack(">H", wd[i*2:i*2+2])[0] for i in range(min(nw, length))]
        except Exception as e:
            self.connected = False
            return False, str(e)


# ─── Friendly FINS end-code descriptions ──────────────────────────
def _fins_end_code_desc(code: int) -> str:
    table = {
        0x0001: "Service cancelled",
        0x0101: "Area classification mismatch",
        0x0102: "Access size error",
        0x0103: "Address range exceeded",
        0x0104: "Address range specification error",
        0x0106: "Program missing",
        0x0201: "PLC in program mode",
        0x0202: "PLC in debug mode",
        0x0203: "PLC in monitor mode",
        0x0204: "PLC running",
        0x2201: "Unit error",
        0x2301: "Command too long",
        0x2302: "Command too short",
        0x2501: "Frame length error",
    }
    msg = table.get(code, f"Unknown FINS error")
    return f"FINS end code 0x{code:04X} – {msg}"