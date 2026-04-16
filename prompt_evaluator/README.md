# Prompt Evaluator

Evaluates multiple system prompts to find which produces the best output.

## What it does
Tests 4 role-based prompts against the same bug query and scores them.

## Scoring methods
- Quality: LLM-as-judge rates suggestion 1-10
- Coverage: keyword matching against expected technical areas
- Diversity: cosine similarity between prompt embeddings
- Final: weighted score (quality 50% + coverage 30% + diversity 20%)

## Why
Helps select the best prompt for production use instead of guessing.

## Stack
Claude API, ChromaDB, NumPy