from argparse import ArgumentParser as ArgParser
from collections import defaultdict
from pprint import pprint
import yaml

class Item:
    def __init__(self, name, count):
        self.name = name
        self.count = int(count)

    def __repr__(self):
        return f"Item(name={self.name!r}, count={self.count})"

def main():
    args = parse_args()

    item = parse_item(args.item)
    print(f"Crafting {fmt_item(item)}")

    recipes = load_recipes(args.source)
    print(f"Recipes have been loaded from {args.source}")

    if input("Dump recipes? [enter to skip] "):
        pprint(dict(recipes))

    recipe = flatten_recipe(calculate(item, recipes))
    print(f"To craft {fmt_item(item)}, you will need:")
    print(fmt_recipe(recipe))

def parse_args():
    parser = ArgParser(description="calculate required ingredients for complicated Minetest craft trees")
    parser.add_argument("item", help="fully qualified string of item to craft")
    parser.add_argument("source", nargs="+", help="YAML files containing recipes")

    return parser.parse_args()

def parse_item(item):
    try:
        name, count = item.split(" ")
        return Item(name, count)
    except ValueError:
        return Item(item, 1)

def load_recipes(sources):
    recipes = defaultdict(list)

    for source in sources:
        with open(source) as f:
            for k, v in yaml.safe_load(f).items():
                recipes[k].extend(v)

    return dict(recipes)

def fmt_recipe(recipe, indent=0):
    return "\n".join(["\t" * indent + "- " + fmt_item(item) for item in recipe])

def fmt_recipe_str(recipe, indent=0):
    return "\n".join(["\t" * indent + "- " + fmt_item(parse_item(item)) for item in recipe])

def fmt_item(item):
    return f"{item.count} x {item.name}"

def calculate(item, recipes, indent=0):
    try:
        delegation = delegate(item, recipes[item.name], indent)
    except KeyError:
        do_indent(indent)
        print(f"Item {item.name} has no recipe")
        return [item]

    ingredients = []

    for k, v in delegation.items():
        item_ = Item(item.name, v)
        do_indent(indent)
        print(f"Crafting {fmt_item(item_)} using recipe #{k}")
        ingredients.extend(follow_recipe(item_, k - 1, recipes, indent + 1))
        do_indent(indent)
        print(f"Done crafting {fmt_item(item_)}")

    return ingredients

def delegate(item, item_recipes, indent):
    for i, recipe in enumerate(item_recipes):
        do_indent(indent)
        print(f"Recipe #{i+1} for {item.name}:")
        print(fmt_recipe_str(recipe, indent))

    if len(item_recipes) == 1:
        do_indent(indent)
        print(f"Auto-choosing because there is only one recipe")
        return {1: item.count}

    delegation = defaultdict(int)
    remaining = item.count

    while remaining > 0:
        recipe = -1
        while not (1 <= recipe <= len(item_recipes)):
            do_indent(indent)
            print(f"Select a recipe to craft {item.name}? [1-{len(item_recipes)}] ", end="")
            recipe = get_int(indent)

        uses = -1
        while not (1 <= uses <= remaining):
            do_indent(indent)
            print(f"How many times to use recipe #{recipe}? [1-{remaining}] ", end="")
            uses = get_int(indent)

        delegation[recipe] += uses
        remaining -= uses

        do_indent(indent)
        print(f"Need to choose {remaining} more recipes...")

    return delegation

def get_int(indent):
    while True:
        try:
            return int(input().strip())
        except ValueError:
            do_indent(indent)
            print("Input a valid integer: ", end="")

def follow_recipe(item, which, recipes, indent):
    recipe = recipes[item.name][which]
    ingredients = []

    for subitem in recipe:
        subitem = parse_item(subitem)
        subitem.count *= item.count

        do_indent(indent)
        print(f"Crafting {fmt_item(item)} requires {fmt_item(subitem)}")
        ingredients.extend(calculate(subitem, recipes, indent))

    return ingredients

def flatten_recipe(recipe):
    counter = defaultdict(int)
    for item in recipe:
        counter[item.name] += item.count

    result = []
    for k, v in counter.items():
        result.append(Item(k, v))

    return result

def do_indent(indent):
    print("\t" * indent, end="")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
    except Exception as e:
        print(str(e))

