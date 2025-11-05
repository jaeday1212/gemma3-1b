import requests 
import json

ollama_url = "http://127.0.0.1:11434/api/chat"
model = "gemma3-1b"
logfile = []

def send_message(user_input):
    json_payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_input}],
        "stream": False
    }

    try:
        send_input = requests.post(ollama_url, json=json_payload)
        send_input.raise_for_status()
        response = send_input.json()
        
        if "message" in response:
            message = response["message"]["content"]
        else:
            message = response.get("response", "No response received")
            
        logfile.append({"role": "assistant", "content": message})
        return message
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to communicate with Ollama: {str(e)}")

def main():
    print("Chatting with Ollama (type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        try:
            reply = send_message(user_input)
            print(f"Gemma: {reply}\n")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()



