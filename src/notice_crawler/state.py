import json
from pathlib import Path


def load_processed_links(file_path="processed_links.json"):
    path = Path(file_path)

    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as f:
        links = json.load(f)

    return set(links)


def save_processed_links(links, file_path="processed_links.json"):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            sorted(set(links)),
            f,
            ensure_ascii=False,
            indent=2,
        )


def save_processed_link(link, file_path="processed_links.json"):
    processed_links = load_processed_links(file_path)
    processed_links.add(link)
    save_processed_links(processed_links, file_path)
