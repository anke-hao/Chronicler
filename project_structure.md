# Chronicler - Project Structure

## Directory Structure

```
ai-changelog-generator/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── changelog.db (created automatically)
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   └── index.css
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── package.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── nginx.conf
└── cli/
    ├── changelog_gen.py
    ├── setup.py
    └── requirements.txt
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ai-changelog-generator
```

### 2. Environment Setup

Create `.env` file in the root directory:

```bash
# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Custom configuration
API_BASE_URL=http://localhost:8000
PUBLIC_URL=http://localhost
```

### 3. Option A: Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 4. Option B: Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### CLI Tool
```bash
cd cli
pip install -e .
changelog-gen --help
```

## CLI Usage Examples

### Initialize in your project
```bash
cd your-project
changelog-gen init
```

### Generate changelog
```bash
# Last 7 days
changelog-gen generate

# Last 30 days  
changelog-gen generate --days 30

# Between specific commits
changelog-gen generate --from abc123 --to def456

# Preview without saving
changelog-gen generate --preview
```

### Publish changelog
```bash
# Interactive mode
changelog-gen publish --version v1.2.0

# From file
changelog-gen publish --version v1.2.0 --file CHANGELOG.md

# With custom title
changelog-gen publish --version v1.2.0 --title "Major Update"
```

### Other commands
```bash
# List published changelogs
changelog-gen list

# Show specific version
changelog-gen show v1.2.0

# Check server status
changelog-gen server

# Configure settings
changelog-gen config
```

## Configuration

### Project Configuration (`.changelog-config.json`)

```json
{
  "api_base_url": "http://localhost:8000",
  "editor": "code",
  "public_url": "https://changelog.yourapp.com",
  "exclude_patterns": [
    "^chore:",
    "^docs:",
    "^test:",
    "Merge pull request",
    "^ci:",
    "^build:"
  ],
  "categories": {
    "features": "🚀 New Features",
    "bugfixes": "🐛 Bug Fixes",
    "improvements": "💡 Improvements",
    "breaking": "⚠️ Breaking Changes"
  }
}
```

## API Endpoints

### Developer API
- `POST /api/generate` - Generate changelog from commits
- `POST /api/publish` - Publish changelog
- `GET /api/health` - Health check

### Public API
- `GET /api/changelog` - List all changelogs
- `GET /api/changelog/{version}` - Get specific changelog

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### CLI Development
```bash
cd cli
pip install -e .
# CLI now available as `changelog-gen`
```

## Deployment

### Production Docker
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# With custom domain
DOMAIN=changelog.yourapp.com docker-compose up -d
```

### Individual Service Deployment

#### Backend (Railway/Heroku)
```bash
cd backend
# Set OPENAI_API_KEY environment variable
# Deploy main.py with requirements.txt
```

#### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy dist/ directory
# Set API_BASE_URL to your backend URL
```

## Troubleshooting

### Common Issues

1. **OpenAI API Error**
   - Ensure OPENAI_API_KEY is set
   - Check API key validity
   - Verify sufficient credits

2. **Git Repository Error**
   - Ensure you're in a Git repository
   - Check if repository has commits

3. **Connection Error**
   - Verify backend is running on port 8000
   - Check firewall settings
   - Ensure correct API_BASE_URL

4. **Permission Errors**
   - Check file permissions for database
   - Ensure write access to project directory

### Logs and Debugging

```bash
# Docker logs
docker-compose logs backend
docker-compose logs frontend

# Backend logs
tail -f backend.log

# Enable debug mode
export DEBUG=1
uvicorn main:app --reload --log-level debug
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### CLI Tests
```bash
cd cli
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## Security Considerations

- Store OpenAI API keys securely
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regularly update dependencies
- Validate user inputs
- Implement rate limiting for public APIs

## Performance Optimization

- Enable gzip compression
- Use CDN for static assets
- Implement caching strategies
- Monitor API response times
- Optimize database queries
- Use connection pooling

## Monitoring

- Set up health checks
- Monitor API response times
- Track error rates
- Log important events
- Set up alerts for failures