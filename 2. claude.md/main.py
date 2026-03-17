"""CLI entry point — run with: uv run python main.py <city>"""

import logging
import sys

from weather import fetch_weather, format_weather

# Configure logging at the entry point, not inside library modules (Design Best Practice)
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python main.py <city>")
        sys.exit(1)

    city = " ".join(sys.argv[1:])
    result = fetch_weather(city)

    if result is None:
        print("Could not fetch weather. Check your API key and city name.")
        sys.exit(1)

    print(format_weather(result))


if __name__ == "__main__":
    main()
