import argparse
import json
import os

import requests

BASE_URL = "http://data.bioontology.org"
DOWNLOAD_DIR = "bioportal"
ONTOLOGIES_JSON = "ontologies.json"


def main():
    parser = argparse.ArgumentParser(description="Download ontologies from BioPortal")
    parser.add_argument("--api-key", type=str, help="API key for BioPortal")
    parser.add_argument("--base-url", type=str, help="Base URL for BioPortal", default=BASE_URL)
    parser.add_argument("--download-dir", type=str, help="Directory to download ontologies", default=DOWNLOAD_DIR)
    parser.add_argument("--cache", type=str, help="JSON file to cache the ontology index", default=ONTOLOGIES_JSON)

    args = parser.parse_args()

    api_key = args.api_key
    base_url = args.base_url
    download_dir = args.download_dir
    cache = args.cache

    headers = {
        "Authorization": f"apikey token={api_key}"
    }

    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    # Download or load from disk
    if not os.path.exists(cache):
        response = requests.get(f"{base_url}/ontologies", headers=headers)
        ontologies = response.json()

        with open(cache, "w") as f:
            json.dump(ontologies, f)
    else:
        with open(cache, "r") as f:
            ontologies = json.load(f)

    for ontology in ontologies:
        acronym = ontology.get("acronym", None)
        download_url = ontology.get("links", {}).get("download", None)

        if acronym is None or download_url is None:
            print(f"Skipping {ontology}")
            continue

        # Download the ontology if not already downloaded
        filename = f"{acronym}.owl"
        filepath = os.path.join(download_dir, filename)

        if os.path.exists(filepath):
            print(f"Already downloaded {acronym}")
            continue

        response = requests.get(download_url, headers=headers)

        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"Downloaded {acronym}")
        else:
            print(f"Failed to download {acronym}")


if __name__ == "__main__":
    main()
