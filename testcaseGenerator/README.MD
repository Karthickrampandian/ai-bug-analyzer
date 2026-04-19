# AI Test Case Generator

Automatically generates Gherkin feature files and Kotlin step definitions from Jira tickets using Claude AI.

## What it does
- Fetch tickets by Jira ticket ID or project name
- Generate Gherkin feature file per ticket
- Generate Kotlin step definition skeleton per ticket
- Download files directly from the UI

## Tech Stack
- Claude API (Haiku) — feature and step definition generation
- Jira REST API — ticket fetching
- ChromaDB — vector storage
- Streamlit — UI

## How to run
1. Create `.env` file with your credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python3 -m streamlit run Testcase_Generator.py`

## Environment Variables
ANTHROPIC_API_KEY=your-key
TEST_JIRA_URL=https://your-domain.atlassian.net
TEST_JIRA_EMAIL=your@email.com
TEST_JIRA_TOKEN=your-token

## Project Structure
- `Testcase_Generator.py` — Streamlit UI
- `JIRA_CONNECT.py` — Jira API integration
- `Cucumber_Generation.py` — Claude feature/step generation
- `llm_connect.py` — JQL generation using Claude