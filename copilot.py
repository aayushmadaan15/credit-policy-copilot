# ─────────────────────────────────────────────────────────────
# RAG Credit Policy Copilot
# Stack: Python + ChromaDB + OpenAI Embeddings + Claude API
# ─────────────────────────────────────────────────────────────

import os
import chromadb
from docx import Document
from openai import OpenAI
from anthropic import Anthropic
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─── YOUR API KEYS ───────────────────────────────────────────
import os
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
POLICY_FILE   = "Personal_Loan_Credit_Policy.docx"

# ─── INITIALISE CLIENTS ──────────────────────────────────────
openai_client    = OpenAI(api_key=OPENAI_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
chroma_client    = chromadb.Client()

print("\n╔══════════════════════════════════════════╗")
print("║     RAG Credit Policy Copilot v1.0       ║")
print("║     Zenith Finserv — Personal Loan        ║")
print("╚══════════════════════════════════════════╝\n")


# ─────────────────────────────────────────────────────────────
# STEP 1: READ THE POLICY DOCUMENT
# What's happening: We open the .docx and extract all text
# ─────────────────────────────────────────────────────────────
print("[ Step 1 ] Reading policy document...")

doc = Document(POLICY_FILE)
paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
full_text = "\n".join(paragraphs)

print(f"           ✓ Document loaded — {len(full_text)} characters, {len(paragraphs)} paragraphs")


# ─────────────────────────────────────────────────────────────
# STEP 2: CHUNK THE DOCUMENT
# What's happening: We split the policy into smaller pieces
# so each chunk covers one topic. Overlap ensures context
# isn't lost at chunk boundaries.
# ─────────────────────────────────────────────────────────────
print("[ Step 2 ] Chunking document...")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,       # ~2-3 sentences per chunk
    chunk_overlap=60,     # overlap so context isn't lost at edges
    separators=["\n\n", "\n", ".", " "]
)
chunks = splitter.split_text(full_text)

print(f"           ✓ {len(chunks)} chunks created")
print(f"           Sample chunk 1: {chunks[0][:80]}...")


# ─────────────────────────────────────────────────────────────
# STEP 3: CREATE EMBEDDINGS + STORE IN VECTOR DATABASE
# What's happening: Each chunk is converted into a vector
# (list of numbers representing meaning) using OpenAI's
# embedding model. These vectors are stored in ChromaDB.
# ─────────────────────────────────────────────────────────────
print("[ Step 3 ] Creating embeddings and storing in ChromaDB...")
print("           (This calls the OpenAI API once per chunk)")

# Create a collection in ChromaDB — like a table in a database
collection = chroma_client.create_collection(name="credit_policy")

for i, chunk in enumerate(chunks):
    # Convert chunk text → vector using OpenAI
    response = openai_client.embeddings.create(
        input=chunk,
        model="text-embedding-3-small"  # cheapest, very good
    )
    vector = response.data[0].embedding

    # Store in ChromaDB: the vector + original text + an ID
    collection.add(
        ids=[f"chunk_{i}"],
        embeddings=[vector],
        documents=[chunk]
    )
    print(f"           Embedded chunk {i+1}/{len(chunks)}", end="\r")

print(f"\n           ✓ All {len(chunks)} chunks embedded and stored in ChromaDB")


# ─────────────────────────────────────────────────────────────
# STEP 4: QUERY FUNCTION
# What's happening: When user asks a question —
# 1. Question is converted to a vector (same model)
# 2. ChromaDB finds the 3 most similar vectors
# 3. Those chunks are passed to Claude with the question
# 4. Claude answers using ONLY those chunks
# ─────────────────────────────────────────────────────────────

def query_copilot(question):
    print(f"\n{'─'*50}")
    print(f"Query: {question}")
    print(f"{'─'*50}")

    # Convert question to vector
    print("\n[ Retrieve ] Converting query to embedding...")
    q_response = openai_client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    )
    query_vector = q_response.data[0].embedding

    # Find most similar chunks in ChromaDB
    print("[ Retrieve ] Searching vector database...")
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=3
    )

    retrieved_chunks = results['documents'][0]
    distances = results['distances'][0]

    print(f"[ Retrieve ] ✓ Top 3 chunks retrieved:")
    for i, (chunk, dist) in enumerate(zip(retrieved_chunks, distances)):
        print(f"             Chunk {i+1} (similarity: {round(1-dist, 3)}): {chunk[:70]}...")

    # Build context from retrieved chunks
    context = "\n\n".join([f"[Policy Section {i+1}]\n{chunk}"
                           for i, chunk in enumerate(retrieved_chunks)])

    # Send to Claude with strict grounding instructions
    print("\n[ Generate ] Sending to Claude with policy context...")

    message = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        system="""You are a credit policy assistant for Zenith Finserv Private Limited.

Rules you must follow:
1. Answer ONLY using the provided policy context. Never use outside knowledge.
2. Always mention which policy section supports your answer.
3. If the answer is not in the context, say: "This is not covered in the current policy document."
4. For eligibility questions, start with a clear verdict: ELIGIBLE / NOT ELIGIBLE / CONDITIONAL.
5. Be precise with numbers — FOIR, income limits, age limits, scores.
6. Keep answers concise and underwriter-friendly.""",

        messages=[{
            "role": "user",
            "content": f"Policy Context:\n{context}\n\nUnderwriter Question: {question}"
        }]
    )

    answer = message.content[0].text

    print("\n[ Answer ]\n")
    print(answer)
    return answer


# ─────────────────────────────────────────────────────────────
# STEP 5: INTERACTIVE LOOP
# Ask questions until you type 'exit'
# ─────────────────────────────────────────────────────────────
print("\n\n✓ Copilot ready. Type your question or 'exit' to quit.\n")

while True:
    user_input = input("\nUnderwriter > ").strip()
    if user_input.lower() in ['exit', 'quit', 'q']:
        print("\nSession ended.")
        break
    if not user_input:
        continue
    query_copilot(user_input)