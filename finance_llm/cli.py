import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from .rag_engine import FinanceRAGEngine
from . import ingestion
from . import config

app = typer.Typer(help="Finance LLM — Your 80-year Wall Street expert")
console = Console()
rag = FinanceRAGEngine()


@app.command()
def query(question: str, k: int = 5):
    """Ask the finance expert a question"""
    with console.status("[bold green]Analyzing..."):
        result = rag.query(question, k=k)

    console.print(Panel(Markdown(result["answer"]), title="Answer", border_style="green"))

    if result["sources"]:
        table = Table(title="Sources", show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Relevance", style="yellow")
        table.add_column("Preview", style="white")
        for s in result["sources"]:
            src = s["metadata"].get("title", s["metadata"].get("source", "unknown"))
            table.add_row(
                src[:50],
                str(s["relevance_score"]),
                s["content"][:100] + "...",
            )
        console.print(table)


@app.command()
def ingest(
    file: str = typer.Option(None, help="Path to text file"),
    url: str = typer.Option(None, help="URL to ingest"),
    rss: bool = typer.Option(False, help="Ingest from RSS feeds"),
):
    """Ingest financial documents into the knowledge base"""
    docs = []

    if file:
        path = Path(file)
        if not path.exists():
            console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(1)
        text = path.read_text(encoding="utf-8")
        docs.append(ingestion.ingest_text(text, source=str(path)))
        console.print(f"[green]Loaded file: {file}[/green]")

    if url:
        with console.status(f"[green]Fetching {url}..."):
            doc = ingestion.ingest_from_url(url)
        if doc:
            docs.append(doc)
            console.print(f"[green]Loaded URL: {url}[/green]")

    if rss:
        with console.status("[green]Fetching RSS feeds..."):
            docs.extend(ingestion.ingest_rss_feeds())
        console.print(f"[green]Loaded {len(docs)} RSS items[/green]")

    if not docs:
        console.print("[yellow]No documents to ingest. Use --file, --url, or --rss[/yellow]")
        return

    with console.status("[green]Indexing..."):
        rag.ingest_documents(docs)

    console.print(f"[bold green]✓ Ingested {len(docs)} document(s)[/bold green]")


@app.command()
def stats():
    """Show knowledge base statistics"""
    s = rag.get_collection_stats()
    table = Table(title="Knowledge Base Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("Document chunks", str(s["document_chunks"]))
    table.add_row("Embedding model", config.EMBEDDING_MODEL)
    table.add_row("LLM model", config.LLM_MODEL)
    console.print(table)


@app.command()
def chat():
    """Interactive chat mode"""
    console.print("[bold]Finance LLM Chat[/bold] — type 'exit' to quit\n")
    while True:
        question = console.input("[cyan]You: [/cyan]")
        if question.lower() in ("exit", "quit"):
            break
        with console.status("[bold green]Thinking..."):
            result = rag.query(question)
        console.print()
        console.print(Panel(Markdown(result["answer"]), title="Expert", border_style="green"))
        console.print()


if __name__ == "__main__":
    app()
