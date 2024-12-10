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
