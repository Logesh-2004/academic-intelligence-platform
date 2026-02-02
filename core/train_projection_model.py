import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import joblib
import os

print("Loading datasets...")

admission = pd.read_excel("data/AE-STU-DETAILS.xlsx")
academic = pd.read_excel("data/AE-sem1&2.xlsx")

admission.columns = admission.columns.str.strip()
academic.columns = academic.columns.str.strip()

# Rename for merge
admission.rename(columns={
    "Register_No (Primary Key)": "Register Number"
}, inplace=True)

# Merge datasets
df = pd.merge(admission, academic, on="Register Number", how="inner")
df.columns = df.columns.str.strip()

if "Department_x" in df.columns:
    df.rename(columns={"Department_x": "Department"}, inplace=True)

if "Department_y" in df.columns:
    df.drop(columns=["Department_y"], inplace=True)

print("Merged rows:", len(df))
print(df.columns.tolist())

df = df.dropna()

# ----------------- Feature Encoding -----------------

cat_cols = ["Gender",
            "Department", 
            "Board", 
            "Medium", 
            "Course Code",
            "Admission_Year"
        ]

encoders = {}

for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

# ----------------- Features -----------------

X = df[[
    "Gender",
    "Department",
    "12th_Percentage",
    "Cutoff",
    "Board",
    "Medium",
    "Parent_Education_Index",
    "Total_Family_Income",
    "Admission_Year",
    "Sem No",
    "Course Code",
    "Credit Points",
    "Has_External"
]]
df = df.dropna()

print(X.dtypes)

y_internal = df["Internal Mark"]
y_external = df["External Mark"]
y_gp = df["gp"]
y_result = df["Result_Binary"]

# ----------------- Train Models -----------------

print("Training models...")

internal_model = RandomForestRegressor(n_estimators=200, random_state=42)
external_model = RandomForestRegressor(n_estimators=200, random_state=42)
gp_model = RandomForestRegressor(n_estimators=200, random_state=42)

result_model = RandomForestClassifier(n_estimators=200, random_state=42)

internal_model.fit(X, y_internal)
external_model.fit(X, y_external)
gp_model.fit(X, y_gp)

result_model.fit(X, y_result)

# ----------------- Save -----------------

os.makedirs("models", exist_ok=True)

joblib.dump(internal_model, "models/internal_model.pkl")
joblib.dump(external_model, "models/external_model.pkl")
joblib.dump(gp_model, "models/gp_model.pkl")
joblib.dump(result_model, "models/result_model.pkl")
joblib.dump(encoders, "models/projection_encoders.pkl")

print("Projection models saved successfully")

# Save subject template (unique subjects per sem)

subject_template = df[[
    "Sem No",
    "Course Code",
    "Course Name",
    "Credit Points",
    "Has_External"
]].drop_duplicates()

subject_template.to_csv("models/subject_template.csv", index=False)
