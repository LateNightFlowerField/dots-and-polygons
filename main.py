from functools import cmp_to_key
import pygame
import numpy as np
from dataclasses import dataclass
from dataclasses import field
from typing import Union, List
import random

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
BACKGROUND_COLOR = pygame.Color(80,80,80)
FRAMERATE = 60
GAME_WIDTH = 5
GAME_HEIGHT = 5
DOT_SPACING = 80
DOT_RADIUS = 4
DOT_COLOR = pygame.Color(90,20,60,a=255)
SNAP_RANGE_COLOR = pygame.Color(70,70,70,a=80)
DOT_NEAR_COLOR = pygame.Color(230,90,180)
DOT_SLECTED_COLOR = pygame.Color(230,200,180)
TEMP_LINE_COLOR = pygame.Color(60,10,30)
MOUSE_SNAP_DISTANCE = DOT_SPACING//2
LINE_THICKNESS = 3
LINE_COLOR = pygame.Color(160,100,130)


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
        return pygame.Vector2(px,py)
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
    add_point: bool = False
    add_line: bool = False
    draw_temp_line: bool = False
    selected_point: object = None

def init():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    dots_layer = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    line_layer = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    running = True
    check_polygon = False
    game_dots = list()
    x_padding = (SCREEN_WIDTH-((GAME_WIDTH-1)*DOT_SPACING))//2
    y_padding = (SCREEN_HEIGHT-((GAME_HEIGHT-1)*DOT_SPACING))//2
    for x in range(GAME_WIDTH):
        for y in range(GAME_HEIGHT):
            game_dots.append(pygame.Vector2(x*DOT_SPACING+x_padding,y*DOT_SPACING+y_padding))
    return Game(screen, dots_layer, line_layer, clock, running, check_polygon, game_dots)

def sort_points_by_distance(point_1):
    return lambda point_2: np.sqrt((point_1.x-point_2.x)**2+(point_1.y-point_2.y)**2)

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

if __name__ == "__main__":
    game = init()
    while game.running:

        game.mouse_cords = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.selected_point:
                    game.add_line = True
                    print("Set Add Line Flag")
                else:
                    game.add_point = True
                    print("Set Add Point Flag")
        
        game.screen.fill(BACKGROUND_COLOR)
        game.draw_temp_line = True

        for point in game.game_dots: #TODO seperate into functions
            if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                pygame.draw.circle(game.screen,SNAP_RANGE_COLOR,point,MOUSE_SNAP_DISTANCE)
            if game.add_point:
                if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                    game.selected_point = point
                    print("Selected Point")
            if game.add_line:
                if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE and point != game.selected_point:
                    if check_valid_line(game, point):
                        intersections = [point,game.selected_point]
                        temp_lines = game.lines.copy()
                        for line in game.lines:
                            if res := line_intersection(*point,*game.selected_point,*line[0],*line[1]):
                                intersections.append(res)
                                temp_lines.extend(zip([line[0],res],[res,line[1]]))
                                temp_lines.remove(line)
                        temp_lines = unique(temp_lines)
                        zt = []
                        for u in temp_lines:
                            if (u not in zt) and ((u[1],u[0]) not in zt) and (u[0] != u[1]):
                                zt.append(u)
                        temp_lines = zt
                        print(temp_lines)
                        # input()
                        intersections = unique(intersections)
                        intersections.sort(key=sort_points_by_distance(game.selected_point))
                        game.last_line = tuple(intersections[0:2])
                        game.new_lines = list(zip(intersections,intersections[1:]))
                        if not all(map(lambda nl: nl in temp_lines,game.new_lines)):
                            game.lines = unique(temp_lines)
                            game.lines.extend(game.new_lines)
                            print("Added line")
                            game.check_polygon = True
                            game.new_intersections = intersections
                        
                    game.selected_point = None
            if game.selected_point:
                if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                    pygame.draw.line(game.screen,TEMP_LINE_COLOR,game.selected_point,point,LINE_THICKNESS)
                    game.draw_temp_line = False

        if game.selected_point and game.draw_temp_line:
            pygame.draw.line(game.screen,TEMP_LINE_COLOR,game.selected_point,game.mouse_cords,LINE_THICKNESS)

        for start_line, end_line in game.lines:
            TEMP_LINE_COLOR = LINE_COLOR
            print(standerdize_line((start_line,end_line)))
            random.seed(start_line.x*start_line.y*end_line.x*end_line.y)
            TEMP_LINE_COLOR = pygame.Color(random.randint(1,255),random.randint(1,255),random.randint(1,255))
            pygame.draw.line(game.screen, TEMP_LINE_COLOR, start_line, end_line,LINE_THICKNESS)
        
        if game.check_polygon:
            intersections_to_check_from = []
            for intersection in game.new_intersections:
                if len(list(filter(has_point(intersection),game.lines))) > 1:
                    intersections_to_check_from.append(intersection)
            for intersection in intersections_to_check_from:
                connected_lines = list(filter(has_point(intersection),game.lines))
                centered_vectors = subtract_center(intersection,connected_lines)
                centered_vectors = list(map(list, centered_vectors))
                temp_vectors = []
                for elm in centered_vectors:
                    for belm in elm:
                        if belm != pygame.Vector2(0,0):
                            temp_vectors.append(belm)
                centered_vectors = temp_vectors
                for line in list(filter(has_point(intersection),game.new_lines)):
                    line = list(line)
                    line.remove(intersection)
                    # print(line[0]-intersection)
                    # print(find_closest_vector(line[0],centered_vectors, False))
            # print(intersections_to_check_from)
            # for cross in game.new_intersections[1:-1]:
            #     for line in filter(has_point(cross),game.new_lines):
            #         ways_to_check.append(line[::-1] if line in ways_to_check else line)
            # for way in ways_to_check:
            #     connected_lines = list(filter(has_point(way[0]),game.lines))
            #     connected_lines = [line for line in connected_lines if line != way and line != (way[1],way[0])]

            #     game.checking_lines = connected_lines
            #     print(way,list(map(lambda h: [u for u in h if u != way[0]],connected_lines)))

            game.check_polygon = False
        for point in game.game_dots:
            CURRENT_DOT_COLOR = DOT_COLOR
            if point.distance_to(game.mouse_cords) < MOUSE_SNAP_DISTANCE:
                CURRENT_DOT_COLOR = DOT_NEAR_COLOR
            if game.selected_point:
                if game.selected_point == point:
                    CURRENT_DOT_COLOR = DOT_SLECTED_COLOR
            pygame.draw.circle(game.screen,CURRENT_DOT_COLOR,point,DOT_RADIUS)
        
        for intersection_point in game.new_intersections:
            pygame.draw.circle(game.screen,'yellow',intersection_point,DOT_RADIUS)

        for start_line, end_line in game.checking_lines:
            pygame.draw.line(game.screen, 'white', start_line, end_line,LINE_THICKNESS)

        if game.add_line:
            game.selected_point = False
        game.add_line = False
        game.add_point = False

        font = pygame.font.Font(None, 64)
        text = font.render(str(game.mouse_cords), True, (10, 10, 10))
        game.screen.blit(text, (0,0))
        text = font.render(str(round(game.clock.get_fps())), True, (5, 5, 5))
        game.screen.blit(text, (0,40))
        # print(len(game.lines))
        pygame.display.update()
        game.clock.tick(FRAMERATE)
        # print(game.clock.get_fps())
    pygame.quit()