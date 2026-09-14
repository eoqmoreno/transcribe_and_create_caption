import argparse
import itertools
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


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "ffmpeg não encontrado. Instale o Homebrew em https://brew.sh e execute "
            "'brew install ffmpeg'. Depois, abra um novo Terminal e tente novamente."
        )


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


def transcribe_audio(audio_path: Path, model_name: str, language: str, device: str):
    requested_device = device.lower().strip()

    try:
        model = WhisperModel(model_name, device=requested_device)
    except Exception as exc:
        if requested_device != "cpu":
            print(f"Falha ao usar o dispositivo '{requested_device}': {exc}")
            print("Tentando novamente com CPU...")
            model = WhisperModel(model_name, device="cpu")
        else:
            raise

    segments_result = []
    error_holder = []

    def run_transcription() -> None:
        try:
            segments, _ = model.transcribe(str(audio_path), language=language)
            segments_result.extend(list(segments))
        except Exception as exc:
            error_holder.append(exc)

    worker = threading.Thread(target=run_transcription, daemon=True)
    worker.start()

    spinner = itertools.cycle(["|", "/", "-", "\\"])
    while worker.is_alive():
        print(f"\rTranscrevendo... {next(spinner)}", end="", flush=True)
        time.sleep(0.1)

    print("\rTranscrição concluída      ")
    worker.join()

    if error_holder:
        raise error_holder[0]

    return segments_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcrever vídeo MP4 com faster-whisper e gerar arquivo TXT"
    )
    parser.add_argument("input", help="Arquivo de vídeo MP4 de entrada")
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
        "--no-timestamps",
        action="store_true",
        help="Gerar saída sem timestamps",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    video_path = Path(args.input)

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
        segments = transcribe_audio(audio_path, args.model, args.language, args.device)

        write_transcript(segments, output_path, include_timestamps=not args.no_timestamps)
        write_srt(segments, output_path)

    print(f"Transcrição concluída: {output_path}")
    print(f"Legenda SRT salva em: {output_path.with_suffix('.srt')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
