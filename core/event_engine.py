from config import RESTRICTED_ZONE


def check_intrusion(boxes):
    """
    Check whether any detected person is inside
    the restricted zone.
    """

    zone_x1, zone_y1, zone_x2, zone_y2 = RESTRICTED_ZONE

    for box in boxes:

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        if (
            zone_x1 < center_x < zone_x2
            and
            zone_y1 < center_y < zone_y2
        ):
            return True

    return False