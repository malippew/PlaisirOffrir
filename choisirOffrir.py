import requests
import json
import re
from bs4 import BeautifulSoup

BASE_URL = "https://choisiroffrir.com"

PRESENT_LISTS: dict[str, str] = {
    "Philippe": "https://choisiroffrir.com/82254",
    "Marion": "https://choisiroffrir.com/70277",
    "Kevin": "https://choisiroffrir.com/70861",
    "Laure-Elodie": "https://choisiroffrir.com/61056",
    "Teyrence": "https://choisiroffrir.com/75829",
    "Mathéo": "https://choisiroffrir.com/61275",
    "David": "https://choisiroffrir.com/71513",
    "Fanny": "https://choisiroffrir.com/71087",
    "Alizéa": "https://choisiroffrir.com/81068",
    "Emma": "https://choisiroffrir.com/71511",
    "Dominique": "https://choisiroffrir.com/101938",
    "Marie-Danièle": "https://choisiroffrir.com/71089",
}


def scrapePresentList(listOwner: str, listUrl: str) -> dict:
    """
    Scrape the present list from the given URL.
    Args:
        listOwner (str): The owner of the present list.
        listUrl (str): The URL of the present list to scrape.
    Returns: A dictionary containing the details of the present list.
    """
    response = requests.get(
        listUrl,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status_code != 200:
        print(
            f"Erreur lors de la récupération de la liste '{listUrl}' : {response.status_code}"
        )
        return {}

    soup = BeautifulSoup(response.content, "html.parser")

    listDetails: dict = {
        "owner": listOwner,
        "url": listUrl,
    }

    coverImageUrl = soup.find("div", class_="cover-container").find("img")["src"]
    listDetails["coverImageUrl"] = coverImageUrl.strip() if coverImageUrl else ""

    descriptionContainer = soup.find("div", class_="description")

    nameList = descriptionContainer.find("h3")
    listDetails["title"] = nameList.text.strip() if nameList else ""

    welcomeMessage = descriptionContainer.find("div", class_="row")
    listDetails["welcomeMessage"] = (
        welcomeMessage.text.strip() if welcomeMessage else ""
    )

    presentsContainer = soup.find("div", class_="container mb-4")

    presents = presentsContainer.find_all("div", class_="card-cadeau")

    listDetails["presents"] = []
    for present in presents:
        if "not-active" in present.find("a", class_="btn-offrir")["class"]:
            pass
        else:
            cardImageContainer = present.find("div", class_="card-image")

            priceTag = cardImageContainer.find("span", class_="prix")
            price_str = priceTag.text.strip() if priceTag else ""
            try:
                price_cleaned = float(
                    re.sub(r"[^\d,\.]", "", price_str).replace(",", ".")
                )

            except ValueError:
                price_cleaned = price_str if price_str else "Pas de prix"

            presentDetails = {
                "detailsLink": BASE_URL + cardImageContainer.find("a")["href"],
                "image": cardImageContainer.find("img")["src"],
                "price": price_cleaned,
            }
            listDetails["presents"].append(presentDetails)

    return listDetails


def convertToJson(presentList: dict) -> str:
    """
    Convert the present list dictionary to a JSON string.
    Args:
        presentList (dict): The present list dictionary to convert.
    Returns: A JSON string representation of the present list.
    """
    with open("listesChoisirOffrir.json", "w", encoding="utf-8") as jsonFile:
        json.dump(presentList, jsonFile, indent=4, ensure_ascii=False)


def main():
    presentList: dict = {"numberOfLists": len(PRESENT_LISTS), "lists": []}
    for listOwner, listUrl in PRESENT_LISTS.items():
        presentList["lists"].append(scrapePresentList(listOwner, listUrl))

    convertToJson(presentList)


if __name__ == "__main__":
    main()
