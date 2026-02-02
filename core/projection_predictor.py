import joblib
import pandas as pd

# ---------------- LOAD MODELS ----------------

internal_model = joblib.load("models/internal_model.pkl")
external_model = joblib.load("models/external_model.pkl")
gp_model = joblib.load("models/gp_model.pkl")
result_model = joblib.load("models/result_model.pkl")

encoders = joblib.load("models/projection_encoders.pkl")


# ---------------- ENCODE FUNCTION ----------------

import numpy as np

def encode_features(df):

    for col, le in encoders.items():

        if col in df.columns:

            values = df[col].astype(str)

            known_classes = set(le.classes_)

            # Replace unseen values with UNKNOWN
            values = values.apply(
                lambda x: x if x in known_classes else "UNKNOWN"
            )

            # Inject UNKNOWN safely
            if "UNKNOWN" not in le.classes_:
                le.classes_ = np.append(le.classes_, "UNKNOWN")

            df[col] = le.transform(values)

    return df


# ---------------- MAIN PREDICT FUNCTION ----------------

def predict_new_students(new_students_df, subject_template_df):

    results = []

    for _, stu in new_students_df.iterrows():

        for _, sub in subject_template_df.iterrows():

            row = {
                "Gender": stu["Gender"],
                "Department": stu["Department"],
                "12th_Percentage": stu["12th_Percentage"],
                "Cutoff": stu["Cutoff"],
                "Board": stu["Board"],
                "Medium": stu["Medium"],
                "Parent_Education_Index": stu["Parent_Education_Index"],
                "Total_Family_Income": stu["Total_Family_Income"],
                "Admission_Year": stu["Admission_Year"],

                "Sem No": sub["Sem No"],
                "Course Code": sub["Course Code"],
                "Credit Points": sub["Credit Points"],
                "Has_External": sub["Has_External"]
            }

            results.append(row)

    X = pd.DataFrame(results)

    # Encode categorical
    X_encoded = encode_features(X.copy())

    # Predict
    internal_pred = internal_model.predict(X_encoded)
    external_pred = external_model.predict(X_encoded)
    gp_pred = gp_model.predict(X_encoded)
    result_pred = result_model.predict(X_encoded)

    # Build output table
    output = X.copy()

    output["Internal Mark"] = internal_pred.round(0)
    output["External Mark"] = external_pred.round(0)
    output["Total Mark"] = output["Internal Mark"] + output["External Mark"]
    output["Internal-External Gap"] = output["Internal Mark"] - output["External Mark"]

    output["Result_Binary"] = result_pred
    output["Result"] = output["Result_Binary"].apply(lambda x: "Pass" if x == 1 else "Fail")

    output["gp"] = gp_pred.round(2)

    return output
