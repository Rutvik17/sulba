from office_records import AWARDS, STUDENTS


def figures():
    return {"students": str(len(STUDENTS)), "awards": str(len(AWARDS))}
