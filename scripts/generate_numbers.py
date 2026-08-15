import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lotto.generate import explain, generate_combination


def main() -> None:
    for rule in ("independent", "fixed"):
        result = generate_combination(rule)
        print(explain(result))
        print()


if __name__ == "__main__":
    main()
