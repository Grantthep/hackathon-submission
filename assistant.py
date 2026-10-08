"""The three operations behind the API: reply, learn from a real reply, learn from instructions."""
import json

import llm
import store


def normalize_history(history, order=None):
    """Return chat history oldest-first.

    The hackathon brief's example sends history newest-first (consultant reply,
    then the client's opening message). Pass order="newest_first"/"oldest_first"
    to be explicit; otherwise we detect that shape and flip it.
    """
    history = [h for h in (history or []) if (h.get("message") or "").strip()]
    if order == "newest_first":
        return history[::-1]
    if order == "oldest_first" or len(history) < 2:
        return history
    if history[0].get("role") == "consultant" and history[-1].get("role") == "client":
        return history[::-1]
    return history


def _transcript(history, client_sequence):
    lines = [f"({h.get('role', 'client').upper()}) {h['message']}" for h in history]
    return (
        "CHAT HISTORY (oldest first):\n" + ("\n".join(lines) or "(none, this is the first message)")
        + "\n\nCLIENT'S LATEST MESSAGE(S):\n" + client_sequence
    )


def generate_reply(client_sequence, history, prompt=None):
    prompt = prompt or store.get("chatbot")
    result = llm.chat_json(prompt, _transcript(history, client_sequence), temperature=0.5)
    reply = str(result.get("reply", "")).strip()
    if not reply:
        raise llm.LLMError("Model returned an empty reply")
    return reply


def _edit_prompt(payload, source, note):
    current = store.get("chatbot")
    result = llm.chat_json(
        store.get("editor"),
        json.dumps({"currentPrompt": current, **payload}, ensure_ascii=False),
        temperature=0.2,
    )
    new = str(result.get("prompt", "")).strip()
    changes = [str(c) for c in result.get("changes", []) if str(c).strip()]

    # Guard rails: a bad edit must never wipe or break the live prompt.
    if not new or new == current:
        return {"updatedPrompt": current, "changes": [], "version": None, "rejected": None}
    if len(new) < 0.6 * len(current):
        return {"updatedPrompt": current, "changes": changes, "version": None,
                "rejected": "edit removed too much of the prompt"}
    if '"reply"' not in new:
        return {"updatedPrompt": current, "changes": changes, "version": None,
                "rejected": "edit dropped the JSON output instruction"}

    row = store.save("chatbot", new, source, note or "; ".join(changes))
    return {"updatedPrompt": new, "changes": changes, "version": row["id"], "rejected": None}


def improve(client_sequence, history, consultant_reply, note=""):
    predicted = generate_reply(client_sequence, history)
    result = _edit_prompt(
        {
            "chatHistory": history,
            "clientSequence": client_sequence,
            "consultantReply": consultant_reply,
            "predictedReply": predicted,
        },
        source="auto",
        note=note,
    )
    return {"predictedReply": predicted, **result}


def improve_manually(instructions):
    return _edit_prompt({"instructions": instructions}, source="manual", note=instructions)
