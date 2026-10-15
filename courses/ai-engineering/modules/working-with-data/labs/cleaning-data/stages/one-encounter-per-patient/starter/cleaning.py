def first_encounters(table):
    """Each patient's first encounter, the one with the lowest encounter_id, in order of
    encounter_id."""
    raise NotImplementedError


def drop_deaths_and_hospice(table):
    """A copy of table without the encounters that ended in death or in hospice care."""
    raise NotImplementedError


def readmitted_within_30_days(table):
    """True for each encounter the patient was readmitted within 30 days of, and False for
    the rest."""
    raise NotImplementedError
