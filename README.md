# Easy Apply

A full-stack application built with FastAPI and React (Vite).

## Project Structure

```
easy-apply/
├── backend/         # FastAPI backend
│   ├── main.py
│   └── requirements.txt
└── frontend/        # React frontend
    ├── src/
    ├── package.json
    └── vite.config.js
```

## Backend Setup

1. Create a virtual environment (recommended):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server:
```bash
uvicorn main:app --reload
```

The backend will be available at http://localhost:8000

## Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Features

- FastAPI backend with CORS support
- React frontend with Vite
- Chakra UI for modern styling
- Axios for API communication
- Development proxy configuration 