"""The dashboard's monthly report of readmissions, by admission source, in SQL."""

import pandas as pd

REPORT = """
WITH firsts AS (
    SELECT e.*
    FROM encounters AS e
    JOIN (
        SELECT patient_nbr, MIN(encounter_id) AS first_id
        FROM encounters
        GROUP BY patient_nbr
    ) AS f ON f.patient_nbr = e.patient_nbr AND f.first_id = e.encounter_id
),
patients AS (
    SELECT
        CASE
            WHEN s.description IS NULL
                OR s.description IN ('NULL', 'Not Available', 'Not Mapped', 'Unknown/Invalid')
            THEN 'Unknown'
            ELSE s.description
        END AS admission_source,
        p.readmitted = '<30' AS soon
    FROM firsts AS p
    LEFT JOIN codes AS s ON s.column_name = 'admission_source_id' AND s.code = p.admission_source_id
    WHERE p.discharge_disposition_id NOT IN (11, 13, 14, 19, 20, 21)
        AND NOT EXISTS (SELECT 1 FROM opted_out AS o WHERE o.patient_nbr = p.patient_nbr)
),
by_source AS (
    SELECT admission_source, COUNT(*) AS patients, SUM(soon) AS readmitted,
        AVG(soon) AS share
    FROM patients
    GROUP BY admission_source
)
SELECT * FROM (
    SELECT admission_source, patients, readmitted, share FROM by_source
    UNION ALL
    SELECT 'All sources', SUM(patients), SUM(readmitted), SUM(readmitted) * 1.0 / SUM(patients)
    FROM by_source
)
ORDER BY admission_source = 'All sources', patients DESC
"""


def report(connection):
    """Patients and those readmitted within 30 days by admission source, each patient at their
    first encounter without deaths and hospice care, and none of the patients opted out, the
    unknown sources together, then every source together."""
    return pd.read_sql_query(REPORT, connection, index_col="admission_source")
