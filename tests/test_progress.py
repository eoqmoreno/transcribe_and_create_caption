from transcribe_video import build_progress_bar, compute_progress_percent


def test_compute_progress_percent():
    assert compute_progress_percent(50, 100) == 50
    assert compute_progress_percent(150, 100) == 100
    assert compute_progress_percent(0, 0) == 0


def test_build_progress_bar():
    bar = build_progress_bar(50)
    assert bar.startswith("[")
    assert bar.endswith("]")
    assert "50%" in bar
