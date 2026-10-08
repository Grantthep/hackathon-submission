"""Turns conversations.json into training samples:
(chat history before the client turn, client sequence, consultant reply)."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("conversations.json")


def load_samples(path=DATA_FILE):
    conversations = json.loads(Path(path).read_text(encoding="utf-8"))
    samples = []
    for convo in conversations:
        # Group consecutive messages from the same side into one "turn".
        turns = []
        for msg in convo["conversation"]:
            role = "client" if msg["direction"] == "in" else "consultant"
            if turns and turns[-1]["role"] == role:
                turns[-1]["messages"].append(msg["text"])
            else:
                turns.append({"role": role, "messages": [msg["text"]]})

        for i, turn in enumerate(turns):
            if turn["role"] != "client" or i + 1 >= len(turns):
                continue
            history = [
                {"role": t["role"], "message": m} for t in turns[:i] for m in t["messages"]
            ]
            samples.append({
                "contactId": convo["contact_id"],
                "scenario": convo["scenario"],
                "chatHistory": history,
                "clientSequence": "\n".join(turn["messages"]),
                "consultantReply": "\n".join(turns[i + 1]["messages"]),
            })
    return samples


if __name__ == "__main__":
    samples = load_samples()
    print(f"{len(samples)} samples from {DATA_FILE.name}\n")
    s = samples[1]
    print("SCENARIO:", s["scenario"])
    print("HISTORY:")
    for h in s["chatHistory"]:
        print(f"  ({h['role'].upper()}) {h['message']}")
    print("CLIENT:", s["clientSequence"])
    print("CONSULTANT:", s["consultantReply"])
