# 🌐 Modern Intelligent University LMS

A modular, scalable, AI-native Learning Management System designed for modern universities.

## Features

### Core Modules
- **Course & Content Management** - Create, organize, and publish courses with AI-generated summaries
- **Assessment & Quiz** - AI-generated quizzes with auto-grading and adaptive testing
- **Intelligent Feedback** - AI-assisted email communication with sentiment analysis
- **Social & Collaborative Learning** - Chat, forums, project groups, and peer feedback
- **Smart Search** - Semantic search with natural language queries and RAG pipeline
- **Dashboards & Analytics** - Progress tracking with AI-powered insights and alerts
- **Security & Compliance** - SSO, data encryption, audit logs, and privacy protection

## Architecture

### Frontend
- React with Tailwind CSS
- Modern responsive design
- Multi-device support (desktop, tablet, mobile)

### Backend
- **Django Monolith**: Core LMS functionality (users, courses, permissions, SSO, files, audits)
- **FastAPI Microservices**: 
  - AI-content service
  - AI-assessment service  
  - AI-communication service
  - AI-search service

### Infrastructure
- **Database**: PostgreSQL with pgvector for embeddings
- **Message Bus**: Celery + Redis for task queue
- **File Storage**: S3-compatible storage (MinIO)
- **Cache**: Redis
- **Auth/SSO**: OAuth2, LDAP, Shibboleth integration
- **AI Engine**: LLM, embeddings, ML models
- **Communication**: POP3/IMAP/SMTP integration
- **Deployment**: Docker + Kubernetes ready, Render optimized

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd intelligent-lms
```

2. Set up backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend:
```bash
cd frontend
npm install
```

4. Set up microservices:
```bash
cd microservices
pip install -r requirements.txt
```

5. Configure environment variables (see `.env.example`)

6. Run migrations:
```bash
cd backend
python manage.py migrate
```

7. Start development servers:
```bash
# Backend (Django)
cd backend && python manage.py runserver

# Frontend (React)
cd frontend && npm start

# Microservices
cd microservices && uvicorn main:app --reload
```

## Project Structure

```
intelligent-lms/
├── backend/                 # Django monolithic core
│   ├── apps/
│   │   ├── users/
│   │   ├── courses/
│   │   ├── permissions/
│   │   ├── files/
│   │   └── audits/
│   ├── core/
│   └── manage.py
├── frontend/                # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   └── package.json
├── microservices/           # FastAPI services
│   ├── ai_content/
│   ├── ai_assessment/
│   ├── ai_communication/
│   └── ai_search/
├── deployment/              # Docker & deployment configs
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── k8s/
└── docs/                    # Documentation
```

## Development

### Running Tests
```bash
# Backend tests
cd backend && python manage.py test

# Frontend tests
cd frontend && npm test

# Microservices tests
cd microservices && pytest
```

### Code Style
- Python: Black, isort, flake8
- JavaScript: Prettier, ESLint
- Pre-commit hooks configured

## Deployment

### Render Deployment
The project is optimized for Render deployment with single-link access.

### Docker
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f deployment/k8s/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support, please open an issue or contact the development team.
