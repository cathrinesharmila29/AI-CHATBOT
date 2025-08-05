%%writefile vicky.py
import streamlit as st
import subprocess
import os
import json
import requests

# --- Helper functions for Streamlit ---
def install_ollama():
    """Installs Ollama. Handles potential errors and displays status in Streamlit."""
    try:
        st.sidebar.info("🔄 Installing Ollama...")
        subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], shell=True, check=True, capture_output=True, text=True)
        st.sidebar.success("✅ Ollama installed successfully!")
    except subprocess.CalledProcessError as e:
        st.sidebar.error(f"❌ Error installing Ollama: {e.stderr}")
        st.stop()
    except Exception as e:
        st.sidebar.error(f"⚠️ An unexpected error occurred during Ollama installation: {e}")
        st.stop()


def load_ollama_model(model_name):
    """Loads the specified Ollama model. Handles errors and displays status in Streamlit."""
    try:
        st.sidebar.info(f"🚀 Loading model '{model_name}'...")
        subprocess.run(["ollama", "pull", model_name], check=True, capture_output=True, text=True)
        st.sidebar.success(f"✅ Model '{model_name}' loaded successfully!")
    except subprocess.CalledProcessError as e:
        st.sidebar.error(f"❌ Error loading model '{model_name}': {e.stderr}")
        st.stop()
    except Exception as e:
        st.sidebar.error(f"⚠️ An unexpected error occurred while loading the model: {e}")
        st.stop()


def chat_with_deepseek(model="deepseek-r1:1.5b", max_words=400, prompt=""):
    """
    Chats with a DeepSeek model using the Ollama API with streaming,
    limiting the output to a maximum number of words and ensuring responses are in English.
    """
    try:
        url = "http://localhost:11434/api/generate"
        system_prompt = "Respond only in English."
        data = {
            "prompt": f"{system_prompt}\n{prompt}",
            "model": model,
            "stream": True,
        }
        response = requests.post(url, json=data, stream=True)

        if response.status_code == 200:
            full_response = ""
            output_area = st.empty()
            for line in response.iter_lines():
                if line:
                    try:
                        json_data = json.loads(line.decode('utf-8'))
                        chunk = json_data.get('response', '')
                        full_response += chunk
                        output_area.write(full_response)
                    except json.JSONDecodeError:
                        print(f"⚠️ Error decoding JSON: {line}")
            words = full_response.split()
            return " ".join(words[:max_words]).strip()
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"⚠️ An error occurred: {e}")
        return None

# --- Streamlit App ---
st.title("🤖 Dynamic FAQ Generator")
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "current_response" not in st.session_state:
    st.session_state["current_response"] = ""

try:
    subprocess.run(["ollama", "-v"], check=True, capture_output=True)
except FileNotFoundError:
    install_ollama()
except subprocess.CalledProcessError:
    install_ollama()

model_name = st.sidebar.text_input("🧠 Model Name (e.g., deepseek-r1:1.5b):", "deepseek-r1:1.5b")
load_ollama_model(model_name)

max_words = st.sidebar.number_input("🔡 Maximum Response Words:", min_value=50, max_value=500, value=200, step=50)

uploaded_file = st.file_uploader("📂 Upload a text file", type=["txt"])
file_content = ""
if uploaded_file is not None:
    try:
        file_content = uploaded_file.read().decode("utf-8")
        st.success("✅ File uploaded successfully!")
    except Exception as e:
        st.error(f"❌ Error reading uploaded file: {e}")

prompt = st.text_area("💬 Enter your query:", "")

full_prompt = f"📖 Context from uploaded file:\n{file_content}\n\n💭 User Query:\n{prompt}" if file_content else prompt

if st.button("🚀 Get Response"):
    if full_prompt:
        with st.spinner("🔍 Generating response..."):
            response = chat_with_deepseek(model=model_name, max_words=max_words, prompt=full_prompt)
        if response:
            st.session_state["chat_history"].append({"prompt": full_prompt, "response": response})
            st.session_state["current_response"] = response
        else:
            st.error("❌ Failed to get a response from the model.")
    else:
        st.warning("⚠️ Please enter a query or upload a file.")

if st.button("🧹 Clear Response"):
    st.session_state["current_response"] = ""

st.subheader("📜 Chat History")
for chat in reversed(st.session_state["chat_history"]):
    st.markdown(f"👤 **You:** {chat['prompt']}")
    st.markdown(f"🤖 **DeepSeek:** {chat['response']}")
    st.markdown("---")

if st.button("🗑️ Clear Chat History"):
    st.session_state["chat_history"] = []
