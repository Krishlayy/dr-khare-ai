# 🏥 Dr. Khare AI Assistant

Welcome to the **Dr. Khare AI Assistant** project! 

This project is a highly intelligent, secure chat widget designed to be embedded directly into Dr. Khare's website. It acts as a 24/7 personal assistant that answers questions from patients, colleagues, and researchers based **strictly** on Dr. Khare's uploaded CV, publications, and clinic documents.

If you are a new developer joining this project with zero prior knowledge, this guide will explain exactly what this is, how it works, and how you can run it and add features to it.

---

## 🌟 What Does This Project Do?

1. **Website Widget**: It provides a clean, minimalist chat interface (the "Frontend") that will be placed on Dr. Khare's official website.
2. **Document-Based AI (RAG)**: It uses a technology called RAG (Retrieval-Augmented Generation). This means when a user asks a question, the system searches through Dr. Khare's private documents, finds the exact paragraphs needed, and generates a confident answer. **It does not hallucinate or make things up.**
3. **Admin Dashboard**: Dr. Khare (or staff) can log in, upload new PDFs or Word documents, and the AI instantly learns from them.
4. **Smart Failover (Circuit Breaker)**: The AI is powered by lightning-fast cloud models (Groq). If the cloud ever goes offline, the system automatically falls back to a local AI model (Ollama) so the website never goes down.
5. **Rate Limiting**: To prevent spam, users are limited to 5 questions every 6 hours. 

---

## 🏗️ The Technology Stack

This project is split into two halves:

### 1. The Frontend (The User Interface)
- Located in the `/frontend` folder.
- Built using **React** and **Vite**.
- Styled with pure CSS to be incredibly clean, fast, and responsive.

### 2. The Backend (The Brains)
- Located in the `/backend` folder.
- Built using **Python** and **FastAPI**.
- Uses **ChromaDB** to store document paragraphs as mathematical vectors.
- Uses **PostgreSQL** (or SQLite locally) to store user accounts and document status.
- Uses **Redis** to track rate limits and monitor the health of the AI providers.

---

## 🚀 How To Start This Project From Scratch (Zero to Running)

If you just cloned this code, follow these exact steps to get it running on your local computer.

### Prerequisites
You must install these on your computer first:
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)
- *(Optional but recommended)* [Ollama](https://ollama.com/) (For local AI fallback)

### Step 1: Set up the Backend (Python)
Open your terminal (or Command Prompt) and type:

```bash
# 1. Go into the backend folder
cd backend

# 2. Install the required Python libraries
pip install -r requirements.txt

# 3. Create a .env file (Ask the team for the secret API keys!)
cp .env.example .env

# 4. Go back to the main folder and initialize the database
cd ..
python init_db.py

# 5. Start the backend server!
python -m uvicorn backend.main:app --reload
```
*The backend is now running quietly in the background at `http://127.0.0.1:8000`.*

### Step 2: Set up the Frontend (React)
Open a **new** terminal window and type:

```bash
# 1. Go into the frontend folder
cd frontend

# 2. Install the required Javascript libraries
npm install

# 3. Start the website!
npm run dev
```
*The website is now running at `http://localhost:5173`. Open this in your browser!*

---

## 🛠️ How to Work on it and Add Features

We encourage you to add new features! Here is where you should look depending on what you want to do:

**"I want to change how the chat bubble looks or change the colors."**
- Go to `frontend/src/App.css` and `frontend/src/index.css`. All the styles are located here.

**"I want to add a new button to the chat window."**
- Go to `frontend/src/App.jsx`. This is the main React component that draws the chat widget.

**"I want to change how the AI reads PDFs."**
- Go to `backend/rag/document_processor.py`. This is where the code rips text out of PDFs and Word documents.

**"I want to change the AI's personality or rules."**
- Go to `backend/services/chat_service.py`. This is where we format the "System Prompt" that tells the AI how to behave before answering a user.

**"I want to add a new API endpoint (like a new URL the frontend can talk to)."**
- Go to the `backend/api/routes/` folder. Add your logic there, and FastAPI will automatically document it for you at `http://127.0.0.1:8000/docs`.

---

## 🚢 Preparing for the Website
When it is time to put this on Dr. Khare's actual website, you will need to "build" the frontend.

Run this inside the `/frontend` folder:
```bash
npm run build
```
This turns the React code into highly optimized HTML and Javascript files in a `dist/` folder. You can upload these files to your web host (like Vercel, Netlify, or an AWS S3 bucket), and embed it into the existing website using an `<iframe>` or web component!

For full production deployment instructions (including setting up Docker, Postgres, and Nginx), please refer to the internal `DEPLOYMENT_GUIDE.md`.
