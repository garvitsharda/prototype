from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

# -------------------------
# Load .env file
# -------------------------
load_dotenv()  # <- loads MONGO_URI and HF_TOKEN into os.environ

MONGO_URI = os.environ.get("MONGO_URI")
HF_TOKEN = os.environ.get("HF_TOKEN")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env")

# -------------------------
# MongoDB Setup
# -------------------------
client = MongoClient(MONGO_URI)
db = client["enterprise_knowledge"]
col = db["context_store"]

print("Connected to MongoDB Atlas")

# -------------------------
# Hugging Face Setup
# -------------------------
hf_client = InferenceClient(token=HF_TOKEN)
MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324:cheapest"

def call_hf_chat(prompt_text):
    try:
        response = hf_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error from HuggingFace API: {str(e)}"

# -------------------------
# Flask App
# -------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # Make sure this file exists in 'templates' folder

@app.route("/chat", methods=["POST"])
def chat():
    user_question = request.json.get("question", "").strip()
    if not user_question:
        return jsonify({"answer": "Please ask a valid question."})

    # Search in MongoDB (first by text index, fallback to regex)
    results = list(col.find({"$text": {"$search": user_question}}).limit(3))
    if not results:
        results = list(col.find({"content": {"$regex": user_question, "$options": "i"}}).limit(3))

    context = " ".join([r.get("content", "") for r in results])
    if not context.strip():
        context = "No relevant information found in the database."

    prompt_text = f"""
Answer the following question using ONLY the context below.
Context:
{context}

Question: {user_question}
"""

    answer = call_hf_chat(prompt_text)
    return jsonify({"answer": answer})

# -------------------------
# Run Flask
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # use Render's PORT if available
    app.run(host="0.0.0.0", port=port)
