import os
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# ⚠️ REMINDER: Delete your old key on Groq Console and paste your NEW key below!
GROQ_API_KEY = "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"

# Initialize Groq client directly using your hardcoded mobile key string
client = Groq(api_key=GROQ_API_KEY)

# LLM Core Instructions and Memory Store
model_memory = [
    {
        "role": "system",
        "content": (
            "You are an autonomous AI playing inside Minecraft Bedrock edition v26.10 alongside the player.\n"
            "You receive two operational contexts:\n"
            "1. 'user_command': Direct text/orders from the player. Listen carefully, learn their habits, and help them.\n"
            "2. 'auto_tick': Context arrays sent every few seconds showing world time and location coordinates. Use these to make your own decisions independently (e.g. giving items, altering weather, spawning helpers, teleporting or checking in) when the player is busy.\n\n"
            "CRITICAL STRATAGEM: You must always respond with a clean, strict JSON map containing exactly two keys: 'reply' and 'command'.\n"
            "Example format:\n"
            "{\"reply\": \"I noticed it's night. Spawning protection!\", \"command\": \"summon iron_golem ~ ~ ~\"}\n"
            "If no active command is needed, leave the value empty: \"\"\n"
            "Do not output any markdown or conversational prose outside the raw JSON object structure."
        )
    }
]

@app.route('/chat', methods=['POST'])
def handle_game_packet():
    global model_memory
    packet_data = request.json
    
    execution_mode = packet_data.get("mode")
    actor = packet_data.get("player")
    content = packet_data.get("message")
    
    # Structure data feed based on communication type
    if execution_mode == "user_command":
        formatted_prompt = f"PLAYER INPUT DIRECTIVE from {actor}: {content}"
    else:
        formatted_prompt = f"SYSTEM ENVIRONMENTAL STREAM: {content}"
        
    model_memory.append({"role": "user", "content": formatted_prompt})
    
    # Enforce a sliding memory window limit to keep token consumption optimal
    if len(model_memory) > 30:
        model_memory = [model_memory[0]] + model_memory[-14:]
        
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192", # Llama 3.1 8B parameter optimization via Groq
            messages=model_memory,
            temperature=0.3,       # Keeping temperature down guarantees structured JSON compliance
            response_format={"type": "json_object"}
        )
        
        response_payload = chat_completion.choices[0].message.content
        model_memory.append({"role": "assistant", "content": response_payload})
        
        return response_payload, 200, {'Content-Type': 'application/json'}
        
    except Exception as error_context:
        print(f"Error compiling Groq Inference: {error_context}")
        return jsonify({"reply": "Core glitch detected.", "command": ""}), 500

if __name__ == '__main__':
    # 0.0.0.0 allows mobile localhost routing to communicate across apps easily
    app.run(host='0.0.0.0', port=5000, debug=False)
  
