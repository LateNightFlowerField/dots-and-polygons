# Dots & Polygons
A polygonal version of the classic Dots &amp; Boxes paper game

**Todo:**
- Fix line creation
- Implement polygon finding algorithm
- Calculate polygon area and add score
- Polish

**Game Rules**
- Played on a grid of dots
- Players take alternating turns connecting two points with a line
- Lines must meet the following criteria
- - May pass through other lines as long as it creates a new segment
- - May **not** pass through existing polygons
- - Must connect to a true points, not the intersection of other lines
- - Must be a straight line
- When a player places a line which qualifies as a polygon(see below) that area becomes their polygon and they score points equal to it's area.

**Polygon:**
- Must be a closed shape
- No side may have three points in a straight line
- Polygon must not contain any point within its area
- Polygons may have holes or lines within

**Polygon finding algorithm plan**
1. For each new line, for each of its points finding the line with the closest angle to the right and the closest angle to the left.
2. To find these take the point in question and subtract it from the start line and all connected lines, use pygame.to_angle() to calculate the angle from the sample line, take the first element and last element. Then convert back into a line by adding the intersection creating a line and standardizing it.
3. Use the last found line to continue (left or right), stop if:  the last three points are colliniar the point only connects to 1 line, or it runs into a point already used. If the point it runs into is the start point we have a polygon.

