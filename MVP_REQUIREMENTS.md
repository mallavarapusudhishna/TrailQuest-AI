# TrailQuest AI — MVP Requirements

## Goal

TrailQuest AI is a web application that uses an open-weight AI model
(Gemma) to create personalized outdoor quests that encourage users
to leave their screens and spend time outdoors.

## User Inputs

The user provides:

- Location
- Available time
- Activity preference
- Difficulty
- Optional interests

Example:

Location: Chennai
Available time: 60 minutes
Activity: Walking
Difficulty: Easy
Interests: Nature and photography

## Location Search

SerpApi finds real outdoor locations near the user's specified location.

Possible locations:

- Parks
- Gardens
- Trails
- Lakes
- Nature areas
- Outdoor recreational locations

Gemma must NOT invent locations.

Gemma can only create quests using locations returned by SerpApi.

## AI Quest Generation

Gemma receives:

- User preferences
- Real location information returned by SerpApi

Gemma generates one personalized outdoor quest.

The quest contains:

- Quest title
- Location
- Estimated duration
- Difficulty
- Short description
- 3–5 objectives
- Safety note

## Quest Completion

The user can mark the quest as:

- Completed
- Partially completed
- Not completed

The user can optionally provide a short reflection.

## Database

MongoDB Atlas stores:

- Quest information
- User preferences
- Selected location
- Generated quest
- Completion status
- Optional reflection
- Created timestamp
- Completion timestamp

No authentication is required for the MVP.

## MVP User Flow

1. User opens TrailQuest AI.
2. User enters preferences.
3. Backend searches for real outdoor locations.
4. Gemma generates a personalized quest.
5. User sees the quest.
6. User goes outside.
7. User returns and records the result.
8. Quest information is stored in MongoDB.

## MVP Does NOT Include

- Authentication
- Social features
- Leaderboards
- GPS tracking
- Real-time navigation
- Mobile application
- Complex maps
- Computer vision
- Fine-tuning
- Voice generation
- Arduino
- Agent frameworks
- Vector databases
- Real-time location tracking

## Technology

Frontend:
HTML, CSS, JavaScript

Backend:
Python, FastAPI

AI:
Gemma through Ollama

Location Search:
SerpApi

Database:
MongoDB Atlas

Deployment:
Render

Version Control:
Git + GitHub

## Core Principle

The application should encourage users to spend LESS time on the
screen and MORE time outdoors.