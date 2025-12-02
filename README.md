# Tumbuhkan Backend

Backend system untuk IoT plant monitoring dengan AI capabilities.

## Features
- 🌱 Sensor data management (CRUD)
- 📡 MQTT integration for real-time data
- 🤖 2 Computer Vision models
- 📊 Random Forest prediction model
- 💬 RAG Chatbot with Gemini AI & HuggingFace embeddings

## Tech Stack
- FastAPI
- MySQL 9.2
- MQTT
- PyTorch / TensorFlow
- Scikit-learn
- Google Gemini AI
- HuggingFace Transformers

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run development server:
```bash
uvicorn app.main:app --reload
```

## Project Structure
```
See folder structure above
```

## API Documentation
After running the server, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
