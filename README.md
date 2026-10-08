# Issa Compass DTV Assistant

A self-learning customer support assistant for Thailand DTV visa DMs. It replies like a human consultant, learns from real consultant replies, and keeps every version of its prompt so you can see how it changed.

The original hackathon brief is in [BRIEF.md](BRIEF.md).

## What it does

- **Replies like a person, not a bot.** The seed prompt was written from the 15 sample conversations. It covers the real fees, timelines, document lists and policies, and the consultants' style: short, warm, one question at a time, always moving the customer toward uploading documents in the app.
- **Learns from real replies.** `/improve-ai` and `train.py` compare the bot's reply with what the human consultant actually said. An editor prompt then makes small, targeted edits to the chatbot prompt. It doesn't keep tacking new rules onto the end.
- **Protects the live prompt.** If an edit would delete most of the prompt or break the JSON output format, it's rejected and the live prompt stays as it was.
- **Keeps every version.** Each change is saved as a new version with its source (auto or manual) and a note on what changed. The web page at `/` shows a line-by-line diff between versions.
- **Works with several LLM providers.** OpenAI, Gemini or Groq, chosen by which key is in `.env`.
- **Handles either history order.** The brief's example sends chat history newest-first, and the API detects that and reverses it. Send `historyOrder` to say the order explicitly.

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # then add one API key
python app.py                   # http://localhost:5000
```

Train on the sample data:

```bash
python data.py                  # show how conversations.json becomes 128 training samples
python train.py --dry-run 3     # compare AI replies with the real consultant replies
python train.py --limit 20      # learn from 20 samples (each one can update the prompt)
```

Tests (no API key needed):

```bash
python -m unittest -v
```

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/generate-reply` | `clientSequence`, `chatHistory`, optional `historyOrder` | `aiReply` |
| POST | `/improve-ai` | `clientSequence`, `chatHistory`, `consultantReply` | `predictedReply`, `updatedPrompt`, `changes`, `version` |
| POST | `/improve-ai-manually` | `instructions` | `updatedPrompt`, `changes`, `version` |
| GET | `/prompt` | | every prompt version |
| GET | `/health` | | the configured LLM and prompt store |

`chatHistory` items look like `{"role": "client" | "consultant", "message": "..."}`. If the LLM call fails, the API returns HTTP 503 with the reason. It never sends back a made-up reply.

### cURL examples

Replace `$URL` with `http://localhost:5000` or the deployed URL.

```bash
curl -X POST $URL/generate-reply -H "Content-Type: application/json" -d '{
  "clientSequence": "I'"'"'m American and currently in Bali. Can I apply from Indonesia?",
  "chatHistory": [
    {"role": "consultant", "message": "Hi there! Thank you for reaching out. The DTV is perfect for remote workers like yourself. May I know your nationality and which country you'"'"'d like to apply from?"},
    {"role": "client", "message": "Hello, I'"'"'m interested in the DTV visa for Thailand. I work remotely as a software developer for a US company."}
  ]
}'

curl -X POST $URL/improve-ai -H "Content-Type: application/json" -d '{
  "clientSequence": "I'"'"'m American and currently in Bali. Can I apply from Indonesia?",
  "chatHistory": [],
  "consultantReply": "Yes, you can apply from Indonesia! For remote workers, our service fees are 18,000 THB including all government fees. The processing time in Indonesia is typically around 10 business days."
}'

curl -X POST $URL/improve-ai-manually -H "Content-Type: application/json" -d '{
  "instructions": "Be more concise. Always mention appointment booking proactively."
}'
```

## Prompt storage

By default, prompt versions are saved to `prompt_store.json`. To use Supabase instead, set `SUPABASE_URL` and `SUPABASE_KEY` and create the table once:

```sql
create table prompts (
  id bigint generated always as identity primary key,
  name text not null,
  prompt text not null,
  source text,
  note text,
  created_at timestamptz default now()
);
```

On hosts that wipe the disk on every redeploy (Render, Railway), use Supabase so the prompt keeps what it has learned.

## Deploy

**Render or Railway:** connect this repo. The start command comes from the `Procfile`. Add the API key (and optionally the Supabase keys) as environment variables.

**Docker (GCP Cloud Run, AWS, anywhere):**

```bash
docker build -t dtv-assistant .
docker run -p 8080:8080 --env-file .env dtv-assistant
```

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask routes |
| `assistant.py` | generating replies, learning from consultant replies, the edit guard rails |
| `prompts.py` | seed chatbot prompt and editor prompt |
| `store.py` | versioned prompt storage (Supabase or local JSON) |
| `llm.py` | OpenAI / Gemini / Groq wrapper that returns JSON |
| `data.py` | turns `conversations.json` into training samples |
| `train.py` | self-learning loop over the sample data |
| `index.html` | chat tester and prompt diff viewer |
