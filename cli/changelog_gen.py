#!/usr/bin/env python3
"""
AI-Powered Changelog Generator CLI
A developer tool for generating user-friendly changelogs from Git commits.
"""

import click
import requests
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.table import Table
from typing import Optional, Dict, Any

console = Console()

# Configuration
DEFAULT_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "editor": os.environ.get("EDITOR", "nano"),
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

CONFIG_FILE = ".changelog-config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
    
    return config

def save_config(config: Dict[str, Any]):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        console.print(f"[green]Configuration saved to {CONFIG_FILE}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving config: {e}[/red]")

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API request to the backend"""
    config = load_config()
    url = f"{config['api_base_url']}/api/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to the changelog API server.[/red]")
        console.print("Make sure the backend server is running on http://localhost:8000")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]API Error: {e.response.status_code} - {e.response.text}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

@click.group()
@click.version_option(version="1.0.0", prog_name="changelog-gen")
def cli():
    """
    AI-Powered Changelog Generator
    
    Generate user-friendly changelogs from Git commits using AI.
    """
    pass

@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to look back for commits")
@click.option("--from-commit", "--from", help="Start commit hash")
@click.option("--to-commit", "--to", help="End commit hash")
@click.option("--repo-path", "-r", default=".", help="Path to Git repository")
@click.option("--preview", "-p", is_flag=True, help="Preview without saving")
@click.option("--output", "-o", help="Output file path")
def generate(days: int, from_commit: Optional[str], to_commit: Optional[str], 
             repo_path: str, preview: bool, output: Optional[str]):
    """Generate a changelog from Git commits"""
    
    config = load_config()
    
    # Prepare request data
    request_data = {
        "repo_path": repo_path,
        "days": days,
        "exclude_patterns": config["exclude_patterns"]
    }
    
    if from_commit:
        request_data["from_commit"] = from_commit
    if to_commit:
        request_data["to_commit"] = to_commit
    
    # Show what we're doing
    if from_commit and to_commit:
        console.print(f"[blue]Generating changelog from {from_commit} to {to_commit}...[/blue]")
    else:
        console.print(f"[blue]Generating changelog for the last {days} days...[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing commits and generating changelog...", total=None)
        
        # Make API request
        result = make_api_request("generate", "POST", request_data)
    
    # Display summary
    summary = result["summary"]
    table = Table(title="Changelog Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Commits Found", str(summary["total_commits"]))
    table.add_row("Relevant Commits", str(summary["filtered_commits"]))
    table.add_row("Authors", ", ".join(summary["authors"]))
    
    console.print(table)
    console.print()
    
    # Display generated changelog
    console.print(Panel(
        Markdown(result["content"]),
        title=f"Generated Changelog: {result['title']}",
        border_style="green"
    ))
    
    if preview:
        console.print("[yellow]Preview mode - changelog not saved[/yellow]")
        return
    
    # Save or edit changelog
    if output:
        # Save to specified file
        with open(output, 'w', encoding='utf-8') as f:
            f.write(f"# {result['title']}\n\n{result['content']}")
        console.print(f"[green]Changelog saved to {output}[/green]")
    else:
        # Open in editor for review
        if Confirm.ask("Would you like to review and edit the changelog?"):
            edit_changelog(result['title'], result['content'])
        # Save to temporary file and show path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(f"# {result['title']}\n\n{result['content']}")
            temp_path = f.name
        console.print(f"[green]Changelog saved to {temp_path}[/green]")

def edit_changelog(title: str, content: str) -> tuple[str, str]:
    """Open changelog in editor for review"""
    config = load_config()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(f"# {title}\n\n{content}")
        temp_path = f.name
    
    try:
        # Open in editor
        subprocess.run([config["editor"], temp_path], check=True)
        
        # Read back the edited content
        with open(temp_path, 'r', encoding='utf-8') as f:
            edited_content = f.read()
        
        # Parse title and content
        lines = edited_content.split('\n')
        if lines[0].startswith('# '):
            edited_title = lines[0][2:].strip()
            edited_content = '\n'.join(lines[2:]).strip()
        else:
            edited_title = title
        
        os.unlink(temp_path)
        return edited_title, edited_content
        
    except subprocess.CalledProcessError:
        console.print("[red]Error opening editor[/red]")
        os.unlink(temp_path)
        return title, content
    except Exception as e:
        console.print(f"[red]Error editing changelog: {e}[/red]")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return title, content

@cli.command()
@click.option("--version", "-v", required=True, help="Version number for the changelog")
@click.option("--title", "-t", help="Custom title for the changelog")
@click.option("--file", "-f", help="Changelog file to publish")
@click.option("--repo-path", "-r", default=".", help="Path to Git repository")
def publish(version: str, title: Optional[str], file: Optional[str], repo_path: str):
    """Publish a changelog to the public website"""
    
    if file:
        # Read changelog from file
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse title from file if not provided
            if not title:
                lines = content.split('\n')
                if lines[0].startswith('# '):
                    title = lines[0][2:].strip()
                    content = '\n'.join(lines[2:]).strip()
                else:
                    title = f"Release {version}"
        except FileNotFoundError:
            console.print(f"[red]Error: File {file} not found[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            sys.exit(1)
    else:
        # Interactive mode - generate and edit
        console.print("[blue]No file specified. Generating changelog...[/blue]")
        days = click.prompt("Number of days to look back", default=7, type=int)
        
        request_data = {
            "repo_path": repo_path,
            "days": days,
            "exclude_patterns": load_config()["exclude_patterns"]
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating changelog...", total=None)
            result = make_api_request("generate", "POST", request_data)
        
        # Let user edit
        title = title or result["title"]
        content = result["content"]
        
        if Confirm.ask("Would you like to review and edit the changelog before publishing?"):
            title, content = edit_changelog(title, content)
    
    # Confirm publication
    console.print(f"\n[bold]About to publish:[/bold]")
    console.print(f"[cyan]Version:[/cyan] {version}")
    console.print(f"[cyan]Title:[/cyan] {title}")
    console.print(f"[cyan]Content length:[/cyan] {len(content)} characters")
    
    if not Confirm.ask("\nProceed with publication?"):
        console.print("[yellow]Publication cancelled[/yellow]")
        return
    
    # Publish to API
    request_data = {
        "version": version,
        "title": title,
        "content": content,
        "raw_commits": json.dumps([])  # TODO: Include raw commits if available
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Publishing changelog...", total=None)
        result = make_api_request("publish", "POST", request_data)
    
    console.print(f"[green]✅ Changelog published successfully![/green]")
    console.print(f"[cyan]Version:[/cyan] {result['version']}")
    console.print(f"[cyan]Published at:[/cyan] {result['published_at']}")
    
    # Show public URL if configured
    config = load_config()
    if "public_url" in config:
        public_url = f"{config['public_url']}/{version}"
        console.print(f"[cyan]Public URL:[/cyan] {public_url}")

@cli.command()
def list():
    """List all published changelogs"""
    
    console.print("[blue]Fetching published changelogs...[/blue]")
    changelogs = make_api_request("changelog")
    
    if not changelogs:
        console.print("[yellow]No published changelogs found[/yellow]")
        return
    
    table = Table(title="Published Changelogs")
    table.add_column("Version", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Published", style="yellow")
    
    for changelog in changelogs:
        published_date = changelog['published_at'][:10] if changelog['published_at'] else 'N/A'
        table.add_row(
            changelog['version'],
            changelog['title'][:50] + "..." if len(changelog['title']) > 50 else changelog['title'],
            published_date
        )
    
    console.print(table)

@cli.command()
@click.argument("version")
def show(version: str):
    """Show a specific published changelog"""
    
    console.print(f"[blue]Fetching changelog for version {version}...[/blue]")
    
    try:
        changelog = make_api_request(f"changelog/{version}")
    except SystemExit:
        console.print(f"[red]Changelog for version {version} not found[/red]")
        return
    
    console.print(Panel(
        Markdown(changelog['content']),
        title=f"{changelog['title']} (v{changelog['version']})",
        subtitle=f"Published: {changelog['published_at'][:10]}",
        border_style="green"
    ))

@cli.command()
def config():
    """Configure the changelog generator"""
    
    current_config = load_config()
    
    console.print("[bold]Current Configuration:[/bold]")
    console.print(json.dumps(current_config, indent=2))
    console.print()
    
    if not Confirm.ask("Would you like to modify the configuration?"):
        return
    
    new_config = current_config.copy()
    
    # API Base URL
    new_url = Prompt.ask(
        "API Base URL",
        default=current_config["api_base_url"]
    )
    new_config["api_base_url"] = new_url
    
    # Editor
    new_editor = Prompt.ask(
        "Preferred editor",
        default=current_config["editor"]
    )
    new_config["editor"] = new_editor
    
    # Public URL
    current_public_url = current_config.get("public_url", "")
    new_public_url = Prompt.ask(
        "Public changelog URL (optional)",
        default=current_public_url
    )
    if new_public_url:
        new_config["public_url"] = new_public_url
    
    save_config(new_config)

@cli.command()
def init():
    """Initialize changelog generator in current directory"""
    
    console.print("[bold]Initializing Changelog Generator[/bold]")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        console.print("[red]Error: Not a Git repository. Please run 'git init' first.[/red]")
        sys.exit(1)
    
    # Create configuration file
    config = DEFAULT_CONFIG.copy()
    
    # Ask for public URL
    public_url = Prompt.ask(
        "Public changelog URL (optional, can be set later)",
        default=""
    )
    if public_url:
        config["public_url"] = public_url
    
    # Ask for custom exclude patterns
    if Confirm.ask("Would you like to customize commit exclude patterns?"):
        console.print("\nCurrent exclude patterns:")
        for i, pattern in enumerate(config["exclude_patterns"]):
            console.print(f"  {i+1}. {pattern}")
        
        console.print("\nAdd additional patterns (one per line, empty line to finish):")
        while True:
            pattern = Prompt.ask("Pattern (regex)", default="")
            if not pattern:
                break
            config["exclude_patterns"].append(pattern)
    
    save_config(config)
    
    console.print("[green]✅ Changelog generator initialized![/green]")
    console.print("\nNext steps:")
    console.print("1. Start the backend server: uvicorn main:app --reload")
    console.print("2. Generate your first changelog: changelog-gen generate")
    console.print("3. Publish it: changelog-gen publish --version v1.0.0")

@cli.command()
def server():
    """Check server status and connection"""
    
    config = load_config()
    
    try:
        health = make_api_request("health")
        
        console.print("[green]✅ Server is running![/green]")
        console.print(f"[cyan]URL:[/cyan] {config['api_base_url']}")
        console.print(f"[cyan]Status:[/cyan] {health['status']}")
        console.print(f"[cyan]OpenAI Configured:[/cyan] {'Yes' if health['openai_configured'] else 'No'}")
        console.print(f"[cyan]Timestamp:[/cyan] {health['timestamp']}")
        
        if not health['openai_configured']:
            console.print("\n[yellow]⚠️  OpenAI API key not configured. AI features will be limited.[/yellow]")
            console.print("Set the OPENAI_API_KEY environment variable to enable AI-powered changelog generation.")
        
    except SystemExit:
        console.print("[red]❌ Server is not running or not accessible[/red]")
        console.print(f"Expected server at: {config['api_base_url']}")
        console.print("\nTo start the server:")
        console.print("1. cd to the backend directory")
        console.print("2. pip install -r requirements.txt")
        console.print("3. uvicorn main:app --reload --port 8000")

if __name__ == "__main__":
    cli()
        