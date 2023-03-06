# Test

from GUI import *


root_path = os.path.dirname(__file__) + "\\GUI\\data\\FNT\\"
weapons = WeaponList(root_path+"weapons.csv")
a = ArmorList(root_path+"armors.csv")
h = HelmetList(root_path+"helmets.csv")
p = CombatantList(root_path+"players.csv", root_path+"enemies.csv")

print(weapons["molerat bite"].dmg)
print(a["leather jacket"].resistances)
print(h["pre-war hat"].get_r("N"))
print(p["Fukuyo Saito"].hp - 100)
print(p["Fukuyo Saito"].hp)

fukuyo = p["Fukuyo Saito"]
nate = p["Steve Sherwin"]
for i in range(10):
    fukuyo.hp -= nate.weapon.dmg
    print(fukuyo.hp)
#obj = GUI()
#obj.start()

