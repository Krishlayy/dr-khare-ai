import re
from pathlib import Path

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    if suffix == ".pdf":
        import fitz

        doc = fitz.open(file_path)
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)

    if suffix == ".docx":
        from docx import Document as DocxDocument

        document = DocxDocument(file_path)
        return "\n".join(
            paragraph.text for paragraph in document.paragraphs if paragraph.text
        )

    raise ValueError(f"Unsupported file type: {suffix}")


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Normalize spaces but keep newlines
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    separators = ["\n\n", "\n", ". ", " ", ""]

    def split_recursively(text_to_split: str, seps: list[str]) -> list[str]:
        if len(text_to_split) <= chunk_size:
            return [text_to_split]

        for i, sep in enumerate(seps):
            if sep == "":
                splits = list(text_to_split)
                break
            if sep in text_to_split:
                splits = text_to_split.split(sep)
                break
        else:
            splits = list(text_to_split)
            sep = ""

        final_chunks = []
        current_chunk = []
        current_len = 0

        for s in splits:
            s_len = len(s) + (len(sep) if current_chunk else 0)
            if current_len + s_len > chunk_size and current_chunk:
                final_chunks.append(sep.join(current_chunk))
                
                # Backtrack to satisfy overlap
                overlap_chunk = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) + len(sep) > overlap:
                        break
                    overlap_chunk.insert(0, item)
                    overlap_len += len(item) + len(sep)
                
                current_chunk = overlap_chunk
                current_len = overlap_len
            
            current_chunk.append(s)
            current_len += len(s) + (len(sep) if len(current_chunk) > 1 else 0)

        if current_chunk:
            final_chunks.append(sep.join(current_chunk))

        result = []
        next_seps = seps[i+1:] if i + 1 < len(seps) else [""]
        for chunk in final_chunks:
            if len(chunk) > chunk_size and next_seps != [""]:
                result.extend(split_recursively(chunk, next_seps))
            else:
                if chunk.strip():
                    result.append(chunk.strip())

        return result

    return split_recursively(cleaned, separators)
