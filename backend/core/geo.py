# Geofencing validation for Comarapa, Santa Cruz, Bolivia

# Defined bounding box/polygon for Comarapa delivery zone
COMARAPA_POLYGON = [
    (-17.915000, -64.515000),
    (-17.895000, -64.510000),
    (-17.880000, -64.495000),
    (-17.882000, -64.475000),
    (-17.900000, -64.460000),
    (-17.920000, -64.465000),
    (-17.935000, -64.485000),
    (-17.930000, -64.505000),
    (-17.915000, -64.515000)  # Close the polygon loop
]

def point_in_polygon(lat, lng, polygon):
    """
    Ray Casting Algorithm to check if a lat/lng point is inside a polygon
    """
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0][1], polygon[0][0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n][1], polygon[i % n][0]
        if lng > min(p1x, p2x):
            if lng <= max(p1x, p2x):
                if lat <= max(p1y, p2y):
                    if p1x != p2x:
                        xints = (lng - p1x) * (p2y - p1y) / (p2x - p1x) + p1y
                    if p1y == p2y or lat <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def is_inside_comarapa(lat, lng):
    """
    Checks if a point is within Comarapa polygon delivery zone
    """
    try:
        lat_f = float(lat)
        lng_f = float(lng)
        return point_in_polygon(lat_f, lng_f, COMARAPA_POLYGON)
    except (ValueError, TypeError):
        return False
