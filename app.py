from flask import Flask, render_template, request, jsonify
import json
import subprocess
import re
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_metrics', methods=['POST'])
def submit_metrics():
    data = request.json
    active_metrics = data.get('activeMetrics', {})
    print("Received Metrics:")
    for key, value in active_metrics.items():
        print(f"{key}: {value}")

    # Save to disk
    with open('metrics_data.json', 'w') as file:
        json.dump(active_metrics, file)

    ens35_reset_cmd = "sudo tc qdisc del dev ens35 root"
    ens35_cmd = f"""sudo tc qdisc add dev ens35 root netem rate {active_metrics['ens35-slider-bandwidth']}mbit loss {active_metrics['ens35-slider-packet-loss']}% corrupt {active_metrics['ens35-slider-packet-corruption']}% delay {active_metrics['ens35-slider-base-latency']}ms {active_metrics['ens35-slider-latency-jitter']}ms 25%"""
    
    ens36_reset_cmd = "sudo tc qdisc del dev ens36 root"
    ens36_cmd = f"""sudo tc qdisc add dev ens36 root netem rate {active_metrics['ens36-slider-bandwidth']}mbit loss {active_metrics['ens36-slider-packet-loss']}% corrupt {active_metrics['ens36-slider-packet-corruption']}% delay {active_metrics['ens36-slider-base-latency']}ms {active_metrics['ens36-slider-latency-jitter']}ms 25%"""

    # Running the commands
    subprocess.run(ens35_reset_cmd, shell=True)
    subprocess.run(ens35_cmd, shell=True)
    subprocess.run(ens36_reset_cmd, shell=True)
    subprocess.run(ens36_cmd, shell=True)

    # Return the same data for frontend
    return jsonify(active_metrics)

@app.route('/save_default', methods=['POST'])
def save_default():
    data = request.json
    default_metrics = data.get('defaultMetrics', {})
    print("Saving Default Metrics:")
    for key, value in default_metrics.items():
        print(f"{key}: {value}")

    # Save to disk
    with open('default_data.json', 'w') as file:
        json.dump(default_metrics, file)

    return jsonify({"message": "Default metrics saved successfully"})

@app.route('/get_metrics_data', methods=['GET'])
def get_metrics_data():
    try:
        with open('metrics_data.json', 'r') as file:
            metrics_data = json.load(file)
            return jsonify(metrics_data)
    except FileNotFoundError:
        return jsonify({"error": "Metrics data not found"}), 404

@app.route('/get_default_metrics', methods=['GET'])
def get_default_metrics():
    try:
        with open('default_data.json', 'r') as file:
            default_metrics = json.load(file)
            return jsonify(default_metrics)
    except FileNotFoundError:
        return jsonify({"error": "Default metrics not found"}), 404

@app.route('/network-status')
def network_status():
    # Run the ifconfig command and capture its output
    result = subprocess.run(['ifconfig'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')

    # Function to check the connection status of a network interface
    def check_connection(interface):
        # Use regular expressions to check if the interface is mentioned in the output
        if re.search(f'^{interface}:', output, re.MULTILINE):
            return "connected"
        else:
            return "not connected"

    # Check the status of ens35 and ens36
    ens35_status = check_connection('ens35')
    ens36_status = check_connection('ens36')

    # Return the status as a JSON response
    return {"ens35": ens35_status, "ens36": ens36_status}

def execute_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
        print(f"Executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")

def check_interface_exists(interface):
    result = subprocess.run(f"ifconfig {interface}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def check_bridge_contains_interfaces():
    result = subprocess.run("brctl show", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode()
    return 'ens35' in output and 'ens36' in output

@app.route('/reticulating_spines')
def reticulating_spines():
    if check_bridge_contains_interfaces():
        print("skipping")
        return {"status": "ens35 and ens36 already in bridge, skipping"}

    commands = [
        "sudo ifconfig ens35 up",
        "sudo ifconfig ens36 up"
    ]

    if not check_interface_exists("br0"):
        commands.extend([
            "sudo ip link add br0 type bridge",
            "sudo ip link set br0 up",
            "sudo ip link set dev ens35 master br0",
            "sudo ip link set dev ens36 master br0",
            "sudo dhclient br0"
        ])

    commands.extend([
            "sudo brctl addif br0 ens35",
            "sudo brctl addif br0 ens36"
        ])

    for cmd in commands:
        execute_command(cmd)

    time.sleep(5)  # Simulate a delay
    return {"status": "completed"}

if __name__ == '__main__':
    app.run(debug=True)
