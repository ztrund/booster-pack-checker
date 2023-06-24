# Booster Pack Checker

The `Booster Pack Checker` is a tool developed for checking the expected values of Steam trading card booster packs
against their market prices. It identifies any booster packs that have a higher expected value than their current listed
price.

## Features

- Scrapes current booster pack and trading card prices from the Steam Community Market.
- Calculates expected values of booster packs based on trading card prices.
- Identifies profitable booster packs.
- Stores and updates data in a SQLite database.

## Installation

1. Clone the repository

```sh
git clone https://github.com/ztrund/booster-pack-checker.git
```

2.Navigate to the project directory

```sh
cd booster-pack-checker
```

3.Install the requirements

```sh
pip install -r requirements.txt
```

## Usage

After successfully installing the project, you can run the Booster Pack Checker by executing the booster_checker_cli.py
script in the root of the project.

```sh
python booster_checker_cli.py
```

The script presents a command-line interface (CLI) menu to the user with various options. Simply follow the prompts on
the CLI to use the tool. These prompts guide you through the process of logging into Steam, fetching booster pack data,
updating trading card prices, and identifying profitable booster packs.

## License

[MIT](LICENSE)