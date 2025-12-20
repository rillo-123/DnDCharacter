#!/usr/bin/env python3
"""Test the actual Open5e API response format."""
import requests
import json


def main() -> int:
    url = "https://api.open5e.com/spells/?limit=5&ordering=name"
    response = requests.get(url)
    data = response.json()

    print("=== Open5e API Response Structure ===\n")
    if data.get("results"):
        spell = data["results"][0]
        print(f"First spell: {spell.get('name')}")
        print(f"\nAll fields: {list(spell.keys())}")
        print(f"\n=== Full first spell data ===")
        print(json.dumps(spell, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
