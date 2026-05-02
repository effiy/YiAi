import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, "/var/www/YiAi/src")

from services.state.state_service import StateStoreService

app = typer.Typer(help="State Store Query CLI")
console = Console()


def _get_service() -> StateStoreService:
    return StateStoreService()


@app.command()
def list(
    record_type: Optional[str] = typer.Option(None, "--record-type", "-t"),
    tags: Optional[list[str]] = typer.Option(None, "--tag"),
    title_contains: Optional[str] = typer.Option(None, "--title"),
    page_num: int = typer.Option(1, "--page", "-p"),
    page_size: int = typer.Option(20, "--page-size", "-s"),
    format: str = typer.Option("table", "--format", "-f"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """查询状态记录"""
    import asyncio

    async def _run():
        service = _get_service()
        result = await service.query(
            record_type=record_type,
            tags=tags,
            title_contains=title_contains,
            page_num=page_num,
            page_size=page_size,
        )

        if format == "json":
            text = json.dumps(result, indent=2, ensure_ascii=False)
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]Saved to {output}[/green]")
            else:
                console.print(text)
        elif format == "csv":
            import csv
            import io

            buffer = io.StringIO()
            writer = None
            for row in result.get("list", []):
                if writer is None:
                    writer = csv.DictWriter(buffer, fieldnames=row.keys())
                    writer.writeheader()
                writer.writerow(row)
            text = buffer.getvalue()
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]Saved to {output}[/green]")
            else:
                console.print(text)
        else:
            table = Table(title="State Records")
            if result.get("list"):
                first = result["list"][0]
                for col in first.keys():
                    table.add_column(col)
                for row in result["list"]:
                    table.add_row(*[str(v) for v in row.values()])
            console.print(table)
            console.print(f"Total: {result.get('total')}, Page: {result.get('pageNum')}/{result.get('totalPages')}")

    asyncio.run(_run())


@app.command()
def get(key: str):
    """根据 key 获取单条记录"""
    import asyncio

    async def _run():
        service = _get_service()
        record = await service.get(key)
        if record:
            console.print_json(json.dumps(record, ensure_ascii=False))
        else:
            console.print("[red]Record not found[/red]")
            raise typer.Exit(1)

    asyncio.run(_run())


@app.command()
def export(
    record_type: Optional[str] = typer.Option(None, "--record-type", "-t"),
    output: str = typer.Option(..., "--output", "-o"),
    format: str = typer.Option("json", "--format", "-f"),
):
    """导出查询结果到文件"""
    list(record_type=record_type, format=format, output=output, page_size=8000)


@app.command()
def stats(
    record_type: Optional[str] = typer.Option(None, "--record-type", "-t"),
):
    """查看状态记录统计"""
    import asyncio

    async def _run():
        service = _get_service()
        result = await service.query(
            record_type=record_type,
            page_num=1,
            page_size=1,
        )
        console.print(f"[bold]Total records:[/bold] {result.get('total', 0)}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
