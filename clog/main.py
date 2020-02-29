import toml


def main():
    config = {}
    config.update(toml.loads(Path(config.toml).read_text()))


if __name__ == "__main__":
    main()
