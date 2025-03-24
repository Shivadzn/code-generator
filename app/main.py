import os
import time
import uuid
import requests
import re
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load .env automatically from the project directory
load_dotenv()

# Read API key and model name
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")  # Default model
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2000"))  # Default max length
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.5"))  # Default temperature

# Debugging: Check if API key is loaded
if not HF_API_KEY:
    print("❌ HF_API_KEY is not set. Check your .env file or environment variables.")
else:
    print(f"HF_API_KEY Loaded: {HF_API_KEY[:5]}******")  # Masked for security

print(f"HF_MODEL Loaded: {HF_MODEL}")
print(f"Using parameters: MAX_LENGTH={MAX_LENGTH}, TEMPERATURE={TEMPERATURE}")

# Initialize FastAPI app
app = FastAPI(
    title="Code Generation API",
    description="API for generating code and explanations using Hugging Face models",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation history (use Redis/DB for production)
conversation_history: Dict[str, List[str]] = {}


# Define request formats
class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The user's prompt or question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation history")
    response_type: Optional[str] = Field("both", description="Type of response: 'code', 'explanation', or 'both'")


class HistoryRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to retrieve or clear history")


def classify_message(message):

    # Convert message to lowercase for comparison
    message_lower = message.lower().strip()

    # List of common conversational greetings and phrases
    conversational_phrases = [
        "hi", "hello", "hey", "hi there", "hello there", "hey there",
        "how are you", "good morning", "good afternoon", "good evening",
        "what's up", "how's it going", "nice to meet you", "bye", "goodbye",
        "thank you", "thanks", "ok", "okay", "yes", "no", "maybe",
        "help", "who are you", "what can you do", "what are you",
        "tell me about", "can you", "could you", "would you", "do you",
        "i want to", "i need", "please", "explain", "describe"
    ]

    # Check if the message is a question or conversation
    if any(message_lower.startswith(phrase) for phrase in conversational_phrases) or \
            any(phrase in message_lower for phrase in conversational_phrases) or \
            message_lower.endswith("?") or \
            len(message_lower.split()) <= 5:  # Short messages are likely conversational
        return "conversation"

    # If in doubt, treat as conversation
    return "conversation"


# API call function with retry and improved error handling
def generate_response_hf(prompt: str) -> str:
    """Sends prompt to Hugging Face API and returns the generated response."""
    if not HF_API_KEY:
        raise HTTPException(status_code=500, detail="HF_API_KEY is missing.")

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": MAX_LENGTH,
            "temperature": TEMPERATURE,
            "return_full_text": False  # Only return the generated text, not the prompt
        },
    }

    for attempt in range(3):  # Retry logic
        try:
            print(f"🔄 Attempt {attempt + 1} - Sending request to HF API")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                generated_text = response.json()
                if isinstance(generated_text, list) and generated_text:
                    result = generated_text[0].get("generated_text", "")
                    # Clean up the response - remove the prompt if it's included
                    if result.startswith(prompt):
                        result = result[len(prompt):].lstrip()
                    return result
                return "No response generated"

            elif response.status_code == 401:  # Unauthorized (Invalid API key)
                print("❌ Authentication error: Invalid API Key")
                raise HTTPException(status_code=401, detail="Invalid API Key. Check your HF_API_KEY.")

            elif response.status_code == 503:  # Model is loading
                print("Model is loading, waiting...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

            elif response.status_code == 429:  # Rate limit error
                print("⚠️ Rate limited, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = str(error_data)
                except:
                    error_detail = response.text

                print(f"❌ API Error: {error_detail}")
                if attempt == 2:  # Last attempt
                    raise HTTPException(status_code=response.status_code,
                                        detail=f"HF API Error: {error_detail}")

        except requests.exceptions.Timeout:
            print("⚠️ Request timed out, retrying...")
            if attempt == 2:  # Last attempt
                raise HTTPException(status_code=504, detail="Request timed out")

        except requests.exceptions.ConnectionError:
            print("⚠️ Connection error, retrying...")
            if attempt == 2:  # Last attempt
                raise HTTPException(status_code=503, detail="Could not connect to Hugging Face API")

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            if attempt == 2:  # Last attempt
                raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        # Wait before retry (except on last attempt)
        if attempt < 2:
            time.sleep(2 ** attempt)

    raise HTTPException(status_code=500, detail="Failed to get response after multiple attempts")


# Helper function to process and format the model's response
def process_response(raw_response: str, response_type: str) -> Dict[str, Any]:
    """Process and format the model's response based on the requested type."""

    # For conversational responses, don't try to extract code
    if response_type == "conversation":
        return {"response": raw_response}

    elif response_type == "code":
        # Extract code blocks with regex
        code_match = re.search(r"```(?:python)?\n(.*?)\n```", raw_response, re.DOTALL)
        if code_match:
            return {"generated_code": code_match.group(1).strip()}
        return {"generated_code": raw_response}

    elif response_type == "explanation":
        # Remove code blocks
        explanation = re.sub(r"```(?:python)?\n.*?\n```", "", raw_response, flags=re.DOTALL).strip()
        return {"explanation": explanation}

    else:  # "both"
        code = None
        explanation = raw_response

        # Extract code blocks
        code_match = re.search(r"```(?:python)?\n(.*?)\n```", raw_response, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            # Remove code blocks from explanation
            explanation = re.sub(r"```(?:python)?\n.*?\n```", "", raw_response, flags=re.DOTALL).strip()

        return {"response": raw_response}


# API route for generating responses
@app.post("/generate/")
async def generate_response(request: PromptRequest):
    """Handles incoming user requests, maintains session history, and calls HF model."""
    try:
        session_id = request.session_id or str(uuid.uuid4())

        if session_id not in conversation_history:
            conversation_history[session_id] = []

        # Build contextual prompt with history
        history_context = ""
        if conversation_history[session_id]:
            history_context = "\n".join(conversation_history[session_id][-6:])  # Keep last 3 exchanges

        # Classify the message type first
        message_type = classify_message(request.prompt)

        # Different prompt formatting based on message type
        if message_type == "conversation":
            # For conversational messages, use a simpler prompt template
            full_prompt = f"<s>[INST] {request.prompt} [/INST]"
        else:
            # For code-related queries, use your original templates
            if request.response_type == "code":
                full_prompt = f"""<s>[INST] Write Python code for the following request. Return only the code without explanation.
User request: {request.prompt}
```python
[/INST]"""
            elif request.response_type == "explanation":
                full_prompt = f"""<s>[INST] Explain how to solve this programming task. Don't include code, just explain the approach clearly.
User request: {request.prompt} [/INST]"""
            else:  # both
                full_prompt = f"""<s>[INST] Write Python code for the following request and provide an explanation.
User request: {request.prompt}

First give a clear explanation of your approach, then include the code in a Python code block (```python). [/INST]"""

        # Add history context if available
        if history_context and message_type != "conversation":
            full_prompt = f"<s>[INST] Previous conversation:\n{history_context}\n\n{request.prompt} [/INST]"

        # Get response from HF model
        print(f"Sending prompt to model: {full_prompt[:100]}...")
        generated_response = generate_response_hf(full_prompt)
        print(f"✅ Received response of length: {len(generated_response)}")

        # Store conversation history
        conversation_history[session_id].append(f"User: {request.prompt}")
        conversation_history[session_id].append(f"AI: {generated_response}")

        # Limit history size to prevent memory issues
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]

        # For conversational messages, return directly without code/explanation processing
        if message_type == "conversation":
            response_data = {"response": generated_response, "message_type": "conversation"}
        else:
            # Handle response type and build response data for code-related messages
            response_data = process_response(generated_response, request.response_type)
            response_data["message_type"] = "code"

        response_data["session_id"] = session_id
        return response_data

    except HTTPException as e:
        # Re-raise HTTP exceptions to maintain status codes
        raise
    except Exception as e:
        print(f"❌ Unexpected error in generate_response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# API route for clearing conversation history
@app.post("/clear_history/")
async def clear_history(request: HistoryRequest):
    """Clears conversation history for a given session."""
    if request.session_id in conversation_history:
        conversation_history[request.session_id] = []
        return {"status": "success", "message": "Conversation history cleared"}
    return {"status": "not_found", "message": "Session ID not found"}


# API route for getting conversation history
@app.post("/get_history/")
async def get_history(request: HistoryRequest):
    """Gets conversation history for a given session."""
    if request.session_id in conversation_history:
        return {"status": "success", "history": conversation_history[request.session_id]}
    return {"status": "not_found", "message": "Session ID not found"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "model": HF_MODEL}


# Request logging middleware for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} → Status: {response.status_code} ({process_time:.2f}s)")
    return response
