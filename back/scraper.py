import time
import os
import re
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Union, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import requests_cache
from bs4 import BeautifulSoup
from jsonschema import validate, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Constants
BASE_URL = "https://choisiroffrir.com"
CACHE_NAME = "choisir_offrir_cache"
CACHE_EXPIRE = 3600  # seconds
OUTPUT_FILE = "data/listes_choisir_offrir.json"
MAX_WORKERS = 5

# Present lists mapping
PRESENT_LISTS: Dict[str, int] = {
    "Philippe": 82254,
    "Marion": 70277,
    "Kevin": 70861,
    "Laure-Elodie": 61056,
    "Teyrence": 75829,
    "Mathéo": 61275,
    "David": 71513,
    "Fanny": 71087,
    "Alizéa": 81068,
    "Emma": 71511,
    "Dominique": 101938,
    "Marie-Danièle": 71089,
}

# JSON schema for output validation
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "number_of_lists": {"type": "integer"},
        "lists": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "cover_image_url": {"type": "string", "format": "uri"},
                    "title": {"type": "string"},
                    "welcome_message": {"type": "string"},
                    "presents": {"type": "array"},
                },
                "required": ["owner", "url", "presents"],
            },
        },
    },
    "required": ["number_of_lists", "lists"],
}

# Initialize cached session
session = requests_cache.CachedSession(
    cache_name=CACHE_NAME,
    backend="sqlite",
    expire_after=CACHE_EXPIRE,
    allowable_codes=(200, 404),
    stale_if_error=True,
)


@dataclass
class Present:
    title: str
    description: str
    link_suggestion: str
    details_link: str
    image_url: str
    price: Union[float, str]
    preference: int


@dataclass
class PresentList:
    owner: str
    url: str
    cover_image_url: str
    title: str
    welcome_message: str
    presents: List[Present]

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["presents"] = [asdict(p) for p in self.presents]
        return data


def get_soup(url: str, timeout: int = 10) -> BeautifulSoup:
    """
    Fetch content and return BeautifulSoup parser.
    Retries once if cache deserialization fails.
    Raises HTTPError on bad status.
    """
    try:
        logger.debug("Fetching URL: %s", url)
        response = session.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except (requests.RequestException, Exception) as err:
        # Handle cache deserialization or SQLite errors by clearing cache entry and retrying once
        try:
            logger.warning(
                "Error fetching from cache or network, clearing cache for URL and retrying: %s",
                url,
            )
            # Suppression manuelle de l’entrée du cache
            try:
                cache_key = session.cache.create_key(url)
                if isinstance(session.cache.responses, dict):
                    session.cache.responses.pop(cache_key, None)
                if isinstance(session.cache.redirects, dict):
                    session.cache.redirects.pop(cache_key, None)

                logger.info("Cache manually cleared for URL: %s", url)
            except Exception as e:
                logger.warning("Failed to clear cache for URL %s: %s", url, e)

            # Nouvelle tentative après nettoyage
            response = session.get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
            )
            response.raise_for_status()
        except Exception as err2:
            logger.error("Failed to fetch URL %s after clearing cache: %s", url, err2)
            raise
    content = response.content or b""
    if not isinstance(content, (bytes, bytearray)):
        content = str(content).encode("utf-8", errors="ignore")
    return BeautifulSoup(content, "html.parser")


def parse_price(price_str: str) -> Union[float, str]:
    """
    Convert price string to float or return original on failure.
    """
    cleaned = re.sub(r"[^\d,\.]", "", price_str).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("Could not parse price '%s'", price_str)
        return price_str or "Pas de prix"


def scrape_present_list(owner: str, list_id: int) -> Dict:
    """
    Scrape presents for given owner and list ID.
    """
    url = f"{BASE_URL}/{list_id}"
    soup = get_soup(url)

    cover_img = soup.select_one(".cover-container img")
    cover_image_url = cover_img["src"].strip() if cover_img else ""

    desc = soup.select_one(".description")
    title_tag = desc.find("h3") if desc else None
    welcome_tag = desc.select_one(".row") if desc else None

    cards = soup.select(".container.mb-4 .card-cadeau")
    presents: List[Present] = []

    for card in cards:
        offer_btn = card.select_one("a.btn-offrir")
        if not offer_btn or "not-active" in offer_btn.get("class", []):
            continue

        img_container = card.select_one(".card-image")
        body = card.select_one(".card-body")
        if not img_container or not body:
            continue

        price_tag = img_container.select_one(".prix")
        price_val = (
            parse_price(price_tag.get_text(strip=True)) if price_tag else "Pas de prix"
        )

        title_text = body.select_one("h5.card-title").get_text(strip=True)
        desc_text = body.select_one("p.description").get_text(strip=True)
        link_tag = body.select_one("a.second-text")
        suggestion = (
            link_tag.get_text(strip=True) if link_tag else "Pas de lien de suggestion"
        )

        detail_href = img_container.find("a")["href"]
        img_src = img_container.find("img")["src"]
        pref_tag = img_container.select_one(".preference")
        pref = int(pref_tag.get_text(strip=True)) if pref_tag else 0

        presents.append(
            Present(
                title=title_text,
                description=desc_text,
                link_suggestion=suggestion,
                details_link=f"{BASE_URL}{detail_href}",
                image_url=img_src,
                price=price_val,
                preference=pref,
            )
        )

    present_list = PresentList(
        owner=owner,
        url=url,
        cover_image_url=cover_image_url,
        title=title_tag.get_text(strip=True) if title_tag else "",
        welcome_message=welcome_tag.get_text(strip=True) if welcome_tag else "",
        presents=presents,
    )
    return present_list.to_dict()


def save_to_json(data: Dict, filename: str) -> None:
    """
    Validate against schema and write to JSON.
    """
    try:
        validate(instance=data, schema=OUTPUT_SCHEMA)

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("Data successfully written to %s", filename)
    except ValidationError as ve:
        logger.error("JSON validation error: %s", ve)
        raise
    except IOError as err:
        logger.error("Failed to write JSON to %s: %s", filename, err)
        raise


def main() -> None:
    """Scrape all lists in parallel and save results."""
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_owner = {
            executor.submit(scrape_present_list, owner, lid): owner
            for owner, lid in PRESENT_LISTS.items()
        }
        for future in as_completed(future_to_owner):
            owner = future_to_owner[future]
            try:
                data = future.result()
                results.append(data)
            except Exception:
                logger.exception("Error processing list for %s", owner)

    output = {"number_of_lists": len(results), "lists": results}
    save_to_json(output, OUTPUT_FILE)

    session.close()


if __name__ == "__main__":
    main()
