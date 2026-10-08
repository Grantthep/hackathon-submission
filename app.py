from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

import assistant  # noqa: E402  (needs .env loaded first)
import llm  # noqa: E402
import store  # noqa: E402

app = Flask(__name__)


def _body(*required):
    data = request.get_json(silent=True) or {}
    missing = [k for k in required if not str(data.get(k) or "").strip()]
    if missing:
        return data, (jsonify({"error": f"Missing field(s): {', '.join(missing)}"}), 400)
    return data, None


@app.errorhandler(llm.LLMError)
def llm_failed(e):
    return jsonify({"error": str(e)}), 503


@app.get("/")
def index():
    return Path(__file__).with_name("index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    try:
        provider, model = llm.provider_name(), llm.model_name()
    except llm.LLMError as e:
        provider, model = None, str(e)
    return jsonify({"ok": True, "llm": provider, "model": model, "promptStore": store.backend()})


@app.post("/generate-reply")
def generate_reply():
    data, err = _body("clientSequence")
    if err:
        return err
    history = assistant.normalize_history(data.get("chatHistory"), data.get("historyOrder"))
    return jsonify({"aiReply": assistant.generate_reply(data["clientSequence"], history)})


@app.post("/improve-ai")
def improve_ai():
    data, err = _body("clientSequence", "consultantReply")
    if err:
        return err
    history = assistant.normalize_history(data.get("chatHistory"), data.get("historyOrder"))
    return jsonify(assistant.improve(data["clientSequence"], history, data["consultantReply"]))


@app.post("/improve-ai-manually")
def improve_ai_manually():
    data, err = _body("instructions")
    if err:
        return err
    return jsonify(assistant.improve_manually(data["instructions"]))


@app.get("/prompt")
def prompt_history():
    return jsonify({"versions": store.history("chatbot")})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
