from dot.cli import build_parser, DotArgs

def main():
    parser = build_parser()

    args = parser.parse_args(namespace=DotArgs())

    print("Hello from dot!")
    print(args.action)
    if args.action == "add":
        print(args.name)

    if args.config:
        print(args.config)


if __name__ == "__main__":
    main()
