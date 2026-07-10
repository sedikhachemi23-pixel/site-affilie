import os
import ftplib
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"

FTP_HOST = os.environ.get("FTP_HOST", "")
FTP_USER = os.environ.get("FTP_USER", "")
FTP_PASS = os.environ.get("FTP_PASS", "")
FTP_ROOT = "/htdocs"


def ensure_ftp_dir(ftp, remote_dir):
    parts = remote_dir.strip("/").split("/")
    current = "/"
    for part in parts:
        if not part:
            continue
        current = f"{current}{part}/"
        try:
            ftp.cwd(current)
        except ftplib.error_perm:
            ftp.mkd(current)
            ftp.cwd(current)


def upload_file(ftp, local_path, rel_path):
    remote_dir = f"{FTP_ROOT}/{os.path.dirname(rel_path)}" if os.path.dirname(rel_path) else FTP_ROOT
    ensure_ftp_dir(ftp, remote_dir)
    ftp.cwd(remote_dir)
    remote_name = os.path.basename(rel_path)
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_name}", f)
    print(f"  [↑] {remote_dir}/{remote_name}")


def main():
    print("=" * 60)
    print("  Déploiement FTP vers InfinityFree")
    print("=" * 60)

    if not all([FTP_HOST, FTP_USER, FTP_PASS]):
        print("[!] Erreur : Variables FTP manquantes")
        exit(1)

    print(f"[*] Connexion à {FTP_HOST}...")
    ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS, timeout=60)
    ftp.encoding = "utf-8"

    ensure_ftp_dir(ftp, FTP_ROOT)

    print(f"[*] Upload des fichiers depuis {SITE_DIR}/")

    for local_path in sorted(SITE_DIR.rglob("*")):
        if local_path.is_file():
            rel_path = str(local_path.relative_to(SITE_DIR)).replace("\\", "/")
            upload_file(ftp, local_path, rel_path)

    ftp.quit()
    print(f"\n[✓] Déploiement terminé !")
    print(f"    Site : https://workshoppro.rf.gd")


if __name__ == "__main__":
    main()
