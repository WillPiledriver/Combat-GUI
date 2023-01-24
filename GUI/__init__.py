import math
import random
from tkinter import *
from ttkwidgets.autocomplete import AutocompleteCombobox
from tkinter.scrolledtext import ScrolledText
from collections import OrderedDict
from operator import *
import copy
import csv
import json
import re
import tools
import os
import random as rand


def csv_to_dict(path, name):
    c = csv.DictReader(open(path))
    return {row[name]: {x: row[x] for x in row if not x == name} for row in c}


root_path = os.path.dirname(__file__) + "\\data\\FNT\\"


class Skirmish:
    def __init__(self, comb, weapons, armors):
        self.combatants = copy.deepcopy(comb)
        self.weapon_dict = weapons
        self.armor_dict = armors

        class Constant:
            env = {
                "neutral": {
                    "HIT": 0,
                    "RANGE": 1
                },
                "sunny": {
                    "HIT": 5,
                    "RANGE": 1.1
                },
                "dark": {
                    "HIT": -5
                },
                "night": {
                    "HIT": -10,
                    "RANGE": 0.75
                },
                "foggy": {
                    "HIT": -20,
                    "RANGE": 0.5
                },
                "rainy": {
                    "HIT": -10,
                    "RANGE": .85
                }
            }
            pos = {
                "h": {
                    "LEVEL": 2,
                    "RANGE": 1.15
                },
                "m": {
                    "LEVEL": 1,
                    "RANGE": 1
                },
                "l": {
                    "LEVEL": 0,
                    "RANGE": .85
                }
            }
            cov = {
                "flanked": -25,
                "wide": -10,
                "neutral": 0,
                "mid": 10,
                "full": 25
            }
            s_e = {
                "crouched": {
                    "HIT": 5,
                    "AC": 3,
                    "INSTANT": True
                },
                "prone": {
                    "HIT": 7,
                    "AC": 5,
                    "INSTANT": True
                },
                "on fire": {
                    "HP": -3,
                    "AP": -2,
                    "HIT": -20,
                    "COOLDOWN": 2,
                    "INSTANT": False
                },
                "drunk": {
                    "HIT": -10,
                    "MD": 2,
                    "INSTANT": True
                },
                "stimpack": {
                    "HP": 10,
                    "COOLDOWN": 2,
                    "INSTANT": True
                },
                "crippled": {
                    "SQ": -5,
                    "AP": -2,
                    "COOLDOWN": 3,
                    "INSTANT": True
                },
                "concussed": {
                    "HIT": -10,
                    "AP": -3,
                    "COOLDOWN": 3,
                    "INSTANT": True
                },
                "blind": {
                    "HIT": -60,
                    "SQ": -2,
                    "INSTANT": True
                },
                "bleeding": {
                    "HP": -4,
                    "COOLDOWN": 2,
                    "INSTANT": False
                },
                "poisoned": {
                    "HP": -2,
                    "COOLDOWN": 2,
                    "INSTANT": False
                },
                "jet": {
                    "AP": 2,
                    "S": 1,
                    "P": 1,
                    "INSTANT": True
                },
                "buffout": {
                    "S": 2,
                    "E": 3,
                    "A": 2,
                    "INSTANT": True
                },
                "psycho": {
                    "DMG": 1.25,
                    "A": 2,
                    "INSTANT": True
                },
                "super stimpack": {
                    "HP": 35,
                    "COOLDOWN": 1,
                    "INSTANT": True
                },
                "med-x": {
                    "DR": 50,
                    "INSTANT": True
                }
            }

        # TODO: incorporate SPECIAL and DR into combat effects and detect random values
        # TODO: calculate all skills on the fly using calc_base + code from prep functions or recalculate them from -
        # TODO: calc_turn if attributes have changed
        # TODO: change turn order when SQ is changed

        self.con = Constant()
        self.turn = 0
        self.hit_mod = 0
        self.temp_ap = 0
        self.temp_sq = 0
        self.temp_xp = 0
        self.environment = None

        self.combatant_list = OrderedDict(sorted(self.combatants.items(), key=lambda x: getitem(x[1]["secondary_skills"], "SQ"), reverse=True))

        self.start()

    @property
    def cur_combatant(self):
        try:
            return list(self.combatant_list.items())[self.turn % len(self.combatant_list)][0]
        except:
            return None

    @property
    def temp_md(self):
        try:
            n = self.combatants[self.cur_combatant]["secondary_skills"]["MD"]
            if "eff" in self.combatants[self.cur_combatant]:
                for k, d in self.combatants[self.cur_combatant]["eff"].items():
                    if "MD" in d:
                        n += int(d["MD"])
            return n
        except Exception as e:
            print(type(e), e)
            return None

    def update_combatants(self, comb):
        self.combatants = copy.deepcopy(comb)
        self.combatant_list = OrderedDict(sorted(self.combatants.items(), key=lambda x: getitem(x[1]["secondary_skills"], "SQ"), reverse=True))
        for k, d in self.combatants.items():
            if "effects" not in d:
                self.combatants[k]["eff"] = dict()
                self.combatants[k]["cov"] = "neutral"
                self.combatants[k]["pos"] = "m"

    def get_combatants(self):
        exclude = ["cov", "eff", "pos"]
        return {k: d for k, d in self.combatants if k not in exclude}

    def start(self):
        # self.cur_combatant = list(self.combatant_list.items())[self.turn % len(self.combatant_list)][0]
        self.environment = "neutral"
        for k, d in self.combatants.items():
            if "eff" not in d:
                self.combatants[k]["eff"] = dict()
                self.combatants[k]["cov"] = "neutral"
                self.combatants[k]["pos"] = "m"

    def calc_turn(self, attacker, defender, update=False):
        if defender == "":
            result = None
            if update:
                delete_effects = list()
                if len(self.combatants[attacker]["eff"]) > 0:
                    if isinstance(self.combatants[attacker]["eff"], list):
                        temp = dict()
                        for l_effect in self.combatants[attacker]["eff"]:
                            temp[l_effect] = dict(self.con.s_e[l_effect])
                        self.combatants[attacker]["eff"] = dict(temp)
                    for ky, dt in self.combatants[attacker]["eff"].items():
                        if isinstance(self.combatants[attacker]["eff"][ky], str):
                            self.combatants[attacker]["eff"][ky] = dict(self.con.s_e[self.combatants[attacker]["eff"][ky]])
                    for e in self.combatants[attacker]["eff"]:
                        for effect, val in self.combatants[attacker]["eff"][e].items():
                            if effect in self.combatants[attacker]["secondary_skills"]:
                                if effect == "AP":
                                    self.temp_ap = val + int(self.combatants[attacker]["secondary_skills"]["AP"])
                                elif effect == "SQ":
                                    self.temp_sq = val + int(self.combatants[attacker]["secondary_skills"]["SQ"])
                                elif effect == "HP":
                                    if result is None:
                                        result = dict()
                                        result["PRETEXT"] = ""
                                    if val < 1:
                                        result["PRETEXT"] += f"{self.cur_combatant} took {val * -1} damage from being {e} - {self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val} HP\n"
                                    else:
                                        if self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val > self.combatants[self.cur_combatant]['secondary_skills']['MAX HP']:
                                            val = self.combatants[self.cur_combatant]['secondary_skills']['MAX HP'] - self.combatants[self.cur_combatant]['secondary_skills']['HP']
                                        result["PRETEXT"] += f"{self.cur_combatant} healed {val} HP from the {e} - {self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val} HP\n"
                                    self.combatants[attacker]["secondary_skills"][effect] += val

                        if "COOLDOWN" in self.combatants[attacker]["eff"][e]:
                            self.combatants[attacker]["eff"][e]["COOLDOWN"] -= 1
                            print("COOL")
                            if self.combatants[attacker]["eff"][e]["COOLDOWN"] == 0:
                                delete_effects.append(e)
                    for e in delete_effects:
                        del self.combatants[attacker]["eff"][e]
                    return result
            return result
        a = self.combatants[attacker]
        d = self.combatants[defender]
        skill = self.weapon_dict[a["WEAPON"]]["SKILL"]

        roll_to_hit = int(a["combat_skills"][skill])

        self.hit_mod = 0

        stuff = {
            "PRETEXT": "",
            "SKILL": str(skill),
            "CTH": int(roll_to_hit),
            "ENV": int(self.con.env[self.environment]["HIT"]),
            "COV": int(self.con.cov[d["cov"]]),
            "POS": (self.con.pos[a["pos"]]["LEVEL"] - self.con.pos[d["pos"]]["LEVEL"]) * 10
        }
        # Defender AC
        ac_temp = int(self.armor_dict[d["ARMOR"]]["AC"])

        # Environment modifier
        self.hit_mod += self.con.env[self.environment]["HIT"]

        # Cover Modifier
        self.hit_mod -= self.con.cov[d["cov"]]

        # Height Modifier
        self.hit_mod += (self.con.pos[a["pos"]]["LEVEL"] - self.con.pos[d["pos"]]["LEVEL"]) * 10

        self.temp_ap = int(a["secondary_skills"]["AP"])
        delete_effects = list()

        # Calculate status effects
        for c in (a, d):
            if len(c["eff"]) > 0:
                if isinstance(c["eff"], list):
                    temp = dict()
                    for l_effect in c["eff"]:
                        temp[l_effect] = dict(self.con.s_e[l_effect])
                    c["eff"] = dict(temp)
                for ky, dt in c["eff"].items():
                    if isinstance(c["eff"][ky], str):
                        c["eff"][ky] = dict(self.con.s_e[c["eff"][ky]])
                for e in self.combatants[attacker]["eff"]:
                    for effect, val in self.combatants[attacker]["eff"][e].items():
                        if effect in c["secondary_skills"]:
                            if effect == "AP":
                                self.temp_ap = val + int(self.combatants[attacker]["secondary_skills"]["AP"])
                            elif effect == "SQ":
                                self.temp_sq = val + int(self.combatants[attacker]["secondary_skills"]["SQ"])
                            elif effect == "HP":
                                if c is a and update:
                                    if val < 1:
                                        stuff["PRETEXT"] += f"{self.cur_combatant} took {val * -1} damage from being {e} - {self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val} HP\n"
                                    else:
                                        if self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val > self.combatants[self.cur_combatant]['secondary_skills']['MAX HP']:
                                            val = self.combatants[self.cur_combatant]['secondary_skills']['MAX HP'] - self.combatants[self.cur_combatant]['secondary_skills']['HP']
                                        stuff["PRETEXT"] += f"{self.cur_combatant} healed {val} HP from the {e} - {self.combatants[self.cur_combatant]['secondary_skills']['HP'] + val} HP\n"
                                    c["secondary_skills"][effect] += val
                                else:
                                    continue

                    if "HIT" in self.combatants[attacker]["eff"][e]:
                        if c is a:
                            if "EFF" in stuff:
                                stuff["EFF"] += self.combatants[attacker]["eff"][e]["HIT"]
                            else:
                                stuff["EFF"] = self.combatants[attacker]["eff"][e]["HIT"]
                            self.hit_mod += self.combatants[attacker]["eff"][e]["HIT"]
                    if "COOLDOWN" in self.combatants[attacker]["eff"][e] and c is a and update:
                        self.combatants[attacker]["eff"][e]["COOLDOWN"] -= 1
                        print("COOL")
                        if self.combatants[attacker]["eff"][e]["COOLDOWN"] == 0:
                            delete_effects.append(e)
                for e in delete_effects:
                    del self.combatants[attacker]["eff"][e]

                delete_effects = list()

        for def_eff in self.combatants[defender]["eff"]:
            if "AC" in self.combatants[defender]["eff"][def_eff]:
                ac_temp += self.combatants[defender]["eff"][def_eff]["AC"]

        stuff["AC"] = ac_temp
        self.hit_mod -= ac_temp
        return stuff


class GUI:
    def __init__(self):
        self.temp_calc = None
        self.attributes = ["S", "P", "E", "C", "I", "A", "L"]
        self.skills = {"AR": {"eq": "{S}+{P}+(2*{A})"},
                       "SG": {"eq": "5+{P}+(3*{A})"},
                       "BG": {"eq": "{S}+{E}+{A}"},
                       "EW": {"eq": "{P}+{I}+{A}"},
                       "U": {"eq": "30+2*({A}+{S})"},
                       "M": {"eq": "20+2*({A}+{S})"},
                       "TH": {"eq": "{S}+(3*{A})"},
                       "FA": {"eq": "2*({P}+{I})"},
                       "D": {"eq": "5+{P}+{I}"},
                       "SN": {"eq": "5+3*{A}"},
                       "LP": {"eq": "10+{P}+{A}"},
                       "ST": {"eq": "3*{A}"},
                       "TR": {"eq": "{P}+{A}"},
                       "SC": {"eq": "4*{I}"},
                       "R": {"eq": "3*{I}"},
                       "PI": {"eq": "2*({A}+{P})"},
                       "SP": {"eq": "5*{C}"},
                       "SU": {"eq": "2*({E}+{I})"},
                       }
        self.combat_skills = {"AR": {"eq": "{S}+{P}+(2*{A})"},
                              "SG": {"eq": "5+{P}+(3*{A})"},
                              "BG": {"eq": "{S}+{E}+{A}"},
                              "EW": {"eq": "{P}+{I}+{A}"},
                              "U": {"eq": "30+2*({A}+{S})"},
                              "M": {"eq": "20+2*({A}+{S})"},
                              "TH": {"eq": "{S}+(3*{A})"}
                              }
        self.secondary = {"SQ": {"eq": "{A}+2*{P}"},
                          "AP": {"eq": "({A}/2)+5"},
                          "MD": {"eq": "{S}-5"},
                          "CRIT": {"eq": "{L}"},
                          "HP": {"eq": "15+{S}+(2*{E})"},
                          }

        self.players = csv_to_dict((root_path + "players.csv"), "NAME")
        self.enemies = csv_to_dict((root_path + "enemies.csv"), "NAME")
        self.armors = csv_to_dict((root_path + "armors.csv"), "NAME")
        self.weapons = csv_to_dict((root_path + "weapons.csv"), "NAME")
        self.ammo = csv_to_dict((root_path + "ammo.csv"), "NAME")

        for k in self.enemies.keys():
            self.enemies[k]["NAMES"] = self.enemies[k]["NAMES"].split(",")
            rand.shuffle(self.enemies[k]["NAMES"])

        self.clean_tables()
        self.prep_players()
        self.all_combatants = dict(**self.enemies, **self.players)
        self.prepped_combatants = dict()

        self.root = Tk()

    def reload(self):
        self.players = csv_to_dict((root_path + "players.csv"), "NAME")
        self.enemies = csv_to_dict((root_path + "enemies.csv"), "NAME")
        self.armors = csv_to_dict((root_path + "armors.csv"), "NAME")
        self.weapons = csv_to_dict((root_path + "weapons.csv"), "NAME")
        self.ammo = csv_to_dict((root_path + "ammo.csv"), "NAME")

        for k in self.enemies.keys():
            self.enemies[k]["NAMES"] = self.enemies[k]["NAMES"].split(",")
            rand.shuffle(self.enemies[k]["NAMES"])

        self.clean_tables()
        self.prep_players()
        self.all_combatants = dict(**self.enemies, **self.players)
        self.prepped_combatants = dict()

    def clean_tables(self):
        tables = [self.enemies, self.players]
        for t in tables:
            for k, d in t.items():
                for kk, dd in d.items():
                    if isinstance(dd, list):
                        pass
                    elif dd.isnumeric():
                        t[k][kk] = int(t[k][kk])

    def generate_enemy(self, name, weapon=None, armor=None):
        enemy = dict(self.enemies[name])
        enemy["NAME"] = name
        randnum_match = re.compile("^[0-9]+-[0-9]+$")
        num_match = re.compile("^[0-9]+$")

        if "NAMES" in enemy:
            for n in enemy["NAMES"]:
                if len(n) == 0:
                    enemy["NAMES"].remove(n)

        for key, value in enemy.items():
            if isinstance(value, (str,)) is False:
                continue
            if re.match(num_match, value):
                # Any integer
                enemy[key] = int(value)
            elif re.match(randnum_match, value):
                # Random number range
                splt = value.split("-")
                r = rand.randint(int(splt[0]), int(splt[1]))
                enemy[key] = r
            if value.count(",") > 0:
                # random list of strings
                enemy[key] = value.split(",")

        if weapon is None:
            if isinstance(enemy["WEAPON"], (list,)):
                # Random weapon
                enemy["WEAPON"] = enemy["WEAPON"][rand.randint(0, len(enemy["WEAPON"]) - 1)]
        else:
            enemy["WEAPON"] = weapon
        if armor is None:
            if isinstance(enemy["ARMOR"], (list,)):
                # Random armor
                enemy["ARMOR"] = enemy["ARMOR"][rand.randint(0, len(enemy["ARMOR"]) - 1)]
        else:
            enemy["ARMOR"] = armor

        if "BONUS" in enemy:
            # Parse and restructure bonuses
            if isinstance(enemy["BONUS"], (list,)):
                bns = {}
                for b in enemy["BONUS"]:
                    splt = b.split(" ")
                    if re.match(randnum_match, splt[1]):
                        splt2 = splt[1].split("-")
                        bns[splt[0]] = rand.randint(int(splt2[0]), int(splt2[1]))
                    else:
                        bns[splt[0]] = int(splt[1])
                enemy["BONUS"] = bns
            else:
                splt = enemy["BONUS"].split(" ")
                if re.match(randnum_match, splt[1]):
                    splt2 = splt[1].split("-")
                    r = rand.randint(int(splt2[0]), int(splt2[1]))
                else:
                    r = int(splt[1])
                enemy["BONUS"] = {splt[0]: r}
        enemy = self.populate(enemy)
        return enemy

    def populate(self, enemy):
        result = dict()
        result["combat_skills"] = {key: dict(self.combat_skills[key]) for key in self.combat_skills}
        result["secondary_skills"] = {key: dict(self.secondary[key]) for key in self.secondary}
        result["WEAPON"] = enemy["WEAPON"]
        result["ARMOR"] = enemy["ARMOR"]
        result["bonus"] = enemy["BONUS"]
        result["xp"] = enemy["XP"]
        result["level"] = enemy["LEVEL"]
        result["enemy_id"] = enemy["NAME"]
        result["skills"] = {key: dict(self.skills[key]) for key in self.skills}

        attributes = {key.upper(): enemy[key] for key in self.attributes
                      if key.upper() in enemy}

        result["attributes"] = attributes

        # Armor Bonus for attributes
        for b_split in self.armors[result["ARMOR"]]["BONUS"].split(","):
            if b_split == "":
                continue
            b_split = b_split.split(" ")
            b_split[1] = int(b_split[1])
            if b_split[0] in result["attributes"]:
                result["attributes"][b_split[0]] += b_split[1]

        for cmbt_skill in self.combat_skills.keys():
            result["combat_skills"][cmbt_skill] = self.calc_base(result["attributes"], self.combat_skills[cmbt_skill]["eq"])

        for skill in self.skills.keys():
            result["skills"][skill] = self.calc_base(result["attributes"], self.skills[skill]["eq"])

        for secondary in self.secondary.keys():
            if secondary in enemy:
                result["secondary_skills"][secondary] = enemy[secondary]
            else:
                result["secondary_skills"][secondary] = self.calc_base(result["attributes"], self.secondary[secondary]["eq"])
            if secondary == "AP":
                if result["secondary_skills"][secondary] < 5:
                    result["secondary_skills"]["AP"] = 5
                result["secondary_skills"]["AP"] = math.ceil(result["secondary_skills"]["AP"])
            if secondary == "MD" and result["secondary_skills"][secondary] < 0:
                result["secondary_skills"][secondary] = 0

        for key, value in result["bonus"].items():
            if key in result["skills"]:
                result["skills"][key] += value
                if key in result["combat_skills"]:
                    result["combat_skills"][key] += value
            elif key in self.secondary:
                result["secondary_skills"][key] += value
            else:
                print("bonus {} does nothing".format(key))

        # Armor Bonus for skills
        for b_split in self.armors[result["ARMOR"]]["BONUS"].split(","):
            if b_split == "":
                continue
            b_split = b_split.split(" ")
            b_split[1] = int(b_split[1])
            if b_split[0] in result["skills"]:
                result["skills"][b_split[0]] += b_split[1]
                if b_split[0] in result["combat_skills"]:
                    result["combat_skills"][b_split[0]] += b_split[1]
            elif b_split[0] in self.secondary:
                result["secondary_skills"][b_split[0]] += b_split[1]
            else:
                print("bonus {} does nothing".format(b_split[0]))

        result["secondary_skills"]["MAX HP"] = result["secondary_skills"]["HP"]

        result["bonus"] = dict()
        return result

    def calc_base(self, attributes, eq):
        """
        Calculates a given equation by replacing strings with variables.
        :param attributes: Dict of attributes with "var" keys.
        :param eq: Equation to perform.
        :return: Solution of the equation.
        """

        attributes = {key: attributes[key] for key in attributes.keys()}
        for key in attributes:
            eq = eq.replace("{"+key+"}", str(attributes[key]))
        exec("self.temp_calc=" + eq)
        return self.temp_calc

    def prep_players(self):
        for k, d in self.players.items():
            if "combat_skills" not in self.players[k]:
                # Calculate Combat Skills
                self.players[k]["combat_skills"] = dict()
                attributes = {key.upper(): self.players[k][key] for key in self.attributes
                              if key.upper() in self.players[k]}
                self.players[k]["attributes"] = attributes

                # Armor Bonus Attributes
                for armor_bns_splt in self.armors[self.players[k]["ARMOR"]]["BONUS"].split(","):
                    if armor_bns_splt == "":
                        continue
                    armor_bns_splt = armor_bns_splt.split(" ")
                    if armor_bns_splt[0] in self.attributes:
                        self.players[k]["attributes"][armor_bns_splt[0]] += int(armor_bns_splt[1])

                for skill in self.combat_skills.keys():
                    self.players[k]["combat_skills"][skill] = self.calc_base(self.players[k]["attributes"],
                                                                             self.combat_skills[skill]["eq"])

                # Calculate secondary skills
                self.players[k]["secondary_skills"] = dict()
                for skill in self.secondary.keys():
                    self.players[k]["secondary_skills"][skill] = self.calc_base(self.players[k]["attributes"],
                                                                                self.secondary[skill]["eq"])
                    if skill == "AP":
                        if self.players[k]["secondary_skills"]["AP"] < 5:
                            self.players[k]["secondary_skills"]["AP"] = 5
                        self.players[k]["secondary_skills"]["AP"] = math.ceil(self.players[k]["secondary_skills"]["AP"])
                    if skill == "MD" and self.players[k]["secondary_skills"][skill] < 0:
                        self.players[k]["secondary_skills"][skill] = 0

                for s in (list("SPECIAL") + ["AP", "MD", "CRIT", "SQ"]):
                    if s in self.players[k]:
                        del self.players[k][s]

                # Calculate bonus
                bonus = self.players[k]["BONUS"].split(",")
                bns = list()
                for b in bonus:
                    bns.append(tuple(b.split(" ")))
                for b in bns:
                    if b[0] in self.players[k]:
                        self.players[k][b[0]] += int(b[1])
                    if b[0] in self.players[k]["secondary_skills"]:
                        self.players[k]["secondary_skills"][b[0]] += int(b[1])
                    if b[0] in self.players[k]["attributes"]:
                        self.players[k]["attributes"][b[0]] += int(b[1])
                    if b[0] in self.players[k]["combat_skills"]:
                        self.players[k]["combat_skills"][b[0]] += int(b[1])

                # Armor Bonus skills
                for armor_bns_splt in self.armors[self.players[k]["ARMOR"]]["BONUS"].split(","):
                    if armor_bns_splt == "":
                        continue
                    armor_bns_splt = armor_bns_splt.split(" ")
                    if armor_bns_splt[0] in self.players[k]["combat_skills"]:
                        self.players[k]["combat_skills"][armor_bns_splt[0]] += int(armor_bns_splt[1])
                    if armor_bns_splt[0] in self.players[k]["secondary_skills"]:
                        self.players[k]["secondary_skills"][armor_bns_splt[0]] += int(armor_bns_splt[1])

                self.players[k]["secondary_skills"]["MAX HP"] = self.players[k]["secondary_skills"]["HP"]
                self.players[k]["BONUS"] = ""

    def main_menu(self):
        self.root.geometry("704x400")
        self.frame = Frame(self.root, padx=10, pady=10)
        self.selected_stat = None
        self.frame.pack()

        self.blue_list = Listbox(self.frame, bg="#a1d0ff", height=20, width=32, activestyle="none")
        self.red_list = Listbox(self.frame, bg="#fa9898", height=20, width=32, activestyle="none")
        self.stat_frame = Frame(self.frame, width=250, height=350)
        selected_combatant = StringVar()

        # initial menu text
        selected_combatant.set("<Choose Combatant>")

        # Create Dropdown menu
        player_keys = list(self.players.keys())
        enemy_keys = list(self.enemies.keys())
        final_list = ["<Choose Combatant>"] + player_keys + enemy_keys
        drop = OptionMenu(self.stat_frame, selected_combatant, *final_list)
        drop.place(y=15, relx=0.5, anchor=CENTER)

        # Move Buttons
        btn_mv_blue = Button(self.stat_frame, text="<", command=lambda: mv_btn(selected_combatant, "b"))
        btn_mv_red = Button(self.stat_frame, text=">", command=lambda: mv_btn(selected_combatant, "r"))

        def clear_all():
            self.reload()
            stat_text.delete("1.0", END)
            self.red_list.delete(0, END)
            self.blue_list.delete(0, END)

        def save_stats():
            self.prepped_combatants[self.selected_stat] = json.loads(stat_text.get("1.0", END))

        # Stat buttons
        btn_save_stats = Button(self.stat_frame, text="Save", command=save_stats)
        btn_clear_all = Button(self.stat_frame, text="Clear All", command=clear_all)
        btn_reroll = Button(self.stat_frame, font="courier 10 bold", bg="black", fg="red",
                            text="COMBAT", command=self.skirmish_menu, activebackground="#302d2d", activeforeground="red")

        btn_save_stats.place(y=330, x=30, anchor=CENTER)
        btn_clear_all.place(y=330, x=110, anchor=CENTER)
        btn_reroll.place(y=330, x=200, anchor=CENTER)
        btn_mv_blue.place(y=15, x=20, anchor=CENTER)
        btn_mv_red.place(y=15, x=230, anchor=CENTER)

        def mv_btn(name, color):
            # Move selected combatant to the appropriate side
            nom = name.get()
            if "FACTION" in self.all_combatants[nom]:
                new_combatant = self.generate_enemy(nom)
                if "NAMES" in self.enemies[nom]:
                    if len(self.enemies[nom]["NAMES"]) > 0:
                        # Use custom names
                        nm = self.enemies[nom]["NAMES"].pop(0)
                    else:
                        # Name sequentially
                        nm = name.get()
                        nm_temp = nm
                        c = 2
                        while nm_temp in self.prepped_combatants:
                            nm_temp = nm + f" {c}"
                            c += 1
                        nm = nm_temp
            else:
                nm = name.get()
                new_combatant = self.all_combatants[name.get()]
            new_combatant["team"] = color
            self.prepped_combatants[nm] = new_combatant
            if color == "b":
                self.blue_list.insert(END, nm)
            else:
                self.red_list.insert(END, nm)

        stat_text = ScrolledText(self.root, height=17, width=28, wrap=WORD)
        stat_text.insert(END, "")
        stat_text.pack(side=LEFT, expand=True, fill=BOTH)
        stat_text.place(y=180, relx=0.5, anchor=CENTER)

        def on_select(evt, color):
            # Called when a name is selected in a list box
            lb = evt.widget
            selection = lb.curselection()
            if len(selection) > 0:
                ind = selection[0]
                v = self.prepped_combatants[lb.get(ind)]
                self.selected_stat = lb.get(ind)
                stat_text.delete("1.0", END)
                stat_text.insert(INSERT, json.dumps(v, indent=1))

        self.red_list.bind("<<ListboxSelect>>", lambda event, color="r": on_select(event, color))
        self.blue_list.bind("<<ListboxSelect>>", lambda event, color="b": on_select(event, color))

#        labels = list()
#        for t in range(len(test)):
#            labels.append(Label(self.stat_frame, text=test[t]))
#            labels[t].pack()
        self.stat_frame.grid(row=0, column=1)
        self.blue_list.grid(row=0, column=0)
        self.red_list.grid(row=0, column=2)

    def skirmish_menu(self):
        skirm = Skirmish(self.prepped_combatants, self.weapons, self.armors)
        s_win = Toplevel(self.root)
        s_win.geometry("800x600")
        s_win.title("Skirmish")
        
        s_frame = LabelFrame(s_win, padx=10, pady=10)
        s_frame.pack()

        # Menu bar
        def change_env(new_env):
            skirm.environment = new_env
            update_everything()

        def reload_combatants():
            skirm.update_combatants(self.prepped_combatants)
            c_listbox.delete(0, END)
            for name, d in skirm.combatant_list.items():
                c_listbox.insert(END, name)
            header_label.config(text=f"TURN: {skirm.turn}\n{list(skirm.combatant_list.keys())[skirm.turn % len(skirm.combatant_list)]}'s turn.")

        menu_bar = Menu(s_win)
        game_menu = Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="Reload Combatants", command=reload_combatants)

        env_menu = Menu(game_menu, tearoff=False)

        temp = list(skirm.con.env.keys())
        for env in range(len(temp)):
            env_menu.add_command(label=temp[env], command=lambda x=temp[env]: change_env(x))

        game_menu.add_cascade(label="Change Environment", menu=env_menu)
        menu_bar.add_cascade(label="Game", menu=game_menu)

        s_win.config(menu=menu_bar)

        # Populate listbox
        c_listbox = Listbox(s_frame, height=10, width=32, selectmode="extended", activestyle="none")
        for name, d in skirm.combatant_list.items():
            c_listbox.insert(END, name)

        header_label = Label(s_frame, text=f"TURN: {skirm.turn}\n{skirm.cur_combatant}'s turn.")
        header_label.grid(row=0, column=0, columnspan=2)

        # Info Frame
        info_frame = Frame(s_frame, width=580, height=250, relief="raised", borderwidth=1)
        info_frame.grid(row=1, column=0, columnspan=2)
        info_font = "courier 10"

        attacker_name = Label(info_frame, text=skirm.cur_combatant, font=info_font+" bold underline")
        defender_name = Label(info_frame, text="")
        attacker_labels = dict()
        attacker_entries = dict()
        defender_labels = dict()
        defender_entries = dict()

        def stat_change(event, name):
            entry = event.widget
            if entry is attacker_entries[name]:
                entries = attacker_entries
                labels = attacker_labels
                com = skirm.cur_combatant
            else:
                entries = defender_entries
                labels = defender_labels
                com = defender_name.cget("text")

            if name == "WEAPON":
                print(name, entry.get())
                try:
                    if entry.get() in skirm.weapon_dict:
                        labels["SKILL"].config(text=f"{skirm.weapon_dict[entry.get()]['SKILL']}:")
                        entries["SKILL"].delete(0, END)
                        t = skirm.weapon_dict[entry.get()]["SKILL"]
                        entries["SKILL"].insert(0, skirm.combatants[com]["combat_skills"][t])
                        skirm.combatants[com]["WEAPON"] = entry.get()
                        update_everything()
                except Exception as e:
                    print(type(e), e)
            elif name == "eff":
                try:
                    skirm.combatants[com][name] = json.loads(entry.get("1.0", END))
                    print(entry.get("1.0", END))
                    if len(skirm.combatants[com][name]) > 0:
                        if isinstance(skirm.combatants[com][name], list):
                            temp = dict()
                            for l_effect in skirm.combatants[com][name]:
                                temp[l_effect] = dict(skirm.con.s_e[l_effect])
                            skirm.combatants[com][name] = dict(temp)
                        for ky, dt in skirm.combatants[com][name].items():
                            if isinstance(skirm.combatants[com][name][ky], str):
                                skirm.combatants[com][name][ky] = dict(skirm.con.s_e[skirm.combatants[com][name][ky]])

                    entry.delete("1.0", END)
                    entry.insert("1.0", json.dumps(skirm.combatants[com][name]))

                    for k, d in skirm.combatants[com][name].items():
                        if "INSTANT" in d:
                            if d["INSTANT"]:
                                # TODO: something
                                pass
                            else:
                                # do nothing
                                pass

                    update_everything()
                except json.decoder.JSONDecodeError:
                    pass
                except Exception as e:
                    print(type(e), e)
            elif name == "ARMOR":
                if entry.get() in skirm.armor_dict:
                    skirm.combatants[com]["ARMOR"] = entry.get()
                    update_everything()
            else:
                try:
                    if entry.get().isnumeric():
                        if name == "SKILL":
                            skill = labels["SKILL"].cget("text").replace(":", "")
                            skirm.combatants[com]["combat_skills"][skill] = int(entry.get())

                        else:
                            skirm.combatants[com]["secondary_skills"][name] = int(entry.get())
                        print(entry.get())
                    else:
                        skirm.combatants[com][name] = entry.get()
                        print(entry.get())
                    update_everything()
                except Exception as e:
                    print(type(e), e)

        def auto_complete_hack(event, name):
            event.widget.handle_keyrelease(event)
            stat_change(event, name)

        def display_info(n, x_offset, y_offset):
            display = ["HP", "AP", "SKILL", "WEAPON", "ARMOR", "cov", "pos", "eff"]
            labels = attacker_labels if skirm.cur_combatant == n else defender_labels
            entries = attacker_entries if skirm.cur_combatant == n else defender_entries

            for label_name in labels:
                labels[label_name].place_forget()
            for entry_name in entries:
                entries[entry_name].place_forget()

            for dis in range(len(display)):
                # Weapon Skill
                if dis == 2:
                    labels["SKILL"] = Label(info_frame, text=f"{skirm.weapon_dict[skirm.combatants[n]['WEAPON']]['SKILL']}:", font=info_font)

                    entries["SKILL"] = Entry(info_frame, width=4, font=info_font)
                    entries["SKILL"].insert(INSERT, str(skirm.combatants[n]["combat_skills"][skirm.weapon_dict[skirm.combatants[n]['WEAPON']]['SKILL']]))
                    labels["SKILL"].place(x=x_offset, y=y_offset + (dis + 1) * 21)
                    entries["SKILL"].place(x=x_offset + 90, y=y_offset + (dis + 1) * 21)
                    entries["SKILL"].bind("<KeyRelease>", lambda event, name="SKILL": stat_change(event, name))
                if display[dis] in skirm.combatants[n]:
                    labels[display[dis]] = Label(info_frame, text=f"{display[dis]}:", font=info_font)

                    if display[dis] == "eff":
                        entries[display[dis]] = Text(info_frame, width=20, height=2, font=info_font)
                        entries[display[dis]].insert("1.0", json.dumps(skirm.combatants[n][display[dis]]))
                        entries[display[dis]].bind("<KeyRelease>",
                                                   lambda event, name=display[dis]: stat_change(event, name))
                    else:
                        if display[dis] == "WEAPON":
                            entries[display[dis]] = AutocompleteCombobox(info_frame, width=18, font=info_font,
                                                                  completevalues=list(skirm.weapon_dict.keys()))
                            entries[display[dis]].bind("<KeyRelease>",
                                                       lambda event, name=display[dis]: auto_complete_hack(event, name))
                        elif display[dis] == "ARMOR":
                            entries[display[dis]] = AutocompleteCombobox(info_frame, width=18, font=info_font,
                                                                      completevalues=list(skirm.armor_dict.keys()))
                            entries[display[dis]].bind("<KeyRelease>",
                                                       lambda event, name=display[dis]: auto_complete_hack(event, name))
                        else:
                            entries[display[dis]] = Entry(info_frame, width=20, font=info_font)
                            entries[display[dis]].bind("<KeyRelease>",
                                                       lambda event, name=display[dis]: stat_change(event, name))
                        entries[display[dis]].insert(INSERT, str(skirm.combatants[n][display[dis]]))
                    labels[display[dis]].place(x=x_offset, y=y_offset + (dis + 1) * 21)
                    entries[display[dis]].place(x=x_offset+90, y=y_offset + (dis + 1) * 21)


                else:
                    check = ["secondary_skills"]
                    for c in check:
                        if display[dis] in skirm.combatants[n][c]:
                            labels[display[dis]] = Label(info_frame,
                                                                  text=f"{display[dis]}:",
                                                                  font=info_font)
                            entries[display[dis]] = Entry(info_frame, width=4, font=info_font)
                            entries[display[dis]].insert(INSERT, str(skirm.combatants[n][c][
                                display[dis]]))
                            labels[display[dis]].place(x=x_offset, y=y_offset + (dis + 1) * 21)
                            entries[display[dis]].place(x=x_offset + 90, y=y_offset + (dis + 1) * 21)

                            entries[display[dis]].bind("<KeyRelease>", lambda event, name=display[dis]: stat_change(event, name))

        display_info(skirm.cur_combatant, 10, 10)

        attacker_name.place(x=10, y=10)
        defender_name.place(x=300, y=10)

        def action_select(event, a):
            if a.get() == "Update Flags":
                flags = ["pos", "cov", "eff"]
                temp_d = dict()
                for f in flags:
                    temp_d[f] = skirm.combatants[c_listbox.get(c_listbox.curselection()[0])][f]

                print(temp_d)
            elif a.get() == "Attack Target":
                target = c_listbox.get(c_listbox.curselection()[0])
                display_info(target, 300, 10)
                defender_name.config(text=target, font="courier 10 bold underline")
                update_everything()
            elif a.get() == "<Choose Action>":
                print("test")

        actions = ["<Choose Action>", "Attack Target", "Update Flags"]
        selected_action = StringVar(s_frame)
        selected_action.set(actions[0])
        action_menu = OptionMenu(s_frame, selected_action, *actions, command=lambda event, a=selected_action: action_select(event, a))
        action_menu.grid(row=0, column=2)
        c_listbox.grid(row=1, column=2)

        # Start turn logic

        def update_everything(change=False):
            header_label.config(text=f"TURN: {skirm.turn}\n{skirm.cur_combatant}'s turn.")

            stuff = skirm.calc_turn(skirm.cur_combatant, defender_name.cget("text"), update=change)
            if stuff is not None:
                if len(stuff) == 1:
                    hit_chance_label.config(text=f"{stuff['PRETEXT']}\nWAITING FOR INPUT...")
                else:
                    hit_chance_label.config(text=f"{stuff['PRETEXT']}{skirm.cur_combatant} is attacking {defender_name.cget('text')}\n"
                                             f"Using the {skirm.combatants[skirm.cur_combatant]['WEAPON']} "
                                             f"the chance to hit is {int(stuff['CTH']) + skirm.hit_mod} ({stuff['CTH']} + ({skirm.hit_mod}))")

            else:
                hit_chance_label.config(text="WAITING FOR INPUT...")
            wd = skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]
            eq = ""
            match wd["SKILL"]:
                case "M" | "U" | "TH" | "EW":
                    eq = f"{wd['DMG']}+{wd['DB'].replace('{MD}', str(skirm.temp_md))}"

                case "BG" | "SG" | "AR":
                    eq = f"{self.ammo[wd['AMMO']]['DMG']}+{wd['DB']}+{wd['DMG']}"

            ap_label.config(text=f"AP: {skirm.temp_ap}\nCOST: {skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]['WEAPON']]['AP']}")
            roll_dmg_eq_label.config(text=eq)
            xp_label.config(text=f"XP: {skirm.temp_xp}")


        def start_combat():
            start_btn.config(text="NEXT TURN >", command=next_turn)
            stuff = skirm.calc_turn(skirm.cur_combatant, defender_name.cget("text"), update=True)
            print(stuff)
            hit_chance_label.config(text=f"{stuff['PRETEXT']}{skirm.cur_combatant} is attacking {defender_name.cget('text')}\n"
                                                        f"Using the {skirm.combatants[skirm.cur_combatant]['WEAPON']} "
                                                        f"the chance to hit is {int(stuff['CTH']) + skirm.hit_mod} ({stuff['CTH']} + ({skirm.hit_mod}))")
            hit_chance_label.place(x=5, y=5)

            wd = skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]
            eq = ""
            match wd["SKILL"]:
                case "M" | "U" | "TH" | "EW":
                    eq = f"{wd['DMG']}+{wd['DB'].replace('{MD}', str(skirm.temp_md))}"

                case "BG" | "SG" | "AR":
                    eq = f"{self.ammo[wd['AMMO']]['DMG']}+{wd['DB']}+{wd['DMG']}"

            roll_dmg_eq_label.config(text=eq)

        def next_turn():
            for c in defender_entries:
                defender_entries[c].place_forget()
            for c in defender_labels:
                defender_labels[c].place_forget()
            print("next turn")
            skirm.turn += 1

            defender_name.config(text="")
            update_everything(change=True)
            stuff = skirm.calc_turn(skirm.cur_combatant, defender_name.cget("text"))
            display_info(skirm.cur_combatant, 10, 10)
            attacker_name.config(text=skirm.cur_combatant)
            hit_miss_label.config(text="")

            # Check if dead
            if skirm.combatants[skirm.cur_combatant]["secondary_skills"]["HP"] < 1:
                defender_entries["HP"].config(text=skirm.combatants[skirm.cur_combatant]["secondary_skills"]["HP"])
                items = c_listbox.get(0, END)
                i = items.index(skirm.cur_combatant)
                if skirm.combatants[skirm.cur_combatant]["team"] == "r" and c_listbox.itemcget(i, "bg") != "#fa9898":
                    xp_gain = int(skirm.combatants[skirm.cur_combatant]["xp"])
                    skirm.temp_xp += xp_gain
                    xp_label.config(text=f"XP: {skirm.temp_xp}")
                    text = hit_chance_label.cget(
                        "text") + f"\n{skirm.cur_combatant} is dead. {xp_gain} XP gained."
                    hit_chance_label.config(text=text)
                    c_listbox.itemconfig(i, bg="#fa9898")

            wd = skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]
            eq = ""
            match wd["SKILL"]:
                case "M" | "U" | "TH" | "EW":
                    eq = f"{wd['DMG']}+{wd['DB'].replace('{MD}', str(skirm.temp_md))}"

                case "BG" | "SG" | "AR":
                    eq = f"{self.ammo[wd['AMMO']]['DMG']}+{wd['DB']}+{wd['DMG']}"

            roll_dmg_eq_label.config(text=eq)

        start_btn = Button(s_frame, text="BEGIN COMBAT", command=start_combat)
        start_btn.place(x=630, y=255)
        combat_frame = Frame(s_frame, width=780, height=240, relief="sunken", borderwidth=2)
        combat_frame.grid(row=2, column=0, columnspan=3, pady=(10, 100))

        hit_chance_label = Label(combat_frame, font=info_font, justify="left")

        # Roll stuff
        def roll_to_hit(event=None):
            if roll_hit_entry.get() == "":
                die_roll = random.randint(1, 100)
                roll_hit_entry.insert(0, str(die_roll))
            else:
                die_roll = int(roll_hit_entry.get())
            weapon_skill = skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]["SKILL"]
            target = skirm.combatants[skirm.cur_combatant]["combat_skills"][weapon_skill] + skirm.hit_mod
            skirm.temp_ap -= int(skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]["AP"])
            ap_label.config(text=f"AP: {skirm.temp_ap}\nCOST: {skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]['WEAPON']]['AP']}")
            if die_roll <= target:
                print("HIT")
                hit_miss_label.config(text="HIT", fg="green")
            else:
                print("MISS")
                hit_miss_label.config(text="MISS", fg="red")

        def roll_for_dmg(event=None):
            wd = skirm.weapon_dict[skirm.combatants[skirm.cur_combatant]["WEAPON"]]
            dmg_roll = None
            eq = ""
            match wd["SKILL"]:
                case "M" | "U" | "TH" | "EW":
                    if roll_dmg_entry.get() != "":
                        dmg_roll = int(roll_dmg_entry.get())
                    else:
                        dmg_roll = tools.roll(wd["DMG"])[1]
                        roll_dmg_entry.insert(0, str(dmg_roll))
                    true_eq = f"{dmg_roll}+{wd['DB'].replace('{MD}', str(skirm.temp_md))}"
                case "SG" | "BG" | "AR":
                    if roll_dmg_entry.get() != "":
                        dmg_roll = int(roll_dmg_entry.get())
                    else:
                        dmg_roll = tools.roll(self.ammo[wd["AMMO"]]["DMG"])[1]
                        roll_dmg_entry.insert(0, str(dmg_roll))

                    true_eq = f"{dmg_roll}+{wd['DB']}+{wd['DMG']}"
            hp = skirm.combatants[defender_name.cget("text")]["secondary_skills"]["HP"]
            total_dmg = sum([tools.roll(i)[1] for i in true_eq.split("+")])

            # Resistances
            (dt, dr) = skirm.armor_dict[skirm.combatants[defender_name.cget("text")]["ARMOR"]][wd["DMG TYPE"]].split("/")
            dt = int(dt)
            dr = int(dr)/100

            n = math.floor(total_dmg * dr)
            total_dmg -= dt
            total_dmg -= n

            if total_dmg < 0:
                total_dmg = 0

            new_hp = int(hp) - total_dmg
            dead = False
            xp_gain = 0
            if new_hp < 1:
                if skirm.combatants[defender_name.cget("text")]["team"] == "r":
                    xp_gain = int(skirm.combatants[defender_name.cget("text")]["xp"])
                    skirm.temp_xp += xp_gain
                    xp_label.config(text=f"XP: {skirm.temp_xp}")
                    dead = True

            defender_entries["HP"].delete(0, END)
            defender_entries["HP"].insert(0, str(int(hp) - total_dmg))
            hit_chance_label.config(text=hit_chance_label.cget("text") +
            f"\n{skirm.cur_combatant} did {total_dmg} ({total_dmg + n + dt} - {dt} - {n}) damage to {defender_name.cget('text')} putting them at {hp -total_dmg}")
            skirm.combatants[defender_name.cget("text")]["secondary_skills"]["HP"] -= total_dmg
            if dead:
                text = hit_chance_label.cget("text") + f"\n{defender_name.cget('text')} is dead. {xp_gain} XP gained."
                hit_chance_label.config(text=text)
                items = c_listbox.get(0, END)
                i = items.index(defender_name.cget('text'))
                c_listbox.itemconfig(i, bg="#fa9898")
            print(total_dmg)

        roll_hit_label = Label(combat_frame, text="ROLL HIT:", font=info_font, justify="left")
        roll_hit_entry = Entry(combat_frame, font=info_font, width=3)
        roll_hit_enter_btn = Button(combat_frame, text="ENTER", font=info_font, command=roll_to_hit)
        hit_miss_label = Label(combat_frame, font="courier 24 bold", fg="green")
        ap_label = Label(combat_frame, font="courier 12 bold")

        roll_hit_label.place(x=5, y=150)
        roll_hit_entry.place(x=95, y=150)
        roll_hit_enter_btn.place(x=133, y=150, height=20)
        hit_miss_label.place(x=55, y=180)
        ap_label.place(x=150, y=185)
        roll_hit_entry.bind("<Return>", roll_to_hit)

        xp_label = Label(combat_frame, text=f"XP: {skirm.temp_xp}", font=info_font)

        xp_label.place(x=570, y=180)

        roll_dmg_label = Label(combat_frame, text="ROLL DMG:", font=info_font)
        roll_dmg_entry = Entry(combat_frame, font=info_font, width=3)
        roll_dmg_enter_btn = Button(combat_frame, text="ENTER", font=info_font, command=roll_for_dmg)
        roll_dmg_eq_label = Label(combat_frame, font=info_font)
        roll_dmg_entry.bind("<Return>", lambda event: roll_for_dmg(event))

        roll_dmg_label.place(x=480, y=150)
        roll_dmg_entry.place(x=570, y=150)
        roll_dmg_enter_btn.place(x=606, y=150, height=20)
        roll_dmg_eq_label.place(x=480, y=165)


    def start(self):
        self.root.title("FNT MEGA COMBAT HUB")
        self.main_menu()
        self.root.mainloop()
        print("OK")
