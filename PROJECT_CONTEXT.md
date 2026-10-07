# TrailQuest AI — Project Context

## Project

TrailQuest AI

## Hacktoberfest Challenge

Hacktoberfest 2026 Week 1

Theme:
Touch Grass

## Goal

Create an application using open-weight AI that encourages users
to leave the screen and participate in real-world outdoor activities.

## Core Idea

The user provides:

- Location
- Available time
- Activity
- Difficulty
- Interests

SerpApi finds real outdoor locations.

Gemma uses those real locations and the user's preferences to
generate a personalized outdoor quest.

The user goes outside and later records whether they completed it.

## Technology Stack

Frontend:
HTML
CSS
JavaScript

Backend:
Python
FastAPI

AI:
Gemma
Ollama

Location Search:
SerpApi

Database:
MongoDB Atlas

Deployment:
Render

Version Control:
Git
GitHub

## Important Architecture Rule

SerpApi is responsible for finding real-world locations.

Gemma is responsible for personalization and quest generation.

Gemma must not invent locations.

## MVP Restrictions

Do not introduce:

- React
- Docker
- Redis
- PostgreSQL
- LangChain
- Vector databases
- Authentication
- GPS tracking
- Social features
- Leaderboards
- Mobile applications
- Complex maps

unless explicitly required later.

## Development Principle

Keep the implementation simple, beginner-readable and modular.

Do not rewrite unrelated files.

Implement and test one feature at a time.

Never place API keys directly in source code.

Use environment variables for secrets.