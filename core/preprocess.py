import pandas as pd

FILE_PATH = "data/AE-M-R.xlsx"

def load_subject_data():

    df = pd.read_excel(FILE_PATH, sheet_name="AE-sem1&2")

    # HARD CLEAN column headers
    df.columns = df.columns.str.strip()

    # REQUIRED COLUMNS
    df = df[[
        "Department",
        "Register Number",
        "Student Name",
        "Sem No",
        "Course Code",
        "Course Name",
        "Internal Mark",
        "External Mark",
        "Internal-External Gap",
        "gp",
        "Credit Points",
        "Result_Binary"
    ]]

    df = df.dropna()

    return df
