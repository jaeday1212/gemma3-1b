import requests
import json
import os
import time

# These are the sockets of each container that I'm going to deploy.
api_endpoints = {
    "promptimizer_granite": "http://promptimizer-service:11434/api/generate",
    "llama": "http://llama-service:11434/api/generate",
    "qwen": "http://qwen-service:11434/api/generate",
    "qwen_small": "http://qwen-small-service:11434/api/generate",
    "judge": "http://judge-service:11434/api/generate",
}

# These are the models I'm using to execute the workflow
models = {
    "promptimizer": "granite4:350m",
    "llama": "llama3.2:1b-instruct-q4_0",
    "qwen": "qwen2.5-coder:1.5b-instruct-q4_0",
    "qwen_small": "qwen3:0.6b",
    "judge": "gemma3:1b"
}

SERVICE_MAX_RETRIES = int(os.getenv("SERVICE_MAX_RETRIES", "10"))
SERVICE_RETRY_DELAY = float(os.getenv("SERVICE_RETRY_DELAY", "6"))
SERVICE_TIMEOUT = float(os.getenv("SERVICE_TIMEOUT", "30"))


def post_with_retries(endpoint, payload):
    last_error = None
    for attempt in range(1, SERVICE_MAX_RETRIES + 1):
        try:
            response = requests.post(endpoint, json=payload, timeout=SERVICE_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            last_error = error
            if attempt == SERVICE_MAX_RETRIES:
                break
            print(f"[wait] {endpoint} not ready (attempt {attempt}/{SERVICE_MAX_RETRIES}): {error}. Retrying in {SERVICE_RETRY_DELAY}s...")
            time.sleep(SERVICE_RETRY_DELAY)

    raise Exception(f"Service {endpoint} unreachable after {SERVICE_MAX_RETRIES} attempts: {last_error}")

def promptimizer(user_input):
    promptimizer_prompt = f"""
    Take {user_input} and rewrite it into a more concise query. The goal is to provide AI systems with a clear, 
    focused prompt for optimal interpretation and response. Only respond with the re-written query."""

    json_promptimizer = {
        "model": models["promptimizer"],
        "prompt": promptimizer_prompt,
        "stream": False
    }

    try:
        response_promptimizer = post_with_retries(api_endpoints["promptimizer_granite"], json_promptimizer)
        message_promptimizer = response_promptimizer["response"]
        return message_promptimizer
    except Exception as error:
        raise Exception(f"Promptimizer failed: {error}")


llama_logfile = []
qwen_logfile = []
qwen_small_logfile = []


def send_message_models(user_input):

    optimized_prompt = promptimizer(user_input)

    json_qwen_small = {
        "model": models["qwen_small"],
        "prompt": optimized_prompt,
        "stream": False
    }
    
    json_llama = {
        "model": models["llama"],
        "prompt": optimized_prompt,
        "stream": False
    }

    json_qwen = {
        "model": models["qwen"],
        "prompt": optimized_prompt,
        "stream": False
    }


    try:
        response_qwen_small = post_with_retries(api_endpoints["qwen_small"], json_qwen_small)
        message_qwen_small = response_qwen_small["response"]
        qwen_small_logfile.append({"role": "assistant", "content": message_qwen_small})

        response_llama = post_with_retries(api_endpoints["llama"], json_llama)
        message_llama = response_llama["response"]
        llama_logfile.append({"role": "assistant", "content": message_llama})

        response_qwen = post_with_retries(api_endpoints["qwen"], json_qwen)
        message_qwen = response_qwen["response"]
        qwen_logfile.append({"role": "assistant", "content": message_qwen})

        return message_qwen_small, message_llama, message_qwen
    
    except Exception as error:
        raise Exception(f"Model fan-out failed: {error}")
    

def make_judgement(user_input):

    judge_prompt = f"""
    User query: {user_input}

    qwen_small answer: {qwen_small_logfile[-1]['content']}
    LLaMA answer: {llama_logfile[-1]['content']}
    Qwen answer: {qwen_logfile[-1]['content']}

    Choose the best answer based on correctness, completeness, clarity, and usefulness.
    Return the contents of the best answer, nothing else.
    """

    
    json_judge = {
        "model": models["judge"],
        "prompt": judge_prompt,
        "stream": False
    }

    try:
        response = post_with_retries(api_endpoints["judge"], json_judge)
        message_judge = response["response"]
        return str(message_judge)
    
    except Exception as error:
        raise Exception(f"Judge failed: {error}")

print("Chatting with gorkheavy-lite! (type 'exit' to quit)")

while True:

    user_input = input("YOU: ").strip()

    if user_input.lower() == "exit":
        print("Bye!")
        break

    try:
        send_message_models(user_input)
        reply = make_judgement(user_input)
        print(f"Reply: {reply}\n")
    except Exception as failed:
        print(f"Error: {failed}")



