# RAG Chatbot Personal Website Project Summary

## Project Overview
Building a personal website with RAG-powered chatbot to showcase ML/AI skills for job applications. Should be a great way to demonstrate end-to-end AI system development.

## How Can I View the Project?
Project will be on my personal website after deployment in late September, all code is visible now, and a live demo is available upon employers' request.

## Project Structure
Personal-RAG-Chatbot/ <br/>
├── README.md (the summarys)<br/> 
├── docs/ (detailed technical decisions)<br/> 
├── backend/ (FastAPI code)<br/> 
├── frontend/ (React code)<br/> 
└── deployment/ (Docker, config files) IN-PROGRESS

## Chosen Tech Stack
- **Vector Store**: Pinecone (managed, reliable, good free tier) ✔️
- **Embeddings**: OpenAI text-embedding-3-small (cost-effective, widely used) ✔️
- **LLM**: OpenAI GPT-4o-mini (cheap, fast, good enough) ✔️
- **Backend**: FastAPI with Python (perfect for ML/AI work) ✔️
- **Caching**: Supabase (PostgreSQL with nice APIs) **IN-PROGRESS**
- **Frontend**: React + TypeScript + Tailwind CSS ✔️
- **Deployment**: Vercel for frontend **IN-PROGRESS

## Overall Project Timeline
2-3 weeks (of work, will take longer) part-time, building incrementally:
1. Basic FastAPI backend
2. OpenAI integration for chat
3. Pinecone vector storage/retrieval
4. React frontend
5. Connect everything and deploy

## Key Learning Outcomes
- RAG implementation and vector databases
- Full-stack development with AI integration
- API design and deployment
- Concrete project for job interviews

## Next Steps
1. Implement Supabase for remote caching
2. Deploy with Vercel
