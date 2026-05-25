# credit-policy-copilot
RAG-based credit policy assistant for NBFC underwriters — built with Python, ChromaDB, OpenAI embeddings, and Claude API
# Credit Policy Copilot

A RAG-based (Retrieval-Augmented Generation) assistant for NBFC underwriters — 
answers credit policy questions by retrieving relevant policy sections before 
generating a response. Built to explore how AI can assist regulated lending 
workflows without hallucinating on policy details.

---

## What it does

- Reads any NBFC credit policy document (.docx)
- Chunks and embeds it into a local vector database (ChromaDB)
- Converts underwriter queries into semantic embeddings
- Retrieves the 3 most relevant policy sections per query
- Passes retrieved context to Claude API for grounded answer generation
- Returns verdict (Eligible / Not Eligible / Conditional) for eligibility queries
- Refuses to answer out-of-scope queries — says "not in policy" instead of guessing

---

## Why this matters in lending

A standalone LLM answering credit policy questions will hallucinate — 
it blends policy norms from hundreds of NBFCs it has seen in training data. 
RAG grounds every answer in your specific policy document.

In a regulated lending context, this has two implications:

1. **Accuracy** — answers cite your policy, not industry averages
2. **Safety** — when a query isn't covered, the system says so explicitly 
   rather than fabricating a plausible-sounding answer

---

## Eval results — v1.0

| Query | Expected | Result |
|---|---|---|
| Max FOIR for salaried customer | 65% | ✅ Correct |
| Min CIBIL for self-employed | 720 | ✅ Correct |
| 60-yr self-employed eligibility | Eligible (policy: 25-65 yrs) | ✅ Correct |
| Write-off customer eligibility | Auto rejection | ✅ Correct |
| Prepayment penalty (not in doc) | Not covered in policy | ✅ Correct — no hallucination |
| FOIR calc: ₹50k income, ₹15k EMI | Conditional + ₹17,500 headroom | ✅ Correct reasoning |

**6/6 on initial eval suite. Zero hallucinations on out-of-scope queries.**

---

## Tech stack

| Component | Tool |
|---|---|
| Document parsing | python-docx |
| Text chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | OpenAI text-embedding-3-small |
| Vector database | ChromaDB (local) |
| Answer generation | Anthropic Claude API |
| Language | Python 3.12 |

---

## How to run

**1. Clone the repo**
```bash
git clone https://github.com/aayushmadaan15/credit-policy-copilot.git
cd credit-policy-copilot
```

**2. Install dependencies**
```bash
pip install chromadb openai anthropic python-docx langchain-text-splitters python-dotenv
```

**3. Add your API keys**

Copy `.env.example` to `.env` and fill in your keys:

**4. Add your policy document**

Place your NBFC credit policy `.docx` file in the project folder.
Update `POLICY_FILE` in `copilot.py` to match the filename.

**5. Run**
```bash
python copilot.py
```

---

## What I learned building this

**Chunking strategy matters more than the model.**
The quality of retrieval depends entirely on how the document is chunked. 
Overlapping chunks (chunk_overlap=60) ensure context isn't lost at boundaries — 
critical for policy documents where a rule in one sentence references a 
definition from the previous one.

**System prompts are the PM's job.**
Engineers build the retrieval pipeline. The behavioural guardrails — 
"only answer from context", "say not covered when out of scope", 
"give a clear verdict for eligibility queries" — are product decisions. 
They determine whether the system is safe to deploy in a regulated environment.

**Hallucination risk doesn't disappear with RAG.**
If the document is poorly structured, chunks overlap in confusing ways, 
or the query retrieves irrelevant sections — the model can still go wrong. 
Document governance is as important as the tech stack.

---

## Next steps

- [ ] Add a Streamlit UI for non-technical underwriters
- [ ] Expand eval suite to 20+ queries including edge cases
- [ ] Test with multi-document knowledge base (policy + bureau guidelines + deviation matrix)
- [ ] Add citation highlighting — show exactly which sentence the answer came from

---

## Author

**Aayush Madaan** — Principal Product Manager, Credit Saison India  
Specialisation: AI in Lending, Credit Underwriting, LOS/LMS, NBFC Compliance  
[LinkedIn](https://linkedin.com/in/aayushmadaan) · [GitHub](https://github.com/aayushmadaan15)
