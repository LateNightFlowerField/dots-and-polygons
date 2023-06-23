from functools import cmp_to_key
import math
import pygame as pg
from pygame import Vector2 as Vec2
import numpy as np
from dataclasses import dataclass
from dataclasses import field
from typing import Union, List
import random
import logging
from itertools import chain, pairwise, filterfalse

DEBUG = True

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
BACKGROUND_COLOR = pg.Color("#FFFFFF")
FRAMERATE = 60
GAME_WIDTH = 5
GAME_HEIGHT = 5
DOT_SPACING = 80
DOT_RADIUS = 4
DOT_COLOR = pg.Color("#D52D00")
SNAP_RANGE_COLOR = pg.Color(pg.Vector3(200,180,180)-pg.Vector3(25))
DOT_NEAR_COLOR = pg.Color("#EF7627")
DOT_SLECTED_COLOR = pg.Color("#FF9A56")
TEMP_LINE_COLOR = pg.Color("#D162A4")
MOUSE_SNAP_DISTANCE = DOT_SPACING//2
LINE_THICKNESS = 3
LINE_COLOR = pg.Color("#B55690")

pg.mixer.init()

PLAY_MUSIC = False

SELECT_SOUND = pg.mixer.Sound("point_selected.wav")
LINE_SOUND = pg.mixer.Sound("line_added.wav")
pg.mixer.music.load("background.wav")

#https://stackoverflow.com/a/68924847 This works now after change < 0 to <= 0.
def line_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """find the intersection of line segments A=(x1,y1)/(x2,y2) and
    B=(x3,y3)/(x4,y4). Returns a point or None"""
    denom = ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    if denom==0: return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    if (px - x1) * (px - x2) <= 0 and (py - y1) * (py - y2) <= 0 \
      and (px - x3) * (px - x4) <= 0 and (py - y3) * (py - y4) <= 0:
        return Vec2(px,py)
    else:
        return None

@dataclass
class Game():
    screen: object
    clock: object
    running: bool
    game_dots: list
    mouse_cords: object = None
    lines: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    selected_point: object = None
    frames: int = 0

# class Line():
#     def __init__(self,p1,p2) -> None:
#         self.p1 = p1
#         self.p2 = p2
#     def __eq__(self, __value: object) -> bool:
#         if type(__value) == Line:
#             if self.p1 == __value.p1:
#                 if self.p2 == __value.p2:
#                     return True
#                 else:
#                     return False
#             elif self.p1 == __value.p2:
#                 if self.p2 == __value.p1:
#                     return True
#                 else:
#                     return False
#             else:
#                 return False

def init():
    logging.basicConfig(level=logging.DEBUG, format=f"%(levelname)s: %(message)s")
    pg.init()
    pg.font.init()
    screen = pg.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pg.time.Clock()
    running = True
    game_dots = list()
    x_padding = (SCREEN_WIDTH-((GAME_WIDTH-1)*DOT_SPACING))//2
    y_padding = (SCREEN_HEIGHT-((GAME_HEIGHT-1)*DOT_SPACING))//2
    for x in range(GAME_WIDTH):
        for y in range(GAME_HEIGHT):
            game_dots.append(Vec2(x*DOT_SPACING+x_padding,y*DOT_SPACING+y_padding))
    return Game(screen, clock, running, game_dots)

def EventHandeler():
    for event in pg.event.get(): #Handle Inputs
        if event.type == pg.QUIT:
            game.running = False
        if event.type == pg.MOUSEBUTTONDOWN:
            left, middle, right = pg.mouse.get_pressed()
            if left and game.selected_point:
                game.flags.append("line")
            elif left:
                game.flags.append("point")
        if event.type == pg.MOUSEBUTTONUP:
            if game.selected_point and game.selected_point.distance_to(game.mouse_cords) > MOUSE_SNAP_DISTANCE:
                game.flags.append("line")
        if event.type == pg.KEYDOWN:
            for line in game.lines:
                print(f"{line}, {line[0].x!r}, {line[0].y!r}, {line[1].x!r}, {line[1].y!r}")

def RenderNearCircle():
    for point in game.game_dots:
        if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
            pg.draw.circle(game.screen,SNAP_RANGE_COLOR,point,MOUSE_SNAP_DISTANCE)

def RenderLines():
    if game.selected_point: # Temporary Line
        for point in game.game_dots:
            if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                pg.draw.aaline(game.screen,TEMP_LINE_COLOR,game.selected_point,point,LINE_THICKNESS)
                break
        else:
            pg.draw.aaline(game.screen,TEMP_LINE_COLOR,game.selected_point,game.mouse_cords,LINE_THICKNESS)

    for line in game.lines:
        color_local = LINE_COLOR
        if DEBUG:
            random.seed(id(line))
            color_local = pg.Color(pg.Vector3(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        pg.draw.aaline(game.screen,color_local, *line, LINE_THICKNESS)
    
def RenderPoints():
    for point in game.game_dots:
        snap = point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE
        if point == game.selected_point:
            pg.draw.circle(game.screen,DOT_SLECTED_COLOR,point,DOT_RADIUS)
            continue
        elif snap:
            pg.draw.circle(game.screen,DOT_NEAR_COLOR,point,DOT_RADIUS)
            continue
        pg.draw.circle(game.screen,DOT_COLOR,point,DOT_RADIUS)

def AddPolygon():
    operating_lines = DivideLines(game.lines)
    print(operating_lines)

def AddPoint():
    if game.selected_point:
        return False
    for point in game.game_dots:
        if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
            game.selected_point = point
            return True
    return False

def AddLine():
    point1, point2 = game.selected_point, None
    for point in game.game_dots:
        if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
            point2 = point
            break
    else:
        return False
    if point1 == point2:
        return False
    new_lines = [(point1,point2)]
    if new_lines[0] in game.lines or (point2,point1) in game.lines:
        return False
    new_lines = SubtractExistingSegments(new_lines)
    # new_lines = DivideLines(new_lines)
    if len(new_lines) == 0:
        return False
    game.lines.extend(new_lines)
    return True

def DivideLines(lines):
    new_lines = []
    lines_to_be_removed = []
    for nline in lines:
        intersections = [*nline]
        for line in game.lines:
            if res := line_intersection(nline[0].x,nline[0].y,nline[1].x,nline[1].y,line[0].x,line[0].y,line[1].x,line[1].y):
                intersections.append(res)
                lines_to_be_removed.append(line)
                new_lines.append((res,line[0]))
                new_lines.append((res,line[1]))
        intersections.sort(key=lambda l: l.distance_to(nline[0]))
        intersections = unique(intersections)
        new_lines.extend(list(zip(intersections,intersections[1:])))
    for line in lines_to_be_removed:
        game.lines.remove(line)
    new_lines = list(filter(lambda k: k[0] != k[1], new_lines))
    new_lines = list(filter(lambda k: k not in game.lines, new_lines))
    new_lines = list(filter(lambda k: (k[1],k[0]) not in game.lines, new_lines))
    return new_lines

def SubtractExistingSegments(lines):
    logging.debug("Start of new line code")
    addedsegment = lines[0]
    adjustedline = (Vec2(0.0,0.0), addedsegment[1] - addedsegment[0])
    linesinline = []
    for line in game.lines:
        checkline = (Vec2(0.0,0.0),line[1] - line[0])
        if adjustedline[1].normalize() in [checkline[1].normalize(),(checkline[1]*-1).normalize()]:
            if (addedsegment[1]-line[1]) == Vec2(0.0,0.0):
                linesinline.append(line)
            elif (addedsegment[1]-line[1]).normalize() in [checkline[1].normalize(),(checkline[1]*-1).normalize()]:
                linesinline.append(line)
    if not linesinline:
        return lines 
    vectorlist = list(chain.from_iterable(linesinline))
    vectorlist.extend(addedsegment)
    vectorlist = sorted(vectorlist,key=lambda l: l.distance_to(vectorlist[-1]))
    vectorlist = sorted(vectorlist,key=lambda l: l.distance_to(vectorlist[-1]))
    vectorlist = unique(vectorlist)
    logging.debug(f"Ordered vectors {vectorlist}")
    futurelines = []
    for zed in vectorlist:
        if Inbox(zed,addedsegment):
            for box in linesinline:
                if XInbox(zed,box):
                    break
            else:
                futurelines.append(zed)
        else:
            logging.debug(f"Zed was a {type(zed)}")
    logging.debug(f"After checking box {futurelines}")
    possiblelines = list(zip(futurelines[::2],futurelines[1::2]))
    futurelines.reverse()
    possiblelines.extend(list(zip(futurelines[::2],futurelines[1::2])))
    logging.debug(f"Lines before removal {possiblelines}")
    possiblelines = filterfalse(lambda l: l[0] == l[1], possiblelines)
    possiblelines= filterfalse(lambda l: l in game.lines, possiblelines)
    possiblelines = filterfalse(lambda l: (l[1],l[0]) in game.lines, possiblelines)
    newlines = []
    for line in possiblelines:
        if line in newlines:
            continue
        if (line[1],line[0]) in newlines:
            continue
        newlines.append(line)
    logging.debug(f"Lines to be added {newlines}")
    return newlines

def Inbox(point,box):
    logging.debug(f"Inbox: {point!r} | {box}")
    if not min(box[0].x,box[1].x) <= point.x <= max(box[0].x,box[1].x):
        logging.debug(f"""
          Inbox returns false due to x-axis miss:
            - {box[0].x = !r}
            - {box[1].x = !r}
            - {point.x = !r}
            - {box[0].x = !r}
            - {box[1].x = !r}
        """)
        return False
    if not min(box[0].y,box[1].y) <= point.y <= max(box[0].y,box[1].y):
        logging.debug(f"""
          Inbox returns false due to y-axis miss:
            - {box[0].y = !r}
            - {box[1].y = !r}
            - {point.y = !r}
            - {box[0].y = !r}
            - {box[1].y = !r}
        """)
        return False    
    logging.debug("True")
    return True

def XInbox(point,box):
    logging.debug(f"XInbox: {point} | {box}")
    if not point.x == box[0].x == box[1].x:
        if not min(box[0].x,box[1].x) < point.x < max(box[0].x,box[1].x):
            logging.debug("False")
            return False
    if not point.y == box[0].y == box[1].y:
        if not min(box[0].y,box[1].y) < point.y < max(box[0].y,box[1].y):
            logging.debug("False")
            return False
    logging.debug("True")
    return True

def OnScreenDebugger():
    font = pg.font.Font(None, 64)
    text = font.render(str(game.mouse_cords), True, (10, 10, 10))
    game.screen.blit(text, (0,0))
    text = font.render(str(round(game.clock.get_fps())), True, (5, 5, 5))
    game.screen.blit(text, (0,40))
    text = font.render(str(len(game.lines)), True, (5, 5, 5))
    game.screen.blit(text, (0,80))

def unique(input_list):
    """Returns the unique elements of a list"""
    empty_list = []
    for item in input_list:
        if item not in empty_list:
            empty_list.append(item)
    return empty_list

if __name__ == "__main__":
    game = init()
    if PLAY_MUSIC:
        pg.mixer.music.play(-1)
    while game.running:
        game.screen.fill(BACKGROUND_COLOR)
        game.mouse_cords = pg.mouse.get_pos()
        
        EventHandeler()
        RenderNearCircle()
        RenderLines()
        RenderPoints()
        for flag in game.flags:
            match flag:
                case "point":
                    if AddPoint():
                        SELECT_SOUND.play()
                        if DEBUG:
                            logging.debug(f"Added Point at {game.selected_point}")
                case "line":
                    if AddLine():
                        if DEBUG:
                            logging.info("Added Line(s)")
                        LINE_SOUND.play()
                    game.selected_point = None
                case "polygon":
                    AddPolygon()
                case _:
                    pass
        if DEBUG:
            OnScreenDebugger()

        game.flags = []

        pg.display.update()
        game.clock.tick(FRAMERATE)
        game.frames += 1
    pg.quit()