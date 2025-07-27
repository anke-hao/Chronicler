# AI-Powered Changelog Generator

A developer tool that automatically generates user-friendly changelogs from Git commits using AI, with a public-facing website for end users.

## Features

- **Developer CLI Tool**: Generate changelogs from Git commits with a single command
- **AI-Powered Summarization**: Converts technical commits into user-friendly descriptions
- **Public Website**: Clean, minimal interface for users to view changelogs
- **Markdown Support**: Rich formatting for better readability
- **Date Grouping**: Automatically organizes changes by release date
- **Category Classification**: Groups changes by type (Features, Bug Fixes, Improvements, etc.)

## Architecture

### Backend (Python/FastAPI)
- **FastAPI** for REST API
- **OpenAI GPT** for intelligent commit summarization
- **GitPython** for Git repository interaction
- **SQLite** for changelog storage
- **Pydantic** for data validation

### Frontend (React)
- **React** with TypeScript for the public website
- **Tailwind CSS** for styling
- **Markdown rendering** for rich content display
- **Responsive design** for mobile/desktop

### Developer Tool (Python CLI)
- **Click** for command-line interface
- **Rich** for beautiful terminal output
- **Git integration** for automatic commit fetching

## Installation

You can set up the AI Changelog Generator using either Docker (recommended) or a local installation.

### Prerequisites

#### For Docker Setup
- Docker and Docker Compose
- Git
- OpenAI API key

#### For Local Setup
- Python 3.8+
- Node.js 16+
- Git
- OpenAI API key

### Option 1: Docker Setup (Recommended)

1. **Clone the repository and navigate to the project directory**

2. **Create a `.env` file with your OpenAI API key**
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```
   This will start both the backend and frontend services.

4. **Install the CLI tool**
   ```bash
   # From the project root directory
   pip install -e ./cli
   ```

### Option 2: Local Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key-here"  # On Windows, use: set OPENAI_API_KEY=your-api-key-here
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### CLI Tool Setup
```bash
cd cli
pip install -e .
changelog-gen --help
```

## Usage

### Developer Workflow
1. **Generate Changelog**: Run `changelog-gen generate` in your project directory
2. **Review & Edit**: AI-generated changelog opens in your editor for review
3. **Publish**: Run `changelog-gen publish` to make it live on the public site

### CLI Commands

```bash
# First, check the server status (works with both Docker and local setup)
changelog-gen server

# Generate changelog from recent commits
changelog-gen generate --days 7

# Generate changelog between specific commits
changelog-gen generate --from abc123 --to def456

# Publish changelog to public site
changelog-gen publish --version "v1.2.0"

# Publish changelog with a specific repository path (useful with Docker)
changelog-gen publish --version "v1.2.0" --repo-path "/path/to/your/repo"

# Preview without publishing
changelog-gen generate --preview
```

### Working with Docker

When using Docker, the CLI tool needs to know where your Git repository is located. If your repository is outside the Docker container, use the `--repo-path` option to specify its location:

```bash
changelog-gen generate --repo-path "/path/to/your/repo"
```

Make sure the repository path is accessible to the Docker container (may require volume mounting in docker-compose.yml).

## Technical Decisions

### Why FastAPI?
- **Performance**: Async support for handling multiple requests
- **Developer Experience**: Automatic API documentation with Swagger
- **Type Safety**: Built-in Pydantic validation
- **Modern**: Python 3.6+ features and type hints

### Why React for Frontend?
- **Component Reusability**: Modular changelog components
- **State Management**: Easy handling of changelog data
- **SEO Friendly**: Can be easily extended with Next.js for SSR
- **Developer Familiarity**: Widely adopted in developer tool companies

### AI Model Choice (GPT-4)
- **Context Understanding**: Better at understanding code context
- **User-Focused Output**: Excels at converting technical language to user-friendly descriptions
- **Categorization**: Good at classifying changes by type and importance

### Data Storage (SQLite)
- **Simplicity**: No complex setup required
- **Portability**: Easy to backup and migrate
- **Performance**: Sufficient for changelog data patterns
- **Development**: Easy local development setup

## Product Design Decisions

### Developer-First Experience
- **Zero Configuration**: Works out of the box with sensible defaults
- **Git Integration**: Leverages existing Git workflow
- **Editor Integration**: Opens generated changelog in developer's preferred editor
- **Preview Mode**: Allows review before publishing

### User-Focused Public Site
- **Clean Design**: Minimal interface focusing on content
- **Mobile Responsive**: Developers often check updates on mobile
- **Fast Loading**: Optimized for quick reference
- **Search & Filter**: Easy to find specific changes

### AI Prompt Engineering
- **Context Awareness**: Includes file paths and diff context
- **User Perspective**: Explicitly asks AI to think from end-user viewpoint
- **Categorization**: Structured output with consistent formatting
- **Relevance Filtering**: Filters out internal/dev-only changes

## API Endpoints

### Developer API
- `POST /api/generate` - Generate changelog from commits
- `POST /api/publish` - Publish changelog to public site
- `GET /api/preview/{id}` - Preview generated changelog

### Public API
- `GET /api/changelog` - Get all published changelogs
- `GET /api/changelog/{version}` - Get specific version changelog

## Example Generated Changelog

```markdown
# v1.2.0 - 2024-01-15

## 🚀 New Features
- **API Rate Limiting**: Added configurable rate limiting to prevent abuse
- **Webhook Support**: You can now receive real-time notifications via webhooks
- **Bulk Operations**: Process multiple records in a single API call

## 🐛 Bug Fixes
- Fixed pagination issue when sorting by date
- Resolved memory leak in background job processor
- Fixed CSV export for large datasets

## 💡 Improvements
- Improved API response times by 40%
- Better error messages with actionable suggestions
- Enhanced documentation with more code examples
```

## Configuration

Create a `.changelog-config.json` in your project root:

```json
{
  "ai_model": "gpt-4",
  "categories": {
    "features": "🚀 New Features",
    "bugfixes": "🐛 Bug Fixes", 
    "improvements": "💡 Improvements",
    "breaking": "⚠️ Breaking Changes"
  },
  "exclude_patterns": [
    "^chore:",
    "^docs:",
    "^test:",
    "Merge pull request"
  ],
  "public_url": "https://your-changelog-site.com"
}
```

## Production Deployment

### Hosting the Public Changelog Site

To deploy the changelog site for public access:

1. **Configure your domain in the CLI**:
   ```bash
   changelog-gen config
   # When prompted, set the public URL to your domain
   ```

2. **Deploy the frontend**:
   ```bash
   cd frontend
   npm run build
   # Deploy the dist/ folder to your hosting service (Vercel, Netlify, etc.)
   ```

3. **Deploy the backend API**:
   - Use the Docker setup described in the installation section, or
   - Deploy to a cloud provider that supports Docker containers

4. **Configure CORS** in the backend to allow requests from your frontend domain

Once deployed, users can access your changelogs at `your-domain.com/v1.0.0` (where v1.0.0 is the version number).

### Public URL Configuration

To configure the public URL for your changelogs:

```bash
# Set during initialization
changelog-gen init
# When prompted, enter your public URL (e.g., https://changelogs.yourapp.com)

# Or update existing configuration
changelog-gen config
# When prompted, update the public URL
```

This URL will be displayed when publishing changelogs, allowing users to access them via `your-public-url/version-number`.

## Future Enhancements

- **GitHub Integration**: Direct integration with GitHub releases
- **Slack/Discord Notifications**: Auto-post changelog updates
- **Multiple AI Providers**: Support for Claude, Gemini, etc.
- **Custom Templates**: Customizable changelog formats
- **Analytics**: Track which changes users engage with most
- **Internationalization**: Multi-language changelog support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
