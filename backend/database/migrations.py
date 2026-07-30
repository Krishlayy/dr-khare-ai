from sqlalchemy import inspect, text

from backend.database.database import engine


def _column_names(table: str) -> set[str]:
    inspector = inspect(engine)
    return {col["name"] for col in inspector.get_columns(table)}


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    if column not in _column_names(table):
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def migrate_documents_table() -> None:
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    columns = _column_names("documents")
    renames = {
        "file_path": "filepath",
        "file_type": "filetype",
        "chunk_count": "chunks_count",
    }

    with engine.begin() as conn:
        for old_name, new_name in renames.items():
            if old_name in columns and new_name not in columns:
                conn.execute(
                    text(f"ALTER TABLE documents RENAME COLUMN {old_name} TO {new_name}")
                )
                columns.remove(old_name)
                columns.add(new_name)

    _add_column_if_missing(
        "documents", "processing_stage", "processing_stage VARCHAR(64) DEFAULT 'uploading'"
    )
    _add_column_if_missing("documents", "error_message", "error_message TEXT")
    _add_column_if_missing(
        "documents", "filepath", "filepath VARCHAR(1024) DEFAULT ''"
    )
    _add_column_if_missing(
        "documents", "filetype", "filetype VARCHAR(32) DEFAULT 'unknown'"
    )
    _add_column_if_missing("documents", "chunks_count", "chunks_count INTEGER DEFAULT 0")
