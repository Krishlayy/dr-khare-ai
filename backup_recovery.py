import os
import shutil
from datetime import datetime
import subprocess

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"Creating backup in {backup_dir}...")
    
    # 1. Backup Postgres
    # Assuming docker container is named 'dr_khare_postgres'
    print("Backing up PostgreSQL database...")
    try:
        with open(os.path.join(backup_dir, "db_dump.sql"), "w") as f:
            subprocess.run(
                ["docker", "exec", "dr_khare_postgres", "pg_dump", "-U", "drkhare", "drkhare_staging"],
                stdout=f,
                check=True
            )
        print("Database backup successful.")
    except Exception as e:
        print(f"Database backup failed: {e}")

    # 2. Backup ChromaDB
    print("Backing up ChromaDB...")
    try:
        shutil.make_archive(os.path.join(backup_dir, "chroma_db"), 'zip', "backend/chroma_db")
        print("ChromaDB backup successful.")
    except Exception as e:
        print(f"ChromaDB backup failed: {e}")

    # 3. Backup Uploads (if local fallback is used, otherwise MinIO data is persistent in docker volume)
    if os.path.exists("storage/uploads"):
        print("Backing up local uploads...")
        try:
            shutil.make_archive(os.path.join(backup_dir, "uploads"), 'zip', "storage/uploads")
            print("Uploads backup successful.")
        except Exception as e:
            print(f"Uploads backup failed: {e}")

    print(f"Backup completed: {backup_dir}")

if __name__ == "__main__":
    create_backup()
