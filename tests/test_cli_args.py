import argparse

from transcribe_video import parse_args


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["transcribe_video.py"],
    )
    args = parse_args()
    assert args.compute_type == "int8"
    assert args.threads > 0
