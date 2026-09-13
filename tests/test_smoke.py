from sentiment_analysis.cli import build_parser


def test_cli_parser_has_project_description() -> None:
    parser = build_parser()
    assert parser.description == "E-learning sentiment analysis"
