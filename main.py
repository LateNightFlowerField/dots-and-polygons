from functools import cmp_to_key
import math
import pygame as pg
from pygame import Vector2 as Vec2
import numpy as np
from dataclasses import dataclass
from dataclasses import field
from typing import Union, List
import random

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
BACKGROUND_COLOR = pg.Color(200,180,200)
FRAMERATE = 60
GAME_WIDTH = 5
GAME_HEIGHT = 5
DOT_SPACING = 80
DOT_RADIUS = 4
DOT_COLOR = pg.Color(100,50,140,a=255)
SNAP_RANGE_COLOR = pg.Color(pg.Vector3(200,180,180)-pg.Vector3(25))
DOT_NEAR_COLOR = pg.Color(230,90,180)
DOT_SLECTED_COLOR = pg.Color(230,200,180)
TEMP_LINE_COLOR = pg.Color(60,10,30)
MOUSE_SNAP_DISTANCE = DOT_SPACING//2
LINE_THICKNESS = 3
LINE_COLOR = pg.Color(10,60,80)

pg.mixer.init()

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


"""
For each new point formed go out to each connected line making only right turns and only left turns. 
If you have three points in a row which fall on a line abort. If you reach your starting point you have a polygon. Testing git
"""
def find_closest_vector(sample_vector,vectors,clockwise):
    vectors.sort(key=lambda c: sample_vector.angle_to(c))
    return vectors #TEMP
    if clockwise:
        return vectors[0]
    if not clockwise:
        return vectors[-1]
def subtract_center(center_vector,vector_pairs):
    return [(vector1-center_vector,vector2-center_vector) for vector1, vector2 in vector_pairs]

@dataclass
class Game():
    screen: object
    line_layer: object
    dot_layer: object
    clock: object
    running: bool
    check_polygon: bool
    game_dots: list
    new_lines: list = field(default_factory=list)
    mouse_cords: object = None
    new_intersections: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    checking_lines: list = field(default_factory=list)
    last_line: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    add_point: bool = False
    add_line: bool = False
    draw_temp_line: bool = False
    selected_point: object = None

def init():
    pg.init()
    pg.font.init()
    screen = pg.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    dots_layer = pg.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    line_layer = pg.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pg.time.Clock()
    running = True
    check_polygon = False
    game_dots = list()
    x_padding = (SCREEN_WIDTH-((GAME_WIDTH-1)*DOT_SPACING))//2
    y_padding = (SCREEN_HEIGHT-((GAME_HEIGHT-1)*DOT_SPACING))//2
    for x in range(GAME_WIDTH):
        for y in range(GAME_HEIGHT):
            game_dots.append(Vec2(x*DOT_SPACING+x_padding,y*DOT_SPACING+y_padding))
    return Game(screen, dots_layer, line_layer, clock, running, check_polygon, game_dots)

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

def RenderNearCircle():
    for point in game.game_dots:
        if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
            pg.draw.circle(game.screen,SNAP_RANGE_COLOR,point,MOUSE_SNAP_DISTANCE)

def RenderLines():
    if game.selected_point: # Temporary Line
        for point in game.game_dots:
            if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                pg.draw.line(game.screen,TEMP_LINE_COLOR,game.selected_point,point,LINE_THICKNESS)
                break
        else:
            pg.draw.line(game.screen,TEMP_LINE_COLOR,game.selected_point,game.mouse_cords,LINE_THICKNESS)

    for line in game.lines:
        # random.seed(line[0].magnitude()-line[1].x*line[1])
        # color_local = pg.Color(pg.Vector3(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        pg.draw.line(game.screen,LINE_COLOR, *line, LINE_THICKNESS)
    
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
    # new_lines, updated_game_lines = DivideLines(new_lines)
    game.lines.extend(new_lines)
    return True

def SubtractExistingSegments(lines):
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
    print(linesinline)
    for line in linesinline:
        if line in game.lines:
            game.lines.remove(line)

    #Order points, from point in bbx new line and no other bbox to next point that is the same.

    return lines

def OnScreenDebugger():
    font = pg.font.Font(None, 64)
    text = font.render(str(game.mouse_cords), True, (10, 10, 10))
    game.screen.blit(text, (0,0))
    text = font.render(str(round(game.clock.get_fps())), True, (5, 5, 5))
    game.screen.blit(text, (0,40))


def sort_points_by_distance(point_1):
    return lambda point_2: np.sqrt((point_1.x-point_2.x)**2+(point_1.y-point_2.y)**2)

def closet_point_to_corner(points):
    print(points)
    gamecorners = [Vec2(0,0),Vec2(0,SCREEN_HEIGHT),Vec2(SCREEN_WIDTH,0),Vec2(SCREEN_WIDTH,SCREEN_HEIGHT)]
    smallest_point = None
    smallest_point_distance = -1
    for point in points:
        distance_to_closet_corner = min([p.distance_to(point) for p in gamecorners])
        print("ffd")
        if distance_to_closet_corner < smallest_point_distance or smallest_point_distance == -1:
            smallest_point = point
            smallest_point_distance = distance_to_closet_corner
    return smallest_point
    # return smallest_point
    

def unique(input_list):
    """Returns the unique elements of a list"""
    empty_list = []
    for item in input_list:
        if item not in empty_list:
            empty_list.append(item)
    return empty_list

def check_valid_line(game, point):
    if (point, game.selected_point) in game.lines or (game.selected_point,point) in game.lines:
        return False
    return True

def has_point(point):
    """Function to be used by filter() to easly check if a line contains a point"""
    return lambda k: point in k

def standerdize_line(line):
    """Sorts line so the points are always in order of distance from (0,0) or the top left"""
    point_1, point_2 = line
    if sum(point_1) < sum(point_2):
        return (point_1,point_2)
    else:
        return (point_2,point_1)

def sortlines(point):
    return lambda line: max([(point.distance_to(line[0]),point.distance_to(line[0]))])*(line[0]-point+line[0]-point).normalize()

def float_between(number, bound1, bound2):
    if bound2 < bound1:
        bound1, bound2 = bound2, bound1
    return number == np.clip(number,bound1,bound2) 


def point_in_bbox(point, bbox):
    if not float_between(point.x,bbox[0].x,bbox[1].x):
        return False
    if not float_between(point.y,bbox[0].y,bbox[1].y):
        return False
    else:
        return True

if __name__ == "__main__":
    game = init()
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
                case "line":
                    if AddLine():
                        SELECT_SOUND.play()
                        LINE_SOUND.play()
                    game.selected_point = None
                case "polygon":
                    pass
                case _:
                    pass
            
        OnScreenDebugger()

        game.flags = []

        pg.display.update()
        game.clock.tick(FRAMERATE)
    pg.quit()