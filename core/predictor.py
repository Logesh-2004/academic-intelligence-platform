import joblib
import pandas as pd

MODEL_PATH = "models/subject_model.pkl"
ENCODER_PATH = "models/course_encoder.pkl"

model = joblib.load(MODEL_PATH)
encoder = joblib.load(ENCODER_PATH)

def predict_subject(sem, course_code, internal, gap, credit):

    # Safety check
    if course_code not in encoder.classes_:
        return None, None

    course_encoded = encoder.transform([course_code])[0]

    data = pd.DataFrame([[
        sem,
        course_encoded,
        internal,
        gap,
        credit
    ]], columns=[
        "Sem No",
        "Course_Code_Enc",
        "Internal Mark",
        "Internal-External Gap",
        "Credit Points"
    ])

    prob = model.predict_proba(data)[0][1]
    pred = model.predict(data)[0]

    return pred, prob
