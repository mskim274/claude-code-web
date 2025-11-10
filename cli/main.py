"""Main CLI application entry point"""
import typer
from cli.commands import collect, backtest, ml, analyze

app = typer.Typer(
    name="kiwoom-auto",
    help="Kiwoom 자동매매 시스템 CLI - 데이터 수집, 백테스팅, 머신러닝, 분석",
    add_completion=False,
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(collect.app, name="collect", help="데이터 수집 (국내/해외)")
app.add_typer(backtest.app, name="backtest", help="백테스팅 실행 및 결과 조회")
app.add_typer(ml.app, name="ml", help="머신러닝 학습/예측/평가")
app.add_typer(analyze.app, name="analyze", help="종목/포트폴리오 분석")


@app.command()
def version():
    """Show CLI version"""
    from cli import __version__
    typer.echo(f"kiwoom-auto CLI version {__version__}")


if __name__ == "__main__":
    app()
