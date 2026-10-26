def figures():
    questions, analyst_minutes = 300, 40
    return {
        "questions": str(questions),
        "analyst_minutes": str(analyst_minutes),
        "analyst_hours": str(questions * analyst_minutes // 60),
        "tables": "900",
        "sales_rows": "4,000,000,000",
    }
