import main
from pygame import Vector2 as Vec2
from main import Inbox

# print(main.Line(Vec2(9,9),Vec2(9,9)) == (Vec2(9,9),Vec2(9,9)))

# DEBUG: Inbox: [90, 170] | (<Vector2(90, 170)>, <Vector2(90, 90)>)
# DEBUG: False
print(Inbox(Vec2(90,170),(Vec2(90,170),Vec2(90,90))))

print(Inbox(Vec2(250,170),(Vec2(250,170),Vec2(250,90))))