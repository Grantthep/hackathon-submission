"""Runs without any API key: the LLM is replaced with a fake.

    python -m unittest -v
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as server
import assistant
import data
import llm
import store


class FakeLLM:
    def __init__(self):
        self.calls = []
        self.edit = None  # what the editor should return

    def __call__(self, system, user, temperature=0.4):
        self.calls.append((system, user))
        if system == store.get("editor"):
            return self.edit if self.edit is not None else {"prompt": json.loads(user)["currentPrompt"]}
        return {"reply": "Yes, you can apply from Indonesia!"}


class AppTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patches = [
            mock.patch.object(store, "LOCAL_FILE", Path(tmp.name) / "store.json"),
            mock.patch.dict("os.environ", {"SUPABASE_URL": "", "SUPABASE_KEY": ""}),
            mock.patch.object(llm, "chat_json", FakeLLM()),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.llm = llm.chat_json
        self.client = server.app.test_client()

    def test_samples_pair_client_turns_with_consultant_replies(self):
        samples = data.load_samples()
        self.assertGreater(len(samples), 100)
        first = samples[0]
        self.assertEqual(first["chatHistory"], [])
        self.assertIn("DTV", first["clientSequence"])
        self.assertIn("nationality", first["consultantReply"])
        # Consecutive client messages are merged into one sequence.
        self.assertTrue(any("\n" in s["clientSequence"] for s in samples))

    def test_generate_reply(self):
        r = self.client.post("/generate-reply", json={"clientSequence": "Can I apply from Bali?", "chatHistory": []})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["aiReply"], "Yes, you can apply from Indonesia!")

    def test_generate_reply_requires_client_sequence(self):
        self.assertEqual(self.client.post("/generate-reply", json={}).status_code, 400)

    def test_brief_example_history_is_flipped_to_oldest_first(self):
        history = [
            {"role": "consultant", "message": "May I know your nationality?"},
            {"role": "client", "message": "Hello, I'm interested in the DTV."},
        ]
        self.assertEqual(assistant.normalize_history(history)[0]["role"], "client")
        self.assertEqual(assistant.normalize_history(history, "oldest_first")[0]["role"], "consultant")

    def test_improve_ai_saves_a_new_version(self):
        new_prompt = store.get("chatbot") + "\n- Mention the 10 business day processing time for Indonesia."
        self.llm.edit = {"prompt": new_prompt, "changes": ["added Indonesia timing"]}
        r = self.client.post("/improve-ai", json={
            "clientSequence": "Can I apply from Indonesia?", "chatHistory": [],
            "consultantReply": "Yes! Processing there is about 10 business days.",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["predictedReply"], "Yes, you can apply from Indonesia!")
        self.assertEqual(r.json["updatedPrompt"], new_prompt)
        self.assertEqual(r.json["version"], 1)
        self.assertEqual(store.get("chatbot"), new_prompt)
        self.assertEqual(len(self.client.get("/prompt").json["versions"]), 1)

    def test_destructive_edit_is_rejected(self):
        before = store.get("chatbot")
        self.llm.edit = {"prompt": "Be nice."}
        r = self.client.post("/improve-ai-manually", json={"instructions": "Use emojis"})
        self.assertEqual(r.json["updatedPrompt"], before)
        self.assertIsNotNone(r.json["rejected"])
        self.assertEqual(store.get("chatbot"), before)

    def test_llm_failure_returns_503(self):
        with mock.patch.object(llm, "chat_json", side_effect=llm.LLMError("bad key")):
            r = self.client.post("/generate-reply", json={"clientSequence": "hi"})
        self.assertEqual(r.status_code, 503)
        self.assertIn("bad key", r.json["error"])


if __name__ == "__main__":
    unittest.main()
