import argparse
import sys

from .build import build


def main() -> int:
    parser = argparse.ArgumentParser(prog="artgen")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_cmd = sub.add_parser("build", help="run generators + pixel-lint")
    build_cmd.add_argument("--only", help="manifest stem or generator module to build")
    args = parser.parse_args()
    if args.cmd == "build":
        return build(args.only)
    return 2


if __name__ == "__main__":
    sys.exit(main())
