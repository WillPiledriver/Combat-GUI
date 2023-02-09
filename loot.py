import tools
import random
import os
import re

root_path = os.path.dirname(__file__) + "\\GUI\\data\\FNT\\"
all_items = tools.csv_to_dict(root_path+"loot.csv", "NAME")


class Loot:
    GUARANTEED = 0
    JUNK = 1  # Grey
    COMMON = 2  # White
    UNCOMMON = 3  # Green
    RARE = 4  # Blue
    EPIC = 5  # Purple
    MYTHIC = 6  # Orange
    UNIQUE = 7  # Gold

    rarities = ["GUARANTEED", "JUNK", "COMMON", "UNCOMMON", "RARE", "EPIC", "MYTHIC", "UNIQUE"]

    def __init__(self, name, category, weight=1, amount=1, rarity=JUNK, value=0):
        self.name = name
        self.category = category
        self.weight = weight
        self.amount_orig = amount
        self.rarity = rarity
        self.value = int(value)

    @property
    def amount(self):
        if isinstance(self.amount_orig, str) and "-" in self.amount_orig:
            min_amount, max_amount = map(int, re.findall(r"\d+", self.amount_orig))
            return random.randint(min_amount, max_amount)
        else:
            return int(self.amount_orig)

    @amount.setter
    def amount(self, new_value):
        self.amount_orig = new_value

    def __str__(self):
        return f"{self.amount} {self.name} found - estimated value: " \
               f"{self.amount * self.value} - ({self.rarities[self.rarity]})"


class LootTable:
    def __init__(self, item_dict):
        self.all_loot = []
        if isinstance(item_dict, list):
            self.all_loot = item_dict
        else:
            for name, item_data in item_dict.items():
                rarity = Loot.rarities.index(item_data["RARITY"])
                category = item_data["CATEGORY"]
                weight = int(item_data["WEIGHT"])
                value = item_data["VALUE"]
                amount = item_data["AMOUNT"]
                loot = Loot(name, category, weight, amount=amount, rarity=rarity, value=value)
                self.all_loot.append(loot)

    def __getitem__(self, name):
        return self.all_loot[name]

    def __add__(self, other):
        return LootTable(self.all_loot + other.all_loot)

    def search_by_category(self, category):
        if isinstance(category, str):
            filtered_items = [item for item in self.all_loot if item.category == category]
        elif isinstance(category, list):
            filtered_items = [item for item in self.all_loot if item.category in category]
        else:
            raise ValueError("Invalid category argument. Must be either a string or a list of strings.")
        return LootTable(filtered_items)

    def search_by_rarity(self, rarity):
        if isinstance(rarity, int):
            filtered_items = [item for item in self.all_loot if item.rarity == rarity]
        elif isinstance(rarity, list):
            filtered_items = [item for item in self.all_loot if item.rarity in rarity]
        else:
            raise ValueError("Invalid rarity argument. Must be either an int or a list of ints.")
        return LootTable(filtered_items)


class Chest:
    def __init__(self, loot_table, num_items):
        self.loot_table = loot_table
        self.num_items = num_items

    def open(self, rarity=Loot.JUNK, ensure_rarity=True):
        multiples = ["currency", "ammo"]
        good = False
        count = 0
        while not good:
            items = []
            filtered_items = [item for item in self.loot_table.all_loot if item.rarity <= rarity]
            total_weight = sum([item.weight for item in filtered_items])
            for i in range(min(self.num_items, len(filtered_items))):
                random_weight = random.uniform(0, total_weight)
                current_weight = 0
                for item in filtered_items:
                    current_weight += item.weight
                    if current_weight >= random_weight:
                        if isinstance(item.amount_orig, str) and "-" in item.amount_orig:
                            min_amount, max_amount = map(int, re.findall(r"\d+", item.amount_orig))
                            if item.category in multiples:
                                min_amount *= (rarity - item.rarity) + 1
                                max_amount *= (rarity - item.rarity) + 1
                            item.amount = random.randint(min_amount, max_amount)

                        if item.rarity == rarity and ensure_rarity:
                            good = True
                        items.append(item)
                        total_weight -= item.weight
                        filtered_items.remove(item)
                        break
            count += 1
            if count >= 250:
                count = 0
                rarity -= 1
            if good or not ensure_rarity:
                return items


for i in range(100):
    for l in Chest(LootTable(all_items).search_by_rarity([Loot.RARE, Loot.UNCOMMON]), 5).open(Loot.RARE, False):
        print(l)
    print()
