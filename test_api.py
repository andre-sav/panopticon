#!/usr/bin/env python3
"""
API Test Script - Controlled experiments with Zoho CRM API
Run: python test_api.py
"""
import tomllib
import requests
from pathlib import Path


def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    secrets_path = Path(".streamlit/secrets.toml")
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def get_access_token(secrets):
    """Get a fresh access token using refresh token"""
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": secrets["zoho"]["client_id"],
        "client_secret": secrets["zoho"]["client_secret"],
        "refresh_token": secrets["zoho"]["refresh_token"],
    }
    response = requests.post(url, data=data, timeout=30)
    response.raise_for_status()
    return response.json()["access_token"]


def api_call(token, method, endpoint, params=None, json_body=None):
    """Make an API call and return full response details"""
    api_domain = "https://www.zohoapis.com"
    url = f"{api_domain}{endpoint}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    print(f"\n{'='*60}")
    print(f"REQUEST: {method} {url}")
    if params:
        print(f"PARAMS: {params}")
    if json_body:
        print(f"BODY: {json_body}")
    print("="*60)

    response = requests.request(
        method, url, headers=headers, params=params, json=json_body, timeout=30
    )

    print(f"\nSTATUS: {response.status_code}")
    print(f"HEADERS: {dict(response.headers)}")
    print(f"\nRESPONSE BODY:")
    try:
        import json
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text[:2000] if response.text else "(empty)")

    return response


def main():
    print("Loading secrets...")
    secrets = load_secrets()

    print("Getting access token...")
    token = get_access_token(secrets)
    print(f"Token obtained: {token[:20]}...")

    # EXPERIMENT 1: Try standard API (not COQL) which expands lookup fields
    print("\n\n>>> EXPERIMENT 1: Standard API with Locator_Name (expands lookups)")
    resp = api_call(token, "GET", "/crm/v2/Locatings",
                   params={"fields": "id,Name,Locator_Name", "per_page": 5})

    if resp.status_code == 200:
        data = resp.json()
        if data.get("data"):
            print("\n>>> Locator_Name from Standard API:")
            for rec in data["data"]:
                locator = rec.get("Locator_Name")
                print(f"  {rec.get('Name')}: Locator_Name = {locator}")

    # EXPERIMENT 2: List available modules
    print("\n\n>>> EXPERIMENT 2: List all modules (looking for Locators module)")
    resp = api_call(token, "GET", "/crm/v2/settings/modules")
    if resp.status_code == 200:
        data = resp.json()
        print("\n>>> Available modules:")
        for mod in data.get("modules", []):
            api_name = mod.get("api_name", "")
            # Show modules that might be locator-related
            if "locat" in api_name.lower() or mod.get("generated_type") == "custom":
                print(f"  - {api_name} (plural: {mod.get('plural_label')}, type: {mod.get('generated_type')})")

    # EXPERIMENT 3: Try fetching from "Locators" module if it exists
    print("\n\n>>> EXPERIMENT 3: Try fetching from Locators module")
    resp = api_call(token, "GET", "/crm/v2/Locators",
                   params={"per_page": 3})

    print("\n\nDone!")


if __name__ == "__main__":
    main()
