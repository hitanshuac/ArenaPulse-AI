---
name: Universal Ingestion (MarkItDown)
description: Implements Microsoft's markitdown library to flatten unstructured proprietary file formats into clean, LLM-digestible markdown streams.
---

# Universal Ingestion Skill

This skill documents the Standard Operating Procedure (SOP) for safely converting messy, unstructured, and proprietary files (PDF, DOCX, XLSX, CSV, PPTX) into a uniform Markdown format using Microsoft's `markitdown`.

## 1. Core Principles

- **Never pass raw proprietary files to an LLM.** Always flatten them into Markdown first.
- **Never pass massive files to an LLM.** To prevent `ContextWindowExceeded` and `RateLimitError` crashes, always truncate the output.
- **Always use secure temporary files.** Do not permanently save user uploads to the `/data` directory unless explicitly required by a stateful logging workflow.

## 2. Dependencies
Ensure `markitdown` and its dependencies are present in `requirements.txt`:
```text
markitdown
```

## 3. Implementation Blueprint

When an Agent needs to build a file uploader or ingestion pipeline, it MUST follow this Python implementation pattern:

### Step 1: Secure Temporary Storage
Use Python's `tempfile` module to temporarily hold the user's uploaded binary stream.

```python
import tempfile
import os
from markitdown import MarkItDown

# Assuming `uploaded_file` is a Streamlit or FastAPI UploadFile object
md = MarkItDown()
with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
    tmp.write(uploaded_file.getvalue()) # or .read()
    tmp_path = tmp.name
```

### Step 2: The Conversion
Pass the temporary file path to `MarkItDown`.

```python
try:
    result = md.convert(tmp_path)
    target_text = result.text_content
except Exception as e:
    # Always implement Defensive Programming Observability
    log_error_to_json(type(e).__name__, "markitdown", str(e))
    target_text = ""
finally:
    # Always cleanly delete the temporary file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
```

### Step 3: SRE Context Safeguard (Mandatory Truncation)
To protect the LLM (like Groq, OpenAI, or Gemini) from Out-of-Memory (OOM) failures or massive billing spikes, the markdown string MUST be truncated.

For Header Mapping & Structured Extraction:
```python
# Truncate to the first 25,000 characters
if len(target_text) > 25000:
    target_text = target_text[:25000]
```
*Rationale:* 25,000 characters is roughly 5,000 to 6,000 tokens, which safely fits inside Groq's 8,000-token context window limit.

## 4. Integration with Pydantic
Once the `target_text` is securely extracted and truncated, it can be seamlessly passed to the `parse_messy_text` LLM function to map the headers and extract the JSON schema validated by Pydantic.


# Strict Constraint: No Raw CSV LLM Scans

This rule applies to all ingestion, auditing, and scanning workflows within the Hybrid AI Router Vision pipeline.

## 1. The Core Constraint
- **Rule**: NEVER pass a raw `.csv` or raw `.xlsx` file directly into an LLM context window.
- **Why**: Raw CSVs contain massive amounts of noisy tokens (commas, empty strings, repetitive structural elements). Passing them directly to an LLM causes severe token inflation, hallucinations (where the LLM loses track of column indices), and immediate context window exhaustion, violating the Context Compaction rule.

## 2. Mandatory Abstraction Layers
- Before any LLM operation is performed on tabular or document data, the file **MUST** be processed locally using a structured parsing package.
- **For Tabular Data (CSV/XLSX)**: Use `markitdown` (via `MarkItDown().convert()`) or `pandas` to structure the grid. If an LLM needs to understand the table, pass it the clean Markdown output from `markitdown` or a highly truncated JSON sample of the headers—never the raw comma-separated text.
- **For Unstructured Documents (PDF/Images)**: Use `docling` (via `DocumentConverter`) or the established Vision Cascade to extract bounding boxes and structured JSON representation.

## 3. Implementation of the Shadow Copy / Silver Layer
When building "Shadow Copies" or extracting data to a Silver Layer, do not rely on an LLM to parse the entire grid. Instead:
1. Use `markitdown` or `docling` to extract the document content.
2. If schema mapping is needed, pass *only* the Markdown headers to the LLM to identify the column positions (Schema-on-Read).
3. Perform the actual data extraction, mathematical validations (e.g., `qty * rate`), and anomaly flagging deterministically in Python.
