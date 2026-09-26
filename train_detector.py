import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("detection_dataset_clean.csv")
print("Dataset shape:", df.shape)

X_text = df["snippet"].astype(str)
y = df["is_issue"]

# Split BEFORE vectorizing, so the vectorizer only ever "sees" the
# training text - fitting it on the full dataset first would leak
# information about the test set into the model.
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=42, stratify=y
)

# TF-IDF: turns each line of text into a vector of word-importance scores.
# max_features caps vocabulary size to keep this fast and avoid overfitting
# on extremely rare tokens (e.g. one-off variable names).
vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

model = RandomForestClassifier(
    n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\n=== Classification report ===")
print(classification_report(y_test, y_pred, target_names=["clean", "issue"]))

print("=== Confusion matrix ===")
print(confusion_matrix(y_test, y_pred))

# Which words/n-grams matter most for detecting an issue - useful for
# understanding what the model actually learned, and for sanity-checking
# it isn't just memorizing one repo's quirks.
feature_names = vectorizer.get_feature_names_out()
importances = pd.Series(model.feature_importances_, index=feature_names)
print("\n=== Top 20 most important tokens ===")
print(importances.sort_values(ascending=False).head(20))

# Save the trained model AND the vectorizer together - both are needed
# to run predictions on new, real playbook files later.
joblib.dump(model, "detector_model.joblib")
joblib.dump(vectorizer, "detector_vectorizer.joblib")
print("\nSaved trained model to detector_model.joblib")
print("Saved vectorizer to detector_vectorizer.joblib")