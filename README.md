# DocuMentor AI 🧠✨

An advanced, full-stack document analysis platform that transforms static documents into interactive conversational partners using an agentic RAG pipeline. Upload a PDF, DOCX, or TXT file and get intelligent, context-aware answers in real-time.

**[➡️ View the Live Demo Here](https://explain-my-doc.vercel.app/)**

---

![DocuMentor AI Demo](./docs/demo.gif)
*(To add a demo, create a `docs` folder in your project, add a `demo.gif` or screenshot, and this will display automatically.)*

## About The Project

Tired of endlessly scrolling through dense documents to find a single piece of information? DocuMentor AI leverages the power of Large Language Models and Retrieval-Augmented Generation (RAG) to solve this problem. Users can upload a document and simply ask questions in plain English. The AI not only provides direct answers but also cites its sources from the document, remembers the conversation, and suggests further topics to explore, acting as a true document expert.

This project was built from the ground up to showcase a modern, production-ready AI application architecture, from the agentic backend logic to a polished, responsive user interface and a full CI/CD deployment pipeline.

## Core Features

*   **📄 Multi-Format Document Upload:** Seamlessly handles PDF, DOCX, and TXT files.
*   **🧠 Agentic RAG Pipeline:** Utilizes an advanced workflow where the AI retrieves relevant context, drafts an answer, and then critiques its own draft for accuracy and clarity before responding.
*   **⚡ Real-Time Streaming:** Responses are streamed token-by-token for a dynamic, ChatGPT-like user experience.
*   **🤔 Conversational Memory:** Remembers the last few turns of the conversation, allowing for natural follow-up questions and pronoun resolution.
*   **📚 Source Citing:** Every AI answer is accompanied by a "Show Sources" button, allowing users to instantly verify the information against the original document text.
*   **💡 Proactive Suggestions:** After answering, the AI suggests relevant follow-up questions to guide the user's exploration of the document.
*   **📥 AI-Powered PDF Export:** A "Summarizer Agent" transforms the entire chat history into a structured, well-formatted report and exports it as a downloadable PDF.
*   **📱 Fully Responsive UI:** The sleek, professional interface is built with TailwindCSS and is optimized for both desktop and mobile use.

## Tech Stack

*   **Frontend:**
    *   Framework: **React** (with Vite)
    *   Styling: **TailwindCSS**
    *   API Communication: **Axios**, Fetch API
*   **Backend:**
    *   Framework: **FastAPI**
    *   Server: **Uvicorn**, Gunicorn
*   **AI & Database:**
    *   AI Models: **Google Gemini API** (for embeddings, generation, and summarization)
    *   Vector Store: **ChromaDB** (in-memory for deployed version)
*   **Deployment & DevOps:**
    *   Version Control: **Git & GitHub**
    *   Frontend Hosting: **Vercel**
    *   Backend Hosting: **Render**
    *   CI/CD: Automated deployments via GitHub webhooks

---

## Getting Started: Running Locally

Follow these steps to set up and run the project on your local machine.

### Prerequisites

Ensure you have the following software installed:
*   **Git**
*   **Python 3.10+** (and `pip`)
*   **Node.js 18+** (and `npm`)
*   **wkhtmltopdf:** Required for the PDF export feature.
    *   Download from the [official site](https://wkhtmltopdf.org/downloads.html).
    *   **Important for Windows users:** You must add the `bin` folder (e.g., `C:\Program Files\wkhtmltopdf\bin`) to your system's PATH Environment Variable.

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-github-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Configure Backend Environment**
    *   **Create `.env` file:** In the project root, create a file named `.env`.
    *   **Get API Key:** Get your API key from [Google AI Studio](https://aistudio.google.com/).
    *   **Add Key to `.env`:**
      ```env
      # /.env
      GOOGLE_API_KEY=AIzaSy...your_secret_api_key_here...
      ```
    *   **Set up Python Virtual Environment:**
      ```bash
      python -m venv venv
      # On Windows
      .\venv\Scripts\activate
      # On macOS/Linux
      source venv/bin/activate
      ```
    *   **Install Python Dependencies:**
      ```bash
      pip install -r requirements.txt
      ```

3.  **Configure Frontend Environment**
    *   **Navigate to the frontend folder:**
      ```bash
      cd frontend
      ```
    *   **Create `.env.local` file:** Inside the `frontend` folder, create a file named `.env.local`.
    *   **Add Backend URL to `.env.local`:**
      ```env
      # /frontend/.env.local
      VITE_API_BASE_URL=http://127.0.0.1:8000
      ```
    *   **Install Frontend Dependencies:**
      ```bash
      npm install
      ```

### Running the Application

You will need **two separate terminals** running at the same time.

1.  **Terminal 1: Start the Backend**
    *   Navigate to the project's **root directory**.
    *   Activate the virtual environment (`.\venv\Scripts\activate`).
    *   Run Uvicorn:
      ```bash
      uvicorn backend.main:app --reload
      ```
    *   The backend will be running at `http://127.0.0.1:8000`.

2.  **Terminal 2: Start the Frontend**
    *   Navigate to the **`frontend` directory**.
    *   Run Vite:
      ```bash
      npm run dev
      ```
    *   The frontend will be running at `http://localhost:5173`.

**You can now open `http://localhost:5173` in your browser to use the app!**

