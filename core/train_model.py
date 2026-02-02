from core.preprocess import load_subject_data
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

print("Loading Dataset...")

df = load_subject_data()

# ---------------- ENCODE COURSE CODE ----------------

encoder = LabelEncoder()
df["Course_Code_Enc"] = encoder.fit_transform(df["Course Code"])

# ---------------- FEATURES ----------------

X = df[[
    "Sem No",
    "Course_Code_Enc",
    "Internal Mark",
    "Internal-External Gap",
    "Credit Points"
]]

y = df["Result_Binary"]

# ---------------- SPLIT ----------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ---------------- TRAIN ----------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

acc = model.score(X_test, y_test)

print("Accuracy:", round(acc * 100, 2), "%")

# ---------------- SAVE ----------------

os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/subject_model.pkl")
joblib.dump(encoder, "models/course_encoder.pkl")

print("Model + Encoder Saved")
