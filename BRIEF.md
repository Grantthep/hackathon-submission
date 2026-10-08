# Issa Compass — Vibe Hackathon 🧭

Welcome to the Vibe Hackathon by **Issa Compass** — a software company on a mission to make moving and living in a new country as easy as ordering from Grab. We’re starting with visas. More about us: [issacompass.com/about](https://www.issacompass.com/about)

You'll be working under [Aaron Yip](https://www.linkedin.com/in/aaron-builds) 👋  
- 20 years building tech in Silicon Valley (video games, self-driving cars, industry advisor for Apple, Google App of the Year)
- Startup builder, product person, Stanford Uni + Chulalongkorn Uni guest lecturer

We’re offering roles for **paid internships + full-time recent graduates** based on: **Main Character Energy** 🔥

## 🌟 Today's Project

Build an **self-learning AI assistant that can respond to customer messages** - helping them early through the visa process (before they get supported by our legal team) and improving through every conversation. 

It’s now possible for (Cursor/Antigravity + Opus 4.5/Gemini 3) to deliver work in hours that would take even senior engineers much longer without AI. That’s why we treat Cursor, Antigravity, Gemini, and ChatGPT as the default benchmark. You should have a working project within an hour and then refine beyond. Your project should outperform what you’d get by simply prompting (Cursor/Antigravity) with this description. We want to see the parts that only you (not the model) can contribute.

## What We Look For

We care about **who you are**, not your resume.

### ✅ You Are:
- **Brave** — You push beyond comfort zones
- **Good vibes** — You help others and uplift your team
- **Competitive** — You want to win, and you work hard for it
- **Big dreamer** — You have a big, bold vision for your future

### ❌ We Don’t Care:
- Which university you went to
- Whether you call your professor or phone a friend

## 🛠️ Hackathon Prompt

**Build an Self-learning AI Assistant for Customer Support**

### Input:
We’ve included a file with sample data: `conversations.py`  
This contains sample messages with customers

### Use it to:
- Understand common visa questions and issues
- Identify signals of high-interest customers
- Spot patterns in drop-offs or ghosting
- Anything else that will help build a useful assistant

### Requirements:
- Use Cursor/Antigravity and LLMs of your choice - Claude, Gemini, and ChatGPT
- Create a microservice that takes in (1+ client messages) with the conversation history -- and responds intelligently by API call with LLM (ChatGPT, Claude, Gemini, etc)
- But responses **must not sound like an AI** — make it human, casual, similar to the sample chat data
- The AI is self-learning and trains on sample data to improve. You have a base 

(You don't have to use Python - but for the rest of this project description, I'm going to describe a Python-based system)

## 1️⃣ How to Get Started
1. Get API keys to free tiers for LLMs - Google (Gemma 2 API, Gemini API), Groq API (Llama, Mistral), Claude API
2. Set up a database and get API keys - Supabase, Neon, and Firestore all have free tiers
3. Download Cursor - Cursor has a free tier with 50 prompts and then after that, you can use API keys above to continue usage
4. (Alternatively, you can use Google Antigravity)
5. You will use Claude + ChatGPT on a browser to understand systems and ideas, and Cursor/Antigravity to update the code itself
6. Set up a basic Flask server (just returns hello world) and host it on Render or Railway.app or Fly.io

(If you want to have a frontend visualization, I recommend Next.js hosted on Vercel)

## 2️⃣ Prompts to Create Your Microservice
In the project, have an .env file with your API keys. 
Then open Cursor/Antigravity in your project (a basic Flask server with .env file with keys) and try putting the following in:

**CURSOR PROMPT 1:**

`conversations.json` represents DM text exchange between clients ("in" messages) and immigration consultants ("out" messages). Clients send 1+ DM sequence followed by consultant's 1+ DM sequence reply. Create a script that reads in the json data to create a list of (client sequence + consultant sequence reply + preceeding chat history) for all of the client sequences. Each conversation may have multiple client sequences. Then print out a sample for testing purposes.

**BROWSER PROMPT 1:**

(Switch over to Claude broswer, attach conversations.json and then prompt it, then copy this prompt back into Cursor)

`conversations.json` represents DM text exchange between clients ("in" messages) and immigration consultants ("out" messages). Clients send 1+ DM sequence followed by consultant's 1+ DM sequence reply. Generate a prompt for LLM that takes in a client sequence + preceeding chat history and returns an appropriate AI chatbot reply in json format, eg {"reply": "reply goes here"}

**CURSOR PROMPT 2:**

[Copy the above generated prompt here]

This is a prompt for LLM that takes in a client sequence + preceeding chat history and returns an appropriate chat AI reply in json format. Update the script to use [YOUR LLM OF CHOICE through API KEY IN ENV] with this prompt to generate AI replies given client sequences + preceeding chat history. Then print out a few samples. 

Example: 

CLIENT:
- I'm American and currently in Bali. Can I apply from Indonesia?

CHAT HISTORY:
- (CONSULTANT) Hi there! Thank you for reaching out. The DTV (Destination Thailand Visa) is perfect for remote workers like yourself. May I know your nationality and which country you'd like to apply from?
- (CLIENT) Hello, I'm interested in the DTV visa for Thailand. I work remotely as a software developer for a US company.

AI REPLY:
etc

**INTERMISSION:**

Move the prompt into your database of choice. This prompt will now get updated and improved.

**CURSOR PROMPT 3:**

Refactor the script so that it reads the prompt from [database using API KEY]. 

**INTERMISSION:**

Try manually updating the prompt in your database - for example, tell it to send lots of emojis 😀😃😄😁😆🥹😅😂🤣 - then try running the script to see if the AI is properly using the updated live prompt in your database.

**BROWSER PROMPT 2:**

(Switch over to Claude broswer, paste in the originally generated AI chatbot prompt, then copy this prompt back into Cursor)

Design and generate an AI chatbot prompt editor prompt. The prompt will take in (1) an existing prompt, (2) client sequence, (3) chat history, (4) real consultant reply, and (5) predicted AI reply. The editor prompt will understand the differences between the real consultant reply and the predicted AI reply, infer the logic and stylistic issues in the AI chatbot prompt, and update the AI chatbot prompt with surgical precision to change specific lines of logic. The editor prompt will return the updated AI chatbot prompt in json format like {"prompt": "new updated prompt"}

**CURSOR PROMPT 4:**

[Copy the above generated editor prompt here]

This is an AI chatbot editor prompt. The prompt will take in (1) an existing prompt, (2) client sequence, (3) chat history, (4) real consultant reply, and (5) predicted AI reply. The editor prompt will understand the differences between the real consultant reply and the predicted AI reply, and then update the prompt in json format like {"prompt": "new updated prompt"}. 

Update the script so it uses the editor prompt, run it across samples inputs from `conversations.json`, then set and update the database prompt, then use the new database prompt to generate AI replies.

**INTERMISSION:**

Try testing it and seeing how it works.

**CURSOR PROMPT 5:**

Update the Flask server to have the following endpoints:

`POST /generate-reply`
Generate an AI response based on conversation context.

**Request:**
```json
{
  "clientSequence": "I'm American and currently in Bali. Can I apply from Indonesia?",
  "chatHistory": [
    { "role": "consultant", "message": "Hi there! Thank you for reaching out. The DTV is perfect for remote workers like yourself. May I know your nationality and which country you'd like to apply from?" },
    { "role": "client", "message": "Hello, I'm interested in the DTV visa for Thailand. I work remotely as a software developer for a US company." }
  ]
}
```

**Response:**
```json
{
  "aiReply": "Great news! As a US citizen, you can apply for the DTV from the Thai Embassy in Jakarta, Indonesia. Processing typically takes 5-7 business days. Would you like me to walk you through the required documents?"
}
```

---

`POST /improve-ai`
Auto-improve the AI prompt by comparing predicted vs actual consultant reply.

**Request:**
```json
{
  "clientSequence": "I'm American and currently in Bali. Can I apply from Indonesia?",
  "chatHistory": [...],
  "consultantReply": "Yes, absolutely! You can apply at the Thai Embassy in Jakarta. I'd recommend scheduling an appointment soon as slots fill up quickly."
}
```

**Response:**
```json
{
  "predictedReply": "Great news! As a US citizen, you can apply...",
  "updatedPrompt": "You are a visa consultant specializing in Thai DTV visas..."
}
```

---

`POST /improve-ai-manually`
Manually update the AI prompt with specific instructions.

**Request:**
```json
{
  "instructions": "Be more concise. Always mention appointment booking proactively."
}
```

**Response:**
```json
{
  "updatedPrompt": "You are a visa consultant specializing in Thai DTV visas..."
}
```

**INTERMISSION:**

Test the endpoints hosted publicly on Render/Railway and now you're ready to build from here - time to have fun!

## 🧪 How to Submit
1. Work from anywhere, get help from anyone, do anything you like
2. When you're done:
   - Send your (i) GitHub project link, (ii) hosted server URL e.g. `https://[yourname]-hackathon.up.railway.app`, and (iii) example cURL commands to test your server to **aaron@issacompass.com**, cc **recruiting.team@issacompass.com**

## 🎨 Be Creative, Be Memorable
Main characters stand out — not because they take the easy path, but because they rise to the moment. 

You’ll get a working project by following the steps - that’s just the starting point, an `F score`. A `C score` means you pushed it meaningfully further. A `B score` means you built something better than almost everyone else. We only make offers to the projects that reach an `A+ score` — the ones that surprise us and feel unmistakably above every other submission we've seen.

Some examples of improvements include:
- Deployment to GCP or AWS using a Dockerized infrastructure, replacing Railway
- Next.js–based chat interface to visualize conversations and integrate AI workflows
- Diff visualization to surface self-learning edits and model updates

Think of the main characters you admire — what would they do in this situation? They’d go deeper. Take risks. Push boundaries but always stay brave and kind. That’s who we’re looking for.

Good luck and have fun!
— Team Issa 🚀
