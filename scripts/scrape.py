import os
import json
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
ASSETS_DIR = SITE_DIR / "assets"

AFFILIATE_URL = os.environ.get(
    "AFFILIATE_URL",
    "https://affpa.top/L?tag=d_3902989m_2387c_&site=3902989&ad=2387",
)

SEO_TAGS = {
    "title": "1xBet Partenaires - Programme d'affiliation | Inscription",
    "description": "Rejoignez le programme d'affiliation 1xBet Partners. Gagnez des commissions sur le sport avec 1xbet. Inscription gratuite et rapide.",
    "keywords": "1xBet, affiliation, partenaires, sport, bookmaker, commissions",
    "og_title": "1xBet Partenaires - Programme d'affiliation",
    "og_description": "Rejoignez le programme d'affiliation 1xBet Partners et gagnez des commissions.",
    "og_url": "https://workshoppro.rf.gd",
}


def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def render_page(driver, url):
    print(f"[*] Navigation vers : {url}")
    driver.get(url)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(("tag name", "body"))
    )

    for i in range(30):
        ready = driver.execute_script(
            "return document.readyState === 'complete'"
        )
        if ready:
            break
        import time
        time.sleep(1)

    import time
    time.sleep(5)

    html = driver.page_source
    current_url = driver.current_url
    print(f"[✓] Page rendue. URL finale : {current_url}")
    return html, current_url


def download_asset(url, folder):
    if not url or url.startswith("data:"):
        return url

    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/")

    if not path:
        return url

    local_path = folder / path
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if local_path.exists():
        return f"assets/{path}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            local_path.write_bytes(resp.content)
            print(f"  [↓] {path}")
            return f"assets/{path}"
        else:
            print(f"  [!] Échec {url} -> status {resp.status_code}")
            return url
    except Exception as e:
        print(f"  [!] Erreur {url} -> {e}")
        return url


def download_assets(soup, base_url, assets_dir):
    tags_attrs = {
        "img": "src",
        "link": "href",
        "script": "src",
        "source": "src",
    }

    for tag, attr in tags_attrs.items():
        for el in soup.find_all(tag):
            val = el.get(attr)
            if val and not val.startswith("data:"):
                full_url = urllib.parse.urljoin(base_url, val)
                local_path = download_asset(full_url, assets_dir)
                if local_path != full_url:
                    el[attr] = local_path


def inject_seo(soup):
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = SEO_TAGS["title"]

    meta_map = {
        "description": SEO_TAGS["description"],
        "keywords": SEO_TAGS["keywords"],
        "robots": "index, follow",
    }
    for name, content in meta_map.items():
        tag = soup.find("meta", attrs={"name": name})
        if tag:
            tag["content"] = content
        else:
            new_tag = soup.new_tag("meta")
            new_tag["name"] = name
            new_tag["content"] = content
            soup.head.append(new_tag)

    og_map = {
        "og:title": SEO_TAGS["og_title"],
        "og:description": SEO_TAGS["og_description"],
        "og:type": "website",
        "og:url": SEO_TAGS["og_url"],
    }
    for prop, content in og_map.items():
        tag = soup.find("meta", attrs={"property": prop})
        if tag:
            tag["content"] = content
        else:
            new_tag = soup.new_tag("meta")
            new_tag["property"] = prop
            new_tag["content"] = content
            soup.head.append(new_tag)

    canonical = soup.find("link", rel="canonical")
    if canonical:
        canonical["href"] = SEO_TAGS["og_url"]


def inject_affiliate_links(soup, affiliate_url):
    link_texts = [
        "register", "sign up", "signup", "sign-up",
        "s'inscrire", "inscription", "créer un compte",
        "get started", "commencer", "join", "rejoindre",
        "inscrivez-vous", "create account",
    ]

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").lower()
        text = a_tag.get_text(strip=True).lower()

        if any(t in href or t in text for t in link_texts):
            old_href = a_tag["href"]
            a_tag["href"] = affiliate_url
            a_tag["target"] = "_blank"
            a_tag["rel"] = "noopener noreferrer"
            print(f"  [→] Lien affilié injecté dans <a> : {old_href[:50]}...")

    for btn_tag in soup.find_all(["button", "input"]):
        btn_type = btn_tag.get("type", "").lower()
        btn_value = btn_tag.get("value", "").lower()
        btn_text = btn_tag.get_text(strip=True).lower()

        if any(
            t in btn_value or t in btn_text for t in link_texts
        ):
            if btn_tag.name == "input" and btn_type in ("submit", "button"):
                parent = btn_tag.find_parent("form")
                if parent:
                    parent["action"] = affiliate_url
                    parent["method"] = "GET"
                    print(f"  [→] Lien affilié injecté dans <form>")
            elif btn_tag.name == "button":
                wrapper = soup.new_tag("a")
                wrapper["href"] = affiliate_url
                wrapper["target"] = "_blank"
                wrapper["rel"] = "noopener noreferrer"
                wrapper["class_"] = btn_tag.get("class", [])
                btn_tag.wrap(wrapper)
                print(f"  [→] Bouton wrappé avec lien affilié")


def add_base_tag(soup, base_url):
    existing = soup.find("base")
    if not existing:
        base = soup.new_tag("base")
        base["href"] = base_url
        if soup.head:
            soup.head.insert(0, base)


def cleanup_scripts(soup):
    blocked_domains = [
        "hotjar", "google-analytics", "googletagmanager",
        "facebook.net", "googleadservices", "doubleclick",
        "gtag", "analytics", "tracking",
    ]
    for script in soup.find_all("script"):
        src = script.get("src", "")
        text = script.get_text() or ""
        if any(d in src.lower() for d in blocked_domains):
            script.decompose()
            continue
        if any(d in text.lower() for d in blocked_domains):
            script.decompose()
            continue
        if src and not src.startswith("data:") and not src.startswith("//"):
            parsed = urllib.parse.urlparse(src)
            if parsed.path and not parsed.hostname:
                original_path = src.lstrip("/")
                if not Path(SITE_DIR / "assets" / original_path).exists():
                    if (ASSETS_DIR / original_path).exists():
                        script["src"] = f"assets/{original_path}"
                    else:
                        print(f"  [x] Script introuvable, retiré : {src[:60]}")
                        script.decompose()

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if any(d in src.lower() for d in blocked_domains):
            iframe.decompose()

    for link in soup.find_all("link"):
        href = link.get("href", "")
        if any(d in href.lower() for d in blocked_domains):
            link.decompose()

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if any(d in src.lower() for d in blocked_domains):
            img.decompose()

    print("  [✓] Scripts et traqueurs nettoyés")


def save_html(soup, output_path):
    html_bytes = soup.encode("utf-8")
    output_path.write_bytes(html_bytes)
    print(f"[✓] HTML sauvegardé : {output_path}")


def main():
    print("=" * 60)
    print("  Scraper Site Affilié 1xPartners")
    print("=" * 60)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    driver = setup_driver()
    try:
        html, final_url = render_page(driver, AFFILIATE_URL)

        base_url = f"{urllib.parse.urlparse(final_url).scheme}://{urllib.parse.urlparse(final_url).netloc}"

        soup = BeautifulSoup(html, "lxml")

        print("[*] Téléchargement des assets...")
        download_assets(soup, base_url, ASSETS_DIR)

        print("[*] Nettoyage des scripts externes problématiques...")
        cleanup_scripts(soup)

        print("[*] Injection des balises SEO...")
        inject_seo(soup)

        print("[*] Injection du lien affilié...")
        inject_affiliate_links(soup, AFFILIATE_URL)

        add_base_tag(soup, base_url)

        index_path = SITE_DIR / "index.html"
        save_html(soup, index_path)

        print(f"\n[✓] Terminé ! Fichiers dans : {SITE_DIR}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
