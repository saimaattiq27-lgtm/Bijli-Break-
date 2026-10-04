# ⚡ Bijli Break

Bijli Break is a load-shedding-aware study planner for students.

It plans screen-based work during light hours and offline work during outage hours.

## Features

- ⚡ Add today's outage slots
- 📝 Add study tasks
- 💻 Screen / 📖 Offline / Either task types
- 🔴 High / Normal priority
- 📅 Automatic daily timeline
- 📌 Tasks that do not fit are shown as moved to tomorrow
- 🔔 Next-outage banner
- 🤖 Optional Groq AI study assistant
- 📱 Responsive Streamlit layout

## Local setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Streamlit secrets

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
GROQ_API_KEY = "your-real-groq-api-key"
GROQ_MODEL = "openai/gpt-oss-20b"
```

Do NOT upload `secrets.toml` to GitHub.

### 3. Run

```bash
streamlit run app.py
```

## GitHub

Upload:

- app.py
- requirements.txt
- README.md
- .gitignore
- .streamlit/secrets.example.toml

Do not upload `.streamlit/secrets.toml`.

## Streamlit deployment

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select your GitHub repository.
5. Select branch `main`.
6. Set main file to `app.py`.
7. Deploy.
8. Open App Settings -> Secrets.
9. Add:

```toml
GROQ_API_KEY = "your-real-groq-api-key"
GROQ_MODEL = "openai/gpt-oss-20b"
```

Save and restart the app.

## Note

The core planner works without Groq. Groq is used for the optional AI Study Assistant.
