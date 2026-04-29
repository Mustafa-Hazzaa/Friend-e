import os
import time
import logging
from queue import Queue
from threading import Event, Thread
from venv import logger


# from serial import Serial
#
# logger = logging.getLogger(__name__)
#
#
# class ArduinoDevice:
#
#     def __init__(self):
#         self.queue         = Queue()
#         self.exit_flag     = Event()
#         self.port_name     = ""
#         self.serial_port   = None
#         self.serial_thread = None
#         self.battery_level = None
#         self.exit_flag.clear()
#
#     def connect(self, port) -> bool:
#         try:
#             self.disconnect()
#             self.serial_port = Serial(port, 115200)
#             self.serial_port.flushInput()
#             self.port_name = port
#             self.exit_flag.clear()
#             self.serial_thread = Thread(target=self._run, daemon=True)
#             self.serial_thread.start()
#         except Exception as e:
#             logger.error(f"Connect error: {e}")
#         return self.is_connected()
#
#     def disconnect(self) -> None:
#         self.battery_level = None
#         if self.serial_thread:
#             self.exit_flag.set()
#             self.serial_thread.join()
#             self.serial_thread = None
#         if self.serial_port:
#             self.serial_port.close()
#             self.serial_port = None
#
#     def is_connected(self) -> bool:
#         return bool(
#             self.serial_thread and self.serial_thread.is_alive() and
#             self.serial_port   and self.serial_port.is_open
#         )
#
#     def send(self, cmd: str) -> bool:
#         if self.is_connected():
#             self.queue.put(cmd)
#             return True
#         return False
#
#     def _run(self):
#         buf = ""
#         while not self.exit_flag.is_set():
#             try:
#                 if not self.queue.empty():
#                     self.serial_port.write((self.queue.get() + '\n').encode())
#                 while self.serial_port.in_waiting > 0:
#                     ch = self.serial_port.read().decode()
#                     if ch in ('\n', '\r'):
#                         self._parse(buf)
#                         buf = ""
#                     else:
#                         buf += ch
#             except Exception as e:
#                 logger.error(f"Serial error: {e}")
#             time.sleep(0.01)
#
#     def _parse(self, msg: str):
#         if "Battery" in msg:
#             parts = msg.split('_')
#             if len(parts) > 1 and parts[1].isdigit():
#                 self.battery_level = parts[1]

class MockArduinoDevice:

    def __init__(self):
        self.battery_level = "75"   # fake battery so the UI shows something

    def connect(self, port="") -> bool:
        logger.info(f"[MOCK] connect({port})")
        return True

    def disconnect(self) -> None:
        logger.info("[MOCK] disconnect")

    def is_connected(self) -> bool:
        return True

    def send(self, cmd: str) -> bool:
        logger.info(f"[MOCK] send → {cmd}")
        return True

    def _parse(self, msg): pass

arduino = MockArduinoDevice()\
    # if os.environ.get("MOCK_HARDWARE") else ArduinoDevice()