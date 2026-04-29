from flask import Blueprint, request, jsonify
from flask_login import login_required

from web_interface.arduino import arduino   # shared ArduinoDevice instance

control = Blueprint('control', __name__)


@control.route('/motor', methods=['POST'])
@login_required
def motor():
    x = request.form.get('stickX')
    y = request.form.get('stickY')
    if x is None or y is None:
        return jsonify({'status': 'Error', 'msg': 'Missing data'})
    if not arduino.is_connected():
        return jsonify({'status': 'Error', 'msg': 'Arduino not connected'})
    arduino.send("X" + str(int(float(x) * 100)))
    arduino.send("Y" + str(int(float(y) * 100)))
    return jsonify({'status': 'OK'})


@control.route('/servoControl', methods=['POST'])
@login_required
def servoControl():
    code  = request.form.get('servo')
    value = request.form.get('value')
    if code is None or value is None:
        return jsonify({'status': 'Error', 'msg': 'Missing data'})
    if not arduino.is_connected():
        return jsonify({'status': 'Error', 'msg': 'Arduino not connected'})
    arduino.send(code + str(value))
    return jsonify({'status': 'OK'})


@control.route('/tts', methods=['POST'])
@login_required
def tts():
    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({'status': 'Error', 'msg': 'No text'})
    return jsonify({'status': 'OK'})