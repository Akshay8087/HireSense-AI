"""File upload validation helpers."""
from __future__ import annotations

from werkzeug.datastructures import FileStorage

from app.core.exceptions import EmptyInputError, FileTooLargeError, InvalidFileError


def validate_upload(
    file: FileStorage | None,
    allowed_extensions: list[str],
    max_size_bytes: int,
) -> bytes:
    """Validate an uploaded file and return its raw bytes."""
    if file is None or file.filename == "":
        raise EmptyInputError("No file was uploaded.")

    filename = file.filename
    if "." not in filename:
        raise InvalidFileError(f"File '{filename}' has no extension.")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions:
        raise InvalidFileError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(allowed_extensions)}."
        )

    file.stream.seek(0, 2)  # seek to end
    size = file.stream.tell()
    file.stream.seek(0)

    if size == 0:
        raise EmptyInputError(f"File '{filename}' is empty.")
    if size > max_size_bytes:
        raise FileTooLargeError(
            f"File '{filename}' is {size / 1024 / 1024:.1f}MB, "
            f"exceeding the {max_size_bytes / 1024 / 1024:.0f}MB limit."
        )

    return file.read()


def validate_text_input(text: str | None, field_name: str = "text", min_length: int = 20) -> str:
    if text is None or not text.strip():
        raise EmptyInputError(f"'{field_name}' must not be empty.")
    if len(text.strip()) < min_length:
        raise EmptyInputError(
            f"'{field_name}' is too short ({len(text.strip())} chars). "
            f"Provide at least {min_length} characters."
        )
    return text.strip()
