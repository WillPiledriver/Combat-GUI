# Test

from GUI import *


root_path = os.path.dirname(__file__) + "\\GUI\\data\\FNT\\"
weapons = WeaponList(root_path+"weapons.csv")
a = ArmorList(root_path+"armors.csv")
h = HelmetList(root_path+"helmets.csv")
print(weapons["molerat bite"].dmg)
print(a["leather jacket"].resistances)
print(h["pre-war hat"].get_r("p"))
#obj = GUI()
#obj.start()

