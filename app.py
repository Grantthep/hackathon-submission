from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import json
from pathlib import Path

load_dotenv()

app = Flask(__name__)

# ----------------------------
# Prompt storage (prompts.json)
# ----------------------------
PROMPTS_FILE = Path("prompts.json")

DEFAULT_PROMPTS = {
    "chatbot_prompt": (
        "You are a helpful visa consultant assistant. "
        "Reply clearly, politely, and practically. Ask one quick clarifying question if needed."
    ),
    "editor_prompt": (
        "You are an expert prompt engineer.\n"
        "Goal: improve the chatbot_prompt so the predicted reply becomes closer to the consultantReply.\n"
        "Return ONLY valid JSON exactly like: {\"prompt\": \"...\"}\n"
        "No extra text."
    ),
}

def ensure_prompts_file():
    if not PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=2)

def load_prompts():
    ensure_prompts_file()
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_prompts(data):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# LLM helpers (OpenAI optional)
# ----------------------------
def _try_openai_chat(messages):
    """
    Tries to call OpenAI if OPENAI_API_KEY is set and openai package is installed.
    Returns text or raises exception.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    # Try the new OpenAI SDK first
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,
        )
        return resp.choices[0].message.content
    except ImportError:
        raise RuntimeError("openai package not installed")
    except Exception:
        # Could be billing/quota, etc.
        raise


def llm_text(messages, fallback_text):
    """
    Always returns a string.
    If OpenAI call fails, returns fallback_text.
    """
    try:
        return _try_openai_chat(messages)
    except Exception:
        return fallback_text


def generate_reply_with_prompt(system_prompt, chat_history, client_sequence):
    """
    chat_history format expected from your API:
      [{"role":"consultant","message":"..."}, {"role":"client","message":"..."}]
    We'll map consultant->assistant, client->user for LLM.
    """
    messages = [{"role": "system", "content": system_prompt}]

    for item in chat_history:
        role = item.get("role")
        msg = item.get("message", "")
        if not msg:
            continue

        if role == "client":
            messages.append({"role": "user", "content": msg})
        elif role == "consultant":
            messages.append({"role": "assistant", "content": msg})
        else:
            # unknown role, treat as user
            messages.append({"role": "user", "content": msg})

    # Latest client message
    messages.append({"role": "user", "content": client_sequence})

    # Fallback (if no OpenAI key)
    fallback = f"Got it — quick question: what country are you applying from right now? 🙂"

    return llm_text(messages, fallback)


def extract_json_object(text):
    """
    Parses JSON from a response that should contain {"prompt": "..."}.
    Works even if the model adds extra text.
    """
    text = (text or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return json.loads(text[start:end + 1])


def update_prompt_with_editor(editor_prompt, payload, fallback_new_prompt):
    """
    Uses LLM editor_prompt to produce {"prompt": "..."}.
    Falls back to a simple prompt update if OpenAI is unavailable.
    """
    messages = [
        {"role": "system", "content": editor_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ]

    # If OpenAI fails, we still return something reasonable
    raw = llm_text(
        messages,
        fallback_text=json.dumps({"prompt": fallback_new_prompt}, ensure_ascii=False)
    )

    try:
        return extract_json_object(raw)
    except Exception:
        # Final fallback if parsing fails
        return {"prompt": fallback_new_prompt}


# ----------------------------
# Routes
# ----------------------------
@app.post("/generate-reply")
def generate_reply():
    data = request.get_json(force=True)

    client_sequence = data.get("clientSequence", "")
    chat_history = data.get("chatHistory", [])

    prompts = load_prompts()
    system_prompt = prompts.get("chatbot_prompt", DEFAULT_PROMPTS["chatbot_prompt"])

    reply = generate_reply_with_prompt(system_prompt, chat_history, client_sequence)

    # Match your current response shape:
    return jsonify({"aiReply": reply})


@app.post("/improve-ai")
def improve_ai():
    data = request.get_json(force=True)

    client_sequence = data.get("clientSequence", "")
    chat_history = data.get("chatHistory", [])
    consultant_reply = data.get("consultantReply", "")

    prompts = load_prompts()
    chatbot_prompt = prompts.get("chatbot_prompt", DEFAULT_PROMPTS["chatbot_prompt"])
    editor_prompt = prompts.get("editor_prompt", DEFAULT_PROMPTS["editor_prompt"])

    # 1) predicted reply
    predicted = generate_reply_with_prompt(chatbot_prompt, chat_history, client_sequence)

    # 2) update prompt (editor)
    payload = {
        "current_prompt": chatbot_prompt,
        "chatHistory": chat_history,
        "clientSequence": client_sequence,
        "consultantReply": consultant_reply,
        "predictedReply": predicted,
    }

    # Fallback new prompt if no OpenAI:
    fallback_new_prompt = (
        chatbot_prompt
        + "\n\nNew rule: Be closer to the consultant's style. "
        + "Be concise, practical, and proactive."
    )

    improved = update_prompt_with_editor(editor_prompt, payload, fallback_new_prompt)
    new_prompt = improved.get("prompt", chatbot_prompt)

    # 3) save
    prompts["chatbot_prompt"] = new_prompt
    save_prompts(prompts)

    return jsonify({
        "predictedReply": predicted,
        "updatedPrompt": new_prompt
    })


@app.post("/improve-ai-manually")
def improve_ai_manually():
    data = request.get_json(force=True)
    instructions = data.get("instructions", "")

    prompts = load_prompts()
    chatbot_prompt = prompts.get("chatbot_prompt", DEFAULT_PROMPTS["chatbot_prompt"])
    editor_prompt = prompts.get("editor_prompt", DEFAULT_PROMPTS["editor_prompt"])

    payload = {
        "current_prompt": chatbot_prompt,
        "instructions": instructions
    }

    fallback_new_prompt = chatbot_prompt + f"\n\nManual instructions:\n- {instructions}"

    improved = update_prompt_with_editor(editor_prompt, payload, fallback_new_prompt)
    new_prompt = improved.get("prompt", chatbot_prompt)

    prompts["chatbot_prompt"] = new_prompt
    save_prompts(prompts)

    return jsonify({"updatedPrompt": new_prompt})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
