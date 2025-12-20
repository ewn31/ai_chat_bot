"""Module for selecting counsellors based on different algorithms."""

import counsellors

def round_robin():
    """
    Round Robin selection algorithm for assigning counsellors.
    Fetches fresh counsellor list on each call to ensure data is up-to-date.
    """
    counsellor_list = counsellors.list_counsellors()
    
    if not counsellor_list:
        return None

    # Static variable to keep track of the last assigned counsellor index
    if not hasattr(round_robin, "last_index"):
        round_robin.last_index = -1

    # Calculate the next index in a round-robin fashion
    round_robin.last_index = (round_robin.last_index + 1) % len(counsellor_list)
    print('Counsellor list:', counsellor_list)
    print('Selected counsellor index:', round_robin.last_index)
    return counsellor_list[round_robin.last_index]
