# import subprocess
#
# from flask import Blueprint, request, jsonify, redirect, url_for
# from flask_login import login_required
# # import serial.tools.list_ports
# # from serial import Serial
#
# from web_interface.arduino import arduino   # shared ArduinoDevice instance
#
# settings = Blueprint('settings', __name__)
#
#
# @settings.route('/arduino/connect', methods=['POST'])
# @login_required
# def arduino_connect():
#     action = request.form.get('action')
#
#     if action == 'updateList':
#         # ports    = serial.tools.list_ports.comports()
#         names    = [p.description for p in ports]
#         selected = 0
#         # for i, p in enumerate(ports):
#             if 'Arduino' in p.description or 'USB' in p.description:
#                 selected = i
#                 break
#         return jsonify({'status': 'OK', 'ports': names, 'portSelect': selected})
#
#     elif action == 'reconnect':
#         if arduino.is_connected():
#             arduino.disconnect()
#             return jsonify({'status': 'OK', 'arduino': 'Disconnected'})
#
#         port = request.form.get('port')
#         if not port or not port.isdigit():
#             return jsonify({'status': 'Error', 'msg': 'Invalid port'})
#
#         devices = [p.device for p in serial.tools.list_ports.comports()]
#         idx     = int(port)
#         if idx >= len(devices):
#             return jsonify({'status': 'Error', 'msg': 'Port index out of range'})
#
#         try:
#             ser = Serial(devices[idx], 115200)
#             ser.flushInput()
#             ser.close()
#             arduino.connect(devices[idx])
#             return jsonify({'status': 'OK', 'arduino': 'Connected'})
#         except Exception as e:
#             return jsonify({'status': 'Error', 'msg': str(e)})
#
#     return jsonify({'status': 'Error', 'msg': 'Unknown action'})
#
#
# @settings.route('/arduino/status', methods=['POST'])
# @login_required
# def arduino_status():
#     if not arduino.is_connected():
#         return jsonify({'status': 'Error', 'msg': 'Arduino not connected'})
#     level = arduino.battery_level
#     if level is None:
#         return jsonify({'status': 'Info', 'msg': 'No battery data yet'})
#     return jsonify({'status': 'OK', 'battery': level})
#
#
# @settings.route('/mode', methods=['POST'])
# @login_required
# def mode():
#     """Switch between auto animation mode and manual servo mode."""
#     val = request.form.get('value')
#     if not arduino.is_connected():
#         return jsonify({'status': 'Error', 'msg': 'Arduino not connected'})
#     arduino.send("M" + str(val))
#     return jsonify({'status': 'OK'})
#
#
# @settings.route('/motor/offset', methods=['POST'])
# @login_required
# def motor_offset():
#     deadzone = request.form.get('motorOff')
#     steer    = request.form.get('steerOff')
#     if not arduino.is_connected():
#         return jsonify({'status': 'Error', 'msg': 'Arduino not connected'})
#     if deadzone:
#         arduino.send("O" + str(deadzone))
#     if steer:
#         arduino.send("S" + str(steer))
#     return jsonify({'status': 'OK'})
#
#
# @settings.route('/shutdown', methods=['POST'])
# @login_required
# def shutdown():
#     subprocess.run(['sudo', 'nohup', 'shutdown', '-h', 'now'], stdout=subprocess.PIPE)
#     return jsonify({'status': 'OK'})
#
#
# @settings.route('/restart', methods=['POST'])
# @login_required
# def restart():
#     subprocess.Popen("sleep 5 && sudo systemctl restart walle", shell=True)
#     return redirect(url_for('auth.login'))