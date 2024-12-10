# README for Network Resilience Evaluation Tool

## Overview

This tool is designed to evaluate network resilience by simulating various network conditions on a portable device. It utilizes a Raspberry Pi to emulate network disruptions such as latency, jitter, packet loss, and bandwidth constraints. The device is equipped with a user-friendly touchscreen interface, making it accessible for users with varying levels of technical expertise.

## System Design

The interface of the tool is a web application developed using HTML and JavaScript for the front end, and Python Flask for the back end. The network disruption functionalities are achieved using a Linux library called “brctl”. Flask interacts with this library, allowing users to manage network settings directly through the web interface.

## Device Setup

1. **Install OS:** Install the 64-bit Raspberry Pi OS on your Raspberry Pi.
2. **Install Touchscreen:** Connect the official 7-inch Raspberry Pi touchscreen to your device.
3. **Download Source Code:** Use the following command in the terminal to clone the repository:
    ```bash
    git clone https://github.com/LeafmanZ/network-disruptor.git
    ```
    Alternatively, download and extract the 'network-disruptor' folder containing the source code.
4. **Install bridge-utils:** Install the `bridge-utils` package to manage network bridges:
    ```bash
    sudo apt install bridge-utils
    ```
5. **System Update and Upgrade:** Run the following commands in the terminal to update and upgrade your system:
    ```bash
    sudo apt update && sudo apt upgrade
    ```
6. **Install Pip:** Before installing Flask, ensure that `pip` is installed:
    ```bash
    sudo apt install python3-pip
    ```
7. **Install Flask:** Now, install Flask using `pip`:
    ```bash
    pip install flask
    ```
8. **Configure Startup Commands:**
    Open your cron table for editing by running:
    ```bash
    crontab -e
    ```
    Add the following lines at the end of the cron table, ensuring that you adjust the paths to match the location where the 'disrupt_app' folder is stored:
    ```cron
    @reboot sudo python /home/<username>/Desktop/disrupt_app/app.py
    @reboot bash /home/<username>/Desktop/disrupt_app/launch_chromium.sh
    ```
9. **Reboot Device:** Restart your Raspberry Pi to apply the changes:
    ```bash
    sudo reboot
    ```
10. **Verify Setup:** Upon reboot, you should see the menu appear on the screen.
11. **Connect Ethernet Adapters:** Plug in two USB-to-Ethernet adapters into your Raspberry Pi. You should then see the status checks for `eth1` and `eth2` resolve.

## Operation

### Initial Setup

1. **Power On:** Turn on the Raspberry Pi device which is equipped with a touchscreen.
2. **Connect Adapters:** Attach two USB-to-Ethernet adapters to the Raspberry Pi.
3. **Adapter Recognition:** Upon connection, the interface will recognize the Ethernet adapters and display their status. Flask then automatically configures a bridge between the two Ethernet ports using “brctl”.

### Integration into Network

1. **Disconnect Existing Connection:** Remove an Ethernet cable from its original socket and connect it to one of the Raspberry Pi’s Ethernet ports.
2. **Establish New Connection:** Connect another Ethernet cable to the second Raspberry Pi port and plug it back into the original socket from which the first cable was disconnected.

This configuration allows network traffic to pass through the Raspberry Pi as if it were part of the network seamlessly.

### Network Manipulation

Through the touchscreen interface, users can manipulate sliders to adjust:
- **Latency**
- **Jitter**
- **Packet Loss**
- **Bandwidth Constraints**

These settings enable users to stress-test the network’s robustness under various conditions, assessing the network's resilience effectively.

## Conclusion

This tool provides a practical and efficient method for simulating network conditions and testing network resilience, suitable for use in diverse environments and applications.

from flask import Flask, request, jsonify
import ollama

def filter_agent_outputs(agent_function):
    new_agent_function = agent_function.replace('<|eom_id|>', '')
    return new_agent_function

available_agent_functions = """
You are an agent that selects pages based on their prompts by executing the most relevant function. The available pages are:

network-status-page: Use this function when the user inquires about network status. It returns the current health of the network infrastructure, including endpoint connectivity, but does not include information on data transfer health. Has no capabilities or functionalities.

transfer-configuration-page: Select this function when the prompt specifically involves questions or intentions regarding data movement, syncing, or transferring.

home-menu-page: Choose this function when the user seeks clarification on the system's knowledge and capabilities, or when the prompt does not align with any of the other specific functions. It provides a summary of all available knowledge, functionalities, and what you can do.

transfer-statistics-page: Use this function to summarize data transfer activities completed within a specified timeframe (default is the last 24 hours). It reports the total bytes transferred, the number of objects synced, and the counts of successful versus failed transfers.

transfer-status-history-page: This function is for prompts requesting details about the most recent or progress on ongoing data transfer or sync operation, including status, data moved, and source/destination information.

no-relevant-page: This function should be selected when the prompt is not related to network status, data transfer, or synchronization operations. This function is for prompts that do not fit into any of the other specific categories.

Given a user prompt, select and execute the most relevant function from the list above to obtain the necessary data. Respond only with the function name. Do not provide explanations.
"""

def generate_agent_function(user_prompt):
    agent_function_raw = ollama.chat(
        model='llama3.1:8b',
        options={
            'num_predict': 40,
        },
        messages=[{'role': 'tool', 'name': 'available_agent_functions', 'content': available_agent_functions},
                  {'role': 'user', 'content': user_prompt}],
        stream=False,
    )

    agent_function_filtered = filter_agent_outputs(agent_function_raw['message']['content'])
    print(f'Agent function filtered: {agent_function_filtered}')

    agent_function_good = False
    for available_function in ['network-status-page', 'transfer-configuration-page', 'home-menu-page', 'transfer-statistics-page', 'transfer-status-history-page']:
        if available_function in agent_function_filtered and len(agent_function_filtered) <= 30:
            agent_function_good = True
            break

    if agent_function_good:
        agent_function = agent_function_filtered
    else:
        agent_function = "home-menu-page"

    print(f'\nAgent function: {agent_function}')

    return agent_function

app = Flask(__name__)

@app.route('/process-prompt', methods=['POST'])
def process_prompt():
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Invalid request. Please provide a "prompt" field.'}), 400

        user_prompt = data['prompt']
        agent_function = generate_agent_function(user_prompt)

        return jsonify({'agent_function': agent_function})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = 5000
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
