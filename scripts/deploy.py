import os
import ftplib
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"

FTP_HOST = os.environ.get("FTP_HOST", "")
FTP_USER = os.environ.get("FTP_USER", "")
FTP_PASS = os.environ.get("FTP_PASS", "")
FTP_ROOT = "/htdocs"


def upload_file(ftp, local_path, remote_path):
    try:
        ftp.cwd(str(Path(remote_path).parent))
    except ftplib.error_perm:
        parts = Path(remote_path).parts
        for i in range(1, len(parts) + 1):
            try:
                ftp.cwd(str(Path(*parts[:i])))
            except ftplib.error_perm:
                ftp.mkd(str(Path(*parts[:i])))
                ftp.cwd(str(Path(*parts[:i])))
        ftp.cwd(FTP_ROOT)

    remote_name = Path(remote_path).name
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_name}", f)
    print(f"  [↑] {remote_path}")


def list_remote_files(ftp, path="."):
    files = []
    try:
        items = ftp.nlst(path)
        for item in items:
            if item in (".", ".."):
                continue
            try:
                ftp.cwd(item)
                sub_files = list_remote_files(ftp, item)
                files.extend(sub_files)
                ftp.cwd("..")
            except ftplib.error_perm:
                files.append(item)
    except ftplib.error_perm:
        pass
    return files


def clean_remote(ftp, remote_path, keep_files):
    try:
        items = ftp.nlst(remote_path)
        for item in items:
            if item in (".", ".."):
                continue
            rel = str(Path(item).relative_to(FTP_ROOT)) if item.startswith(FTP_ROOT) else item
            if rel not in keep_files:
                try:
                    ftp.delete(item)
                    print(f"  [✗] Supprimé : {item}")
                except ftplib.error_perm:
                    try:
                        ftp.rmd(item)
                        print(f"  [✗] Dossier supprimé : {item}")
                    except ftplib.error_perm:
                        pass
    except ftplib.error_perm:
        pass


def main():
    print("=" * 60)
    print("  Déploiement FTP vers InfinityFree")
    print("=" * 60)

    if not all([FTP_HOST, FTP_USER, FTP_PASS]):
        print("[!] Erreur : Variables FTP manquantes (FTP_HOST, FTP_USER, FTP_PASS)")
        exit(1)

    print(f"[*] Connexion à {FTP_HOST}...")
    ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS, timeout=30)
    ftp.encoding = "utf-8"

    try:
        ftp.cwd(FTP_ROOT)
    except ftplib.error_perm:
        ftp.mkd(FTP_ROOT)
        ftp.cwd(FTP_ROOT)

    print(f"[*] Upload des fichiers depuis {SITE_DIR}/")

    keep_files = set()
    for local_path in SITE_DIR.rglob("*"):
        if local_path.is_file():
            rel_path = str(local_path.relative_to(SITE_DIR))
            remote_path = f"{FTP_ROOT}/{rel_path}"
            upload_file(ftp, local_path, remote_path)
            keep_files.add(rel_path)

    print("\n[*] Nettoyage des fichiers distants obsolètes...")
    clean_remote(ftp, FTP_ROOT, keep_files)

    ftp.quit()
    print(f"\n[✓] Déploiement terminé !")
    print(f"    Site : https://workshoppro.rf.gd")


if __name__ == "__main__":
    main()
