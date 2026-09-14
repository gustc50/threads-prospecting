"""Command-line interface for generating Threads posts and replies."""

import argparse
import sys

from .client import MissingAPIKeyError
from .config import load_account_config
from .generator import generate_post, generate_reply


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="threads-prospecting")
    parser.add_argument(
        "--config",
        default="account.yaml",
        help="Path to the account config YAML file (default: account.yaml)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    post_parser = subparsers.add_parser("post", help="Generate a new Threads post")
    post_parser.add_argument("--topic", required=True, help="Topic or angle for the post")

    reply_parser = subparsers.add_parser("reply", help="Generate a reply to a comment")
    reply_parser.add_argument("--comment", required=True, help="The comment to reply to")

    args = parser.parse_args(argv)

    try:
        account = load_account_config(args.config)

        if args.command == "post":
            print(generate_post(account, args.topic))
        elif args.command == "reply":
            reply = generate_reply(account, args.comment)
            print(reply if reply is not None else "SKIP")
    except FileNotFoundError:
        print(f"Erro: arquivo de config '{args.config}' não encontrado.", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except MissingAPIKeyError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
