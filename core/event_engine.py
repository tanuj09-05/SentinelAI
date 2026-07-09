from config import RESTRICTED_ZONE

def _get_box_center(box):
    x1, y1, x2, y2 = map(int, box)
    return (x1 + x2) // 2, (y1 + y2) // 2

def _is_inside_zone(center_x, center_y):
    zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE
    return (zone_x1 < center_x < zone_x2) and (zone_y1 < center_y < zone_y2)

def check_intrusion(bounding_boxes, track_ids):
    intruder_ids = []
    
    for box, track_id in zip(bounding_boxes, track_ids):
        center_x, center_y = _get_box_center(box)
        
        if _is_inside_zone(center_x, center_y):
            intruder_ids.append(track_id)
            
    return intruder_ids
