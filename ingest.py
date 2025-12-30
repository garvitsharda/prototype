from pymongo import MongoClient
from docx import Document
from dotenv import load_dotenv
import os

# ---------------------------
# Load .env
# ---------------------------
load_dotenv()   # automatically reads .env file in the same folder
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# ---------------------------
# MongoDB Connection
# ---------------------------
client = MongoClient(MONGO_URI)
db = client["enterprise_knowledge"]      # Database name
collection = db["context_store"]          # Collection name

print("Connected to MongoDB Atlas")

# ---------------------------
# Read DOCX file
# ---------------------------
doc = Document("reference_data/company.docx")

full_text = ""
for para in doc.paragraphs:
    if para.text.strip():
        full_text += para.text.strip() + " "

print(f"🔹 Total characters read: {len(full_text)}")
print(f"🔹 Total words: {len(full_text.split())}")

# ---------------------------
# Chunking (400 words)
# ---------------------------
words = full_text.split()
chunk_size = 400
count = 0

for i in range(0, len(words), chunk_size):
    chunk_text = " ".join(words[i:i + chunk_size])
    
    collection.insert_one({
        "title": f"Context_{i // chunk_size + 1}",
        "content": chunk_text,
        "source_file": "company.docx"
    })
    count += 1

print(f"Inserted {count} chunks into MongoDB Atlas")
