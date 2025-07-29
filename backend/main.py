from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import openai
from openai import OpenAI
import git
import os
import re
import sqlite3
import json
from datetime import datetime, date
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chronicler",
    description="Generate user-friendly changelogs from Git commits using AI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY not set. AI features will be disabled.")
    client = None

# Database setup
DB_PATH = "changelog.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS changelogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            raw_commits TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP,
            is_published BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class CommitInfo(BaseModel):
    hash: str
    message: str
    author: str
    date: str
    files: List[str] = []

class GenerateChangelogRequest(BaseModel):
    repo_path: str = Field(default=".", description="Path to Git repository")
    days: Optional[int] = Field(default=7, description="Number of days to look back")
    from_commit: Optional[str] = Field(default=None, description="Start commit hash")
    to_commit: Optional[str] = Field(default=None, description="End commit hash")
    exclude_patterns: List[str] = Field(default=[
        r"^chore:",
        r"^docs:",
        r"^test:",
        r"Merge pull request",
        r"^ci:",
        r"^build:"
    ])

class PublishChangelogRequest(BaseModel):
    version: str
    title: str
    content: str
    raw_commits: str

class ChangelogResponse(BaseModel):
    id: int
    version: str
    title: str
    content: str
    created_at: str
    published_at: Optional[str]
    is_published: bool

class GeneratedChangelog(BaseModel):
    title: str
    content: str
    raw_commits: List[CommitInfo]
    summary: Dict[str, Any]

# AI Configuration
CHANGELOG_PROMPT = """
You are an expert technical writer creating user-facing changelogs for developer tools.

Given these Git commits, create a changelog that:
1. Groups changes into logical categories (Features, Bug Fixes, Improvements, Breaking Changes)
2. Writes descriptions from the END USER perspective (not internal dev details)
3. Focuses on what users can now do differently or what problems are solved
4. Excludes purely internal changes (refactoring, testing, CI/CD)
5. Uses clear, concise language that non-technical users can understand

Format the output as clean Markdown with:
- Clear category headers with emojis
- Bullet points for each significant change
- Brief descriptions focusing on user impact

Commits to process:
{commits}

Generate a user-focused changelog in Markdown format:
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_git_commits(repo_path: str, days: int = 7, from_commit: str = None, to_commit: str = None) -> List[CommitInfo]:
    """Extract commits from Git repository"""
    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        raise HTTPException(status_code=400, detail="Invalid Git repository path")
    
    commits = []
    
    if from_commit and to_commit:
        # Get commits between specific hashes
        commit_range = f"{from_commit}..{to_commit}"
        git_commits = list(repo.iter_commits(commit_range))
    else:
        # Get commits from last N days (default is 7)
        from datetime import timedelta
        since_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        since_date = since_date - timedelta(days=days)
        git_commits = list(repo.iter_commits(since=since_date))
    
    for commit in git_commits:
        # Get files changed in this commit
        files = []
        try:
            if commit.parents:
                files = [item.a_path for item in commit.diff(commit.parents[0])]
        except:
            pass
            
        commits.append(CommitInfo(
            hash=commit.hexsha[:8],
            message=commit.message.strip(),
            author=str(commit.author),
            date=commit.committed_datetime.isoformat(),
            files=files
        ))
    
    return commits

def filter_commits(commits: List[CommitInfo], exclude_patterns: List[str]) -> List[CommitInfo]:
    """Filter out commits matching exclude patterns"""
    filtered = []
    
    for commit in commits:
        should_exclude = False
        for pattern in exclude_patterns:
            if re.search(pattern, commit.message, re.IGNORECASE):
                should_exclude = True
                break
        
        if not should_exclude:
            filtered.append(commit)
    
    return filtered

def generate_ai_changelog(commits: List[CommitInfo]) -> str:
    """Use OpenAI to generate user-friendly changelog"""
    if not openai_api_key:
        # Fallback to simple formatting if no API key
        logger.error("No OpenAI API key found. Falling back to simple changelog generation.")
        return generate_simple_changelog(commits)
    
    commits_text = ""
    for commit in commits:
        files_text = f" (Files: {', '.join(commit.files[:5])})" if commit.files else ""
        commits_text += f"- {commit.hash}: {commit.message}{files_text}\n"
    
    try:
        # Using the new OpenAI API format (v1.0.0+)
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert technical writer specializing in user-facing changelogs for developer tools."},
                {"role": "user", "content": CHANGELOG_PROMPT.format(commits=commits_text)}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        logger.info("Generated changelog.")
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"OpenAI API error: {e}\n{error_traceback}")
        # Fall back to simple changelog generation
        return generate_simple_changelog(commits)

def generate_simple_changelog(commits: List[CommitInfo]) -> str:
    """Fallback changelog generation without AI"""
    features = []
    fixes = []
    improvements = []
    other = []
    
    for commit in commits:
        msg = commit.message.lower()
        if any(word in msg for word in ['feat', 'feature', 'add', 'new']):
            features.append(f"- {commit.message}")
        elif any(word in msg for word in ['fix', 'bug', 'resolve', 'patch']):
            fixes.append(f"- {commit.message}")
        elif any(word in msg for word in ['improve', 'enhance', 'update', 'optimize']):
            improvements.append(f"- {commit.message}")
        else:
            other.append(f"- {commit.message}")
    
    changelog = ""
    if features:
        changelog += "## 🚀 New Features\n" + "\n".join(features) + "\n\n"
    if fixes:
        changelog += "## 🐛 Bug Fixes\n" + "\n".join(fixes) + "\n\n"
    if improvements:
        changelog += "## 💡 Improvements\n" + "\n".join(improvements) + "\n\n"
    if other:
        changelog += "## 📝 Other Changes\n" + "\n".join(other) + "\n\n"
    
    return changelog.strip()

@app.post("/api/generate", response_model=GeneratedChangelog)
async def generate_changelog(request: GenerateChangelogRequest):
    """Generate a changelog from Git commits"""
    try:
        # Get commits from Git
        commits = get_git_commits(
            request.repo_path,
            request.days,
            request.from_commit,
            request.to_commit
        )
        
        if not commits:
            raise HTTPException(status_code=404, detail="No commits found in the specified range")
        
        # Filter commits
        filtered_commits = filter_commits(commits, request.exclude_patterns)
        
        if not filtered_commits:
            raise HTTPException(status_code=404, detail="No relevant commits found after filtering")
        
        # Generate changelog content
        changelog_content = generate_ai_changelog(filtered_commits)
        
        # Create title based on date range
        if len(filtered_commits) > 0:
            latest_date = datetime.fromisoformat(filtered_commits[0].date.replace('Z', '+00:00'))
            title = f"Changes - {latest_date.strftime('%B %d, %Y')}"
        else:
            title = f"Changes - {datetime.now().strftime('%B %d, %Y')}"
        
        # Summary stats
        summary = {
            "total_commits": len(commits),
            "filtered_commits": len(filtered_commits),
            "authors": list(set(commit.author for commit in filtered_commits)),
            "date_range": {
                "from": filtered_commits[-1].date if filtered_commits else None,
                "to": filtered_commits[0].date if filtered_commits else None
            }
        }
        
        return GeneratedChangelog(
            title=title,
            content=changelog_content,
            raw_commits=filtered_commits,
            summary=summary
        )
        
    except git.exc.GitError as e:
        raise HTTPException(status_code=400, detail=f"Git error: {str(e)}")
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error generating changelog: {e}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}\nTraceback: {error_traceback}")

@app.post("/api/publish", response_model=ChangelogResponse)
async def publish_changelog(request: PublishChangelogRequest):
    """Publish a changelog to the public site"""
    conn = get_db()
    
    try:
        # Check if version already exists
        existing = conn.execute(
            "SELECT id FROM changelogs WHERE version = ?",
            (request.version,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Version {request.version} already exists")
        
        # Insert new changelog
        cursor = conn.execute('''
            INSERT INTO changelogs (version, title, content, raw_commits, published_at, is_published)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.version,
            request.title,
            request.content,
            request.raw_commits,
            datetime.now().isoformat(),
            True
        ))
        
        changelog_id = cursor.lastrowid
        conn.commit()
        
        # Return the created changelog
        changelog = conn.execute(
            "SELECT * FROM changelogs WHERE id = ?",
            (changelog_id,)
        ).fetchone()
        
        return ChangelogResponse(
            id=changelog['id'],
            version=changelog['version'],
            title=changelog['title'],
            content=changelog['content'],
            created_at=changelog['created_at'],
            published_at=changelog['published_at'],
            is_published=bool(changelog['is_published'])
        )
        
    finally:
        conn.close()

@app.get("/api/changelog", response_model=List[ChangelogResponse])
async def get_changelogs(published_only: bool = True):
    """Get all published changelogs"""
    conn = get_db()
    
    try:
        query = "SELECT * FROM changelogs"
        params = []
        
        if published_only:
            query += " WHERE is_published = ?"
            params.append(True)
        
        query += " ORDER BY created_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        
        changelogs = []
        for row in rows:
            changelogs.append(ChangelogResponse(
                id=row['id'],
                version=row['version'],
                title=row['title'],
                content=row['content'],
                created_at=row['created_at'],
                published_at=row['published_at'],
                is_published=bool(row['is_published'])
            ))
        
        return changelogs
        
    finally:
        conn.close()

@app.get("/api/changelog/{version}", response_model=ChangelogResponse)
async def get_changelog_by_version(version: str):
    """Get a specific changelog by version"""
    conn = get_db()
    
    try:
        row = conn.execute(
            "SELECT * FROM changelogs WHERE version = ? AND is_published = ?",
            (version, True)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Changelog not found")
        
        return ChangelogResponse(
            id=row['id'],
            version=row['version'],
            title=row['title'],
            content=row['content'],
            created_at=row['created_at'],
            published_at=row['published_at'],
            is_published=bool(row['is_published'])
        )
        
    finally:
        conn.close()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(openai.api_key)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)