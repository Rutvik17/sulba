# The discharge codes the mapping describes as a death.
DEATHS = [11, 19, 20, 21]


def encounter_problems(table):
    """The encounters their patient's earlier ones contradict, in order of encounter_id: after
    the patient's death, in a younger age group than the encounter before, or of another
    gender than it. A DataFrame of encounter_id, patient_nbr and problem."""
    raise NotImplementedError
