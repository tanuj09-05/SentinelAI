from config import RESTRICTED_ZONE


def _get_box_center(box):
    """
    Purpose:
    Kissi bhi bounding box ka exact center point nikalna.
    """
    x1, y1, x2, y2 = map(int, box)

    # Math ka simple mid-point formula: (start + end) / 2
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    return center_x, center_y


def _is_inside_zone(center_x, center_y):
    """
    Purpose:
    Check krna ki kya diye gaye coordinates humare restricted area ke andar aate hain.
    """
    # Zone ke chaaro kone (corners) config file se laa rhe hain
    zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE

    # Check kr rhe hain ki X (left-right) aur Y (up-down) coordinates zone ke andar hain ya nhi
    is_x_inside = zone_x1 < center_x < zone_x2
    is_y_inside = zone_y1 < center_y < zone_y2

    return is_x_inside and is_y_inside


def check_intrusion(bounding_boxes, track_ids):
    """
    Purpose:
    Camera me dikh rahe sabhi logon ko check krna ki kya unme se koi restricted zone me ghusa hai.

    Parameters:
    bounding_boxes -> Camera me pakde gaye logon ke boxes ki list.
    track_ids      -> Un logon ki unique tracking IDs.

    Returns:
    Un sabhi logon ki IDs ki list jo zone me pakde gaye hain.
    """
    intruder_ids = []

    # Har ek person ka box aur uski ID ek sath zip karke loop chala rhe hain
    for box, track_id in zip(bounding_boxes, track_ids):

        # 1. Pehle person ke box ka center point nikalenge
        center_x, center_y = _get_box_center(box)

        # 2. Phir check karenge ki kya wo point restricted zone me aata hai
        if _is_inside_zone(center_x, center_y):
            # Agar haan, toh uski ID ko intruders ki list me daal denge
            intruder_ids.append(track_id)

    # Finally saare pakde gaye logon ki list return kr denge
    return intruder_ids
