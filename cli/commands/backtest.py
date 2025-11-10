"""Backtesting commands"""
from typing import Optional
import typer
from cli.ui.console import get_console

app = typer.Typer(
    name="backtest",
    help="백테스팅 명령어",
    no_args_is_help=True,
)


@app.command()
def run(
    strategy: str = typer.Argument(..., help="전략 이름"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="시작 날짜 (YYYYMMDD)"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="종료 날짜 (YYYYMMDD)"),
    initial_capital: float = typer.Option(10000000.0, "--initial-capital", help="초기 자본금"),
):
    """백테스팅 실행"""
    console = get_console()
    console.print(f"[bold blue]백테스팅 실행: {strategy}[/bold blue]")

    # TODO: Implement actual backtesting logic
    console.print(f"시작 날짜: {start_date or 'N/A'}")
    console.print(f"종료 날짜: {end_date or 'N/A'}")
    console.print(f"초기 자본: {initial_capital:,.0f}원")
    console.print("[green]✓ 백테스팅 완료 (Mock)[/green]")


@app.command()
def results(
    backtest_id: Optional[int] = typer.Option(None, "--backtest-id", help="백테스트 ID"),
    limit: int = typer.Option(10, "--limit", help="결과 개수"),
):
    """백테스팅 결과 조회"""
    console = get_console()
    console.print("[bold blue]백테스팅 결과 조회[/bold blue]")

    # TODO: Implement actual results retrieval logic
    if backtest_id:
        console.print(f"백테스트 ID: {backtest_id}")
    else:
        console.print(f"최근 {limit}개 결과")
    console.print("[green]✓ 조회 완료 (Mock)[/green]")
