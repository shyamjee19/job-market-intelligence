"""Local-disk resume storage. Files land under settings.RESUME_UPLOAD_DIR
in a per-user folder, named by a random UUID (never the user-supplied
filename) to rule out path traversal and collisions - the original
filename is kept separately in the database for display purposes only.
"""
import os
import uuid

from utils.exceptions import DataValidationError

_ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

# Magic bytes for each allowed type - checked in addition to the
# extension, since a client can rename any file to end in .pdf. Not a
# full content sandbox, but it rules out the trivial "malicious.exe
# renamed to resume.pdf" case rather than trusting the extension alone.
_MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF-",),
    ".docx": (b"PK\x03\x04",),  # docx is a zip archive
    ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),  # legacy OLE compound format
}


def _validate(filename: str, contents: bytes, max_size_mb: int) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise DataValidationError(f"Unsupported file type '{ext}' - allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}")

    if len(contents) > max_size_mb * 1024 * 1024:
        raise DataValidationError(f"File too large - max {max_size_mb}MB")

    if not any(contents.startswith(sig) for sig in _MAGIC_BYTES[ext]):
        raise DataValidationError("File content doesn't match its extension - upload a real PDF/DOC/DOCX")

    return ext


def save_resume(upload_dir: str, user_id: int, filename: str, contents: bytes, max_size_mb: int) -> str:
    """Validates and writes the file, returning the path it was stored at."""
    ext = _validate(filename, contents, max_size_mb)

    user_dir = os.path.join(upload_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    stored_path = os.path.join(user_dir, f"{uuid.uuid4()}{ext}")
    with open(stored_path, "wb") as file:
        file.write(contents)

    return stored_path
