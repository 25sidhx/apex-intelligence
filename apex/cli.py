"""
APEX Unified CLI: Terminal control center for Embedded Intelligence & Engineering.
"""

import typer
import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

from apex.intelligence.arxiv_radar import fetch_recent_papers
from apex.intelligence.github_radar import fetch_trending_repos
from apex.engineering.scaffolds import scaffold_project, TEMPLATES
from apex.content.humanizer import audit_text, clean_text
from apex.utils.context_filter import filter_compiler_output
from apex.utils.worktree_mgr import WorktreeManager
from apex.reporting.daily import generate_daily_report
from apex.reporting.weekly import generate_weekly_report

app = typer.Typer(help="APEX: Autonomous Tech Intelligence & Embedded Engineering System")
console = Console(safe_box=True)


@app.command()
def scan(
    category: str = typer.Option("all", help="Target radar: arxiv, github, or all"),
    limit: int = typer.Option(5, help="Number of items to return")
):
    """
    Scouts arXiv and GitHub for recent robotics, drone, and embedded developments.
    """
    console.print("\n[bold cyan][APEX RADAR] Scanning High-Signal Engineering Sources...[/bold cyan]\n")

    if category in ["all", "arxiv"]:
        papers = fetch_recent_papers(max_results=limit * 2)
        table = Table(title="[bold green]Top Research Papers (arXiv)[/bold green]", show_lines=True)
        table.add_column("Score", justify="center", style="bold yellow", width=6)
        table.add_column("Title", style="bold white")
        table.add_column("Keywords", style="magenta")
        table.add_column("Link", style="blue")

        for p in papers[:limit]:
            table.add_row(
                f"{p['relevance_score']}/10",
                p['title'],
                ", ".join(p['matched_keywords']),
                p['link']
            )
        console.print(table)
        console.print("")

    if category in ["all", "github"]:
        repos = fetch_trending_repos(max_results=limit)
        if repos:
            table = Table(title="[bold green]Active Open-Source Projects (GitHub)[/bold green]", show_lines=True)
            table.add_column("Stars", justify="center", style="bold yellow", width=8)
            table.add_column("Repo", style="bold white")
            table.add_column("Description", style="dim")
            table.add_column("URL", style="blue")

            for r in repos:
                table.add_row(
                    str(r['stars']),
                    r['name'],
                    r['description'][:80] + "..." if len(r['description']) > 80 else r['description'],
                    r['html_url']
                )
            console.print(table)
            console.print("")


from apex.reporting.telegram import send_telegram_message

@app.command()
def daily(
    limit: int = typer.Option(5, help="Number of items to report"),
    telegram: bool = typer.Option(False, "--telegram", help="Send report to configured Telegram chat")
):
    """Generates the high-signal daily intelligence digest (Section 11)."""
    console.print("\n[bold cyan][APEX] Running Daily Intelligence Scan...[/bold cyan]")
    papers = fetch_recent_papers(max_results=limit*2)
    repos = fetch_trending_repos(max_results=limit*2)
    report = generate_daily_report(papers, repos, limit=limit)
    
    out_path = Path(f"projects/daily_report_{datetime.date.today().isoformat()}.md")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    
    console.print(f"[bold green]✓ Daily Report saved to:[/bold green] {out_path.resolve()}")
    
    if telegram:
        console.print("[bold cyan]Pushing newsletter to Telegram...[/bold cyan]")
        if send_telegram_message(report):
            console.print("[bold green]✓ Successfully sent to Telegram![/bold green]")
        else:
            console.print("[bold red]✗ Failed to send to Telegram. Check ~/.apex/profile.json[/bold red]")


@app.command()
def weekly(
    telegram: bool = typer.Option(False, "--telegram", help="Send report to configured Telegram chat")
):
    """Generates the comprehensive weekly engineering intelligence report (Section 12)."""
    console.print("\n[bold cyan][APEX] Aggregating Weekly Intelligence...[/bold cyan]")
    papers = fetch_recent_papers(max_results=20)
    repos = fetch_trending_repos(max_results=20)
    report = generate_weekly_report(papers, repos)
    
    out_path = Path(f"projects/weekly_report_{datetime.date.today().isoformat()}.md")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    
    console.print(f"[bold green]✓ Weekly Report saved to:[/bold green] {out_path.resolve()}")
    
    if telegram:
        console.print("[bold cyan]Pushing newsletter to Telegram...[/bold cyan]")
        if send_telegram_message(report):
            console.print("[bold green]✓ Successfully sent to Telegram![/bold green]")
        else:
            console.print("[bold red]✗ Failed to send to Telegram. Check ~/.apex/profile.json[/bold red]")


@app.command()
def scaffold(
    template: str = typer.Argument(..., help=f"Template name: {', '.join(TEMPLATES.keys())}"),
    output_dir: str = typer.Option("./project", help="Destination path")
):
    """
    Generates production-ready embedded firmware or ROS 2 drone templates.
    """
    dest = Path(output_dir)
    success = scaffold_project(template, dest)
    if success:
        console.print(f"[bold green]✓ Scaffolding complete:[/bold green] {template} -> [cyan]{dest.resolve()}[/cyan]")
    else:
        console.print(f"[bold red]✗ Invalid template:[/bold red] Choose from {list(TEMPLATES.keys())}")


@app.command()
def humanize(file_path: str = typer.Argument(..., help="Path to text/markdown file")):
    """
    Audits and removes generic AI cliches using blader/humanizer heuristics.
    """
    p = Path(file_path)
    if not p.exists():
        console.print(f"[bold red]File not found:[/bold red] {file_path}")
        return

    content = p.read_text(encoding="utf-8")
    report = audit_text(content)

    console.print(f"\n[bold]Audit Score:[/bold] {report['score']}/10 (Clean: {report['is_clean']})")
    if not report['is_clean']:
        console.print(f"[yellow]Flagged {report['cliche_count']} AI cliches:[/yellow]")
        for word, line in report['flagged_instances']:
            console.print(f"  • Line {line}: '[red]{word}[/red]'")
        cleaned = clean_text(content)
        p.write_text(cleaned, encoding="utf-8")
        console.print(f"[bold green]✓ Cleaned file overwritten successfully.[/bold green]\n")


@app.command()
def filter_logs(log_file: str = typer.Argument(..., help="Path to raw compiler log")):
    """
    Compresses massive GCC/PlatformIO/ROS2 logs down to critical errors (mksglu/context-mode).
    """
    p = Path(log_file)
    if not p.exists():
        console.print(f"[bold red]Log file not found:[/bold red] {log_file}")
        return

    raw = p.read_text(encoding="utf-8", errors="ignore")
    compressed = filter_compiler_output(raw)

    console.print("\n[bold green]Context Filter Summary:[/bold green]")
    console.print(f"• Total Lines: {compressed['total_lines']}")
    console.print(f"• Error Count: {compressed['error_count']}")
    console.print(f"• Warning Count: {compressed['warning_count']}")
    console.print(f"• Token Reduction: [bold yellow]{compressed['compression_ratio']}[/bold yellow]\n")

    if compressed["critical_errors"]:
        console.print("[bold red]Critical Errors:[/bold red]")
        for err in compressed["critical_errors"][:15]:
            console.print(f"  [red]✗[/red] {err}")


@app.command()
def worktrees():
    """
    Lists active Git worktrees for parallel agent development (max-sixty/worktrunk).
    """
    mgr = WorktreeManager()
    wt_list = mgr.list_worktrees()
    table = Table(title="[bold green]Active Git Worktrees[/bold green]")
    table.add_column("Path", style="cyan")
    table.add_column("Branch", style="bold white")
    table.add_column("HEAD Commit", style="dim")

    for wt in wt_list:
        table.add_row(wt.get("path", "-"), wt.get("branch", "detached"), wt.get("head", "-")[:7])
    console.print(table)


if __name__ == "__main__":
    app()
