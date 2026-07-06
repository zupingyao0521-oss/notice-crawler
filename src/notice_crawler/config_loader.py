from pathlib import Path

import yaml


def load_config(config_path="config.yaml"):
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("配置文件是空的")

    required_keys = ["summary", "email", "output", "defaults", "sites"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"配置文件缺少必要字段：{key}")

    return config


def get_sites_from_config(config):
    defaults = config["defaults"]
    sites = []

    for site in config["sites"]:
        full_site = {
            "name": site["name"],
            "list_url": site["list_url"],
            "item_selector": site.get("item_selector", defaults["item_selector"]),
            "title_selector": site.get("title_selector", defaults["title_selector"]),
            "date_selector": site.get("date_selector", defaults["date_selector"]),
            "content_selector": site.get("content_selector", defaults["content_selector"]),
        }

        sites.append(full_site)

    return sites
