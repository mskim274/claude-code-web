"""Data collection commands"""
from typing import Optional
import typer
from cli.ui.console import get_console

app = typer.Typer(
    name="collect",
    help="데이터 수집 명령어",
    no_args_is_help=True,
)


@app.command()
def domestic(
    start_date: Optional[str] = typer.Option(None, "--start-date", help="시작 날짜 (YYYYMMDD)"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="종료 날짜 (YYYYMMDD)"),
    symbols: Optional[str] = typer.Option(None, "--symbols", help="종목 코드 (쉼표로 구분)"),
):
    """국내 주식 데이터 수집"""
    console = get_console()
    console.print("[bold blue]국내 주식 데이터 수집을 시작합니다...[/bold blue]")

    # TODO: Implement actual data collection logic
    console.print(f"시작 날짜: {start_date or 'N/A'}")
    console.print(f"종료 날짜: {end_date or 'N/A'}")
    console.print(f"종목: {symbols or '전체'}")
    console.print("[green]✓ 수집 완료 (Mock)[/green]")


@app.command()
def overseas(
    start_date: Optional[str] = typer.Option(None, "--start-date", help="시작 날짜 (YYYYMMDD)"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="종료 날짜 (YYYYMMDD)"),
    symbols: Optional[str] = typer.Option(None, "--symbols", help="종목 코드 (쉼표로 구분)"),
):
    """해외 주식 데이터 수집"""
    console = get_console()
    console.print("[bold blue]해외 주식 데이터 수집을 시작합니다...[/bold blue]")

    # TODO: Implement actual data collection logic
    console.print(f"시작 날짜: {start_date or 'N/A'}")
    console.print(f"종료 날짜: {end_date or 'N/A'}")
    console.print(f"종목: {symbols or '전체'}")
    console.print("[green]✓ 수집 완료 (Mock)[/green]")
