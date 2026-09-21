import argparse
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from faster_whisper import WhisperModel

# Padrões da solução para uso simples: sempre transcreve em português e, se o ambiente
# não tiver suporte a GPU, usa CPU automaticamente.
DEFAULT_LANGUAGE = "pt"
DEFAULT_DEVICE = "cpu"
DEFAULT_INPUT_DIR = Path("template")
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "ffmpeg não encontrado. Instale-o seguindo as instruções do README e "
            "depois abra um novo terminal e tente novamente."
        )


def find_video_in_template() -> Path:
    if not DEFAULT_INPUT_DIR.exists():
        raise FileNotFoundError(
            f"A pasta '{DEFAULT_INPUT_DIR}' não existe. Crie-a e coloque um vídeo dentro."
        )

    videos = sorted(
        path
        for path in DEFAULT_INPUT_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not videos:
        extensions = ", ".join(sorted(VIDEO_EXTENSIONS))
        raise FileNotFoundError(
            f"Nenhum vídeo encontrado em '{DEFAULT_INPUT_DIR}'. "
            f"Extensões aceitas: {extensions}."
        )

    if len(videos) > 1:
        names = ", ".join(video.name for video in videos)
        raise ValueError(
            f"Mais de um vídeo encontrado em '{DEFAULT_INPUT_DIR}': {names}. "
            "Deixe somente um vídeo na pasta ou informe o arquivo explicitamente."
        )

    return videos[0]


def extract_audio(video_path: Path, audio_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path),
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_srt_timestamp(seconds: float) -> str:
    total_milliseconds = int(seconds * 1000)
    hours, remainder = divmod(total_milliseconds, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def compute_progress_percent(current: float, total: float) -> int:
    if total <= 0:
        return 0
    percent = int((current / total) * 100)
    return max(0, min(100, percent))


def build_progress_bar(percent: int, width: int = 20) -> str:
    filled = max(0, min(width, int((percent / 100) * width)))
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent}%"


def get_audio_duration(audio_path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def write_transcript(segments, output_path: Path, include_timestamps: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue

            if include_timestamps:
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                output_file.write(f"[{start} --> {end}] {text}\n")
            else:
                output_file.write(f"{text}\n")


def write_srt(segments, output_path: Path) -> None:
    srt_path = output_path.with_suffix(".srt")
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    with srt_path.open("w", encoding="utf-8") as output_file:
        for index, segment in enumerate(segments, start=1):
            text = segment.text.strip()
            if not text:
                continue

            start = format_srt_timestamp(segment.start)
            end = format_srt_timestamp(segment.end)
            output_file.write(f"{index}\n{start} --> {end}\n{text}\n\n")


def transcribe_audio(audio_path: Path, model_name: str, language: str, device: str, compute_type: str = "int8", cpu_threads: int = 4):
    requested_device = device.lower().strip()

    try:
        model = WhisperModel(
            model_name,
            device=requested_device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
        )
    except Exception as exc:
        if requested_device != "cpu":
            print(f"Falha ao usar o dispositivo '{requested_device}': {exc}")
            print("Tentando novamente com CPU...")
            model = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=cpu_threads,
            )
        else:
            raise

    total_duration = get_audio_duration(audio_path)
    segments_result = []
    error_holder = []

    def run_transcription() -> None:
        try:
            segments, _ = model.transcribe(str(audio_path), language=language)
            last_percent = 0
            for segment in segments:
                segments_result.append(segment)
                if total_duration > 0:
                    percent = compute_progress_percent(segment.end, total_duration)
                    if percent != last_percent:
                        print(
                            f"\r{build_progress_bar(percent)} - Transcrevendo...",
                            end="",
                            flush=True,
                        )
                        last_percent = percent
            if total_duration > 0:
                print(f"\r{build_progress_bar(100)} - Transcrevendo...", end="", flush=True)
        except Exception as exc:
            error_holder.append(exc)

    worker = threading.Thread(target=run_transcription, daemon=True)
    worker.start()

    spinner = itertools.cycle(["|", "/", "-", "\\"])
    while worker.is_alive():
        if total_duration <= 0:
            print(f"\rTranscrevendo... {next(spinner)}", end="", flush=True)
        time.sleep(0.1)

    print("\rTranscrição concluída                ")
    worker.join()

    if error_holder:
        raise error_holder[0]

    return segments_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcrever vídeo MP4 com faster-whisper e gerar arquivo TXT"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Arquivo de vídeo de entrada. Se omitido, usa o único vídeo em template/",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Arquivo de texto de saída. Se não for informado, usa o mesmo nome do vídeo com extensão .txt",
    )
    parser.add_argument(
        "--model",
        default="medium",
        help="Modelo faster-whisper (tiny, base, small, medium, large-v3)",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Idioma da transcrição (padrão: pt)",
    )
    parser.add_argument(
        "--device",
        default=DEFAULT_DEVICE,
        help="Dispositivo para inferência (padrão: cpu)",
    )
    parser.add_argument(
        "--compute-type",
        choices=["int8", "float16", "float32"],
        default="int8",
        help="Tipo de computação do modelo para ganhar velocidade em CPU (padrão: int8)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=max(1, min(os.cpu_count() or 4, 8)),
        help="Número de threads da CPU para inferência (padrão: até 8 núcleos ou o máximo da máquina)",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Gerar saída sem timestamps",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        video_path = Path(args.input) if args.input else find_video_in_template()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = video_path.with_suffix(".txt")

    if not video_path.exists():
        print(f"Arquivo não encontrado: {video_path}", file=sys.stderr)
        return 1

    try:
        check_ffmpeg()
    except EnvironmentError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.wav"
        print(f"Extraindo áudio do vídeo para: {audio_path}")
        extract_audio(video_path, audio_path)

        print("Iniciando transcrição...")
        segments = transcribe_audio(
            audio_path,
            args.model,
            args.language,
            args.device,
            compute_type=args.compute_type,
            cpu_threads=args.threads,
        )

        write_transcript(segments, output_path, include_timestamps=not args.no_timestamps)
        write_srt(segments, output_path)

    print(f"Transcrição concluída: {output_path}")
    print(f"Legenda SRT salva em: {output_path.with_suffix('.srt')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
