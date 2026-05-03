from collections import deque
import threading
from flask import Blueprint, request, jsonify

pi_bridge = Blueprint('pi_bridge', __name__)

command_queue = deque()
queue_lock = threading.Lock()

def push_command(cmd: dict):
    with queue_lock:
        command_queue.append(cmd)

@pi_bridge.route('/next_command', methods=['GET'])
def next_command():
    with queue_lock:
        if command_queue:
            return jsonify(command_queue.popleft())
    return jsonify({"type": "idle"})

@pi_bridge.route('/voice_answer', methods=['POST'])
def voice_answer():
    data = request.get_json()
    answer = data.get("text", "")
    # pass answer to your existing AI code here
    return jsonify({"status": "OK"})