import main
from pygame import Vector2 as Vec2


assert main.XInbox(Vec2(10,0),(Vec2(0,0),Vec2(20,0)))

print(main.Line(Vec2(9,9),Vec2(9,9)) == (Vec2(9,9),Vec2(9,9)))