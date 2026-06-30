def calculate_threat(person_count, intrusion):

    if person_count == 0:
        return "SAFE"

    if intrusion:
        if person_count >= 2:
            return "CRITICAL"
        return "HIGH"

    if person_count == 1:
        return "LOW"

    return "MEDIUM"