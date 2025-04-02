# XMemory

A modern Python project with FastAPI backend and modern frontend.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher (for frontend)
- Elasticsearch 8.x
- `uv` package manager

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd xmemory
```

2. Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

4. Install dependencies:
```bash
uv pip install -e .
```

5. Copy the environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. Start the backend server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000
API documentation will be available at http://localhost:8000/docs

## Development

### Backend

- The backend is built with FastAPI
- Main application code is in the `app` directory
- API endpoints are organized in the `app/api` directory
- Database models are in `app/models`
- Services are in `app/services`

### Frontend

- The frontend is a modern web application
- Located in the `frontend` directory
- Built with modern web technologies

## Testing

Run tests with:
```bash
pytest
```

## License

MIT License 