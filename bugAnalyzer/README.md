# AI Bug Analyzer

AI-powered Jira bug analysis using Claude AI with RAG pipeline.

## What it does
- Connects to Jira and fetches bugs automatically
- Searches ChromaDB for similar past bugs (RAG)
- Sends each bug to Claude with historical context
- Returns severity, priority, component and fix suggestions
- Shows similar past bugs in UI for reference
- CSV download button

## Tech Stack
Python · Claude API · Streamlit · Jira REST API · ChromaDB · LangChain

## Branches
- main — RAG version with ChromaDB
- feature/basic — Basic version, no RAG
- feature/langgraph-agent — LangGraph agent version
- feature/tool-use — Tool use examples

## How to run
1. Set environment variables: ANTHROPIC_API_KEY, JIRA_URL, JIRA_EMAIL, JIRA_TOKEN
2. pip install -r requirements.txt
3. python3 -m streamlit run bugAnalyzer/Bug_APP.py

## Built by
Karthick Ram Pandian — Senior QA Automation Engineer transitioning to AI Engineering