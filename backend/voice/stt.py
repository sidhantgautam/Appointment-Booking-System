from faster_whisper import WhisperModel

# Load lightweight whisper model
model = WhisperModel("base", compute_type="int8")


def transcribe_audio(file_path: str):

    segments, info = model.transcribe(file_path)

    text = ""
    for segment in segments:
        text += segment.text

    return text.strip()