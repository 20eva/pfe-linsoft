import pandas as pd
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("detection_dataset_clean.csv")
print("Dataset shape:", df.shape)

X_text = df["snippet"].astype(str)
y = df["is_issue"]
groups = df["repository"]

# Group split by repository - the honest evaluation method, confirmed
# in our comparison to better reflect real-world generalization.
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X_text, y, groups=groups))

X_train_text, X_test_text = X_text.iloc[train_idx], X_text.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

train_repos = set(groups.iloc[train_idx])
test_repos = set(groups.iloc[test_idx])
print(f"\nRepos in train: {len(train_repos)} | in test: {len(test_repos)}")
print(f"Repos present in BOTH (must be 0): {len(train_repos & test_repos)}")

vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\n=== Classification report (FINAL MODEL: Logistic Regression, group split) ===")
print(classification_report(y_test, y_pred, target_names=["clean", "issue"]))

print("=== Confusion matrix ===")
print(confusion_matrix(y_test, y_pred))

# Logistic Regression coefficients: positive = pushes toward "issue",
# negative = pushes toward "clean". More directly interpretable than
# Random Forest's feature importances (which only show magnitude, not
# direction).
feature_names = vectorizer.get_feature_names_out()
coefficients = pd.Series(model.coef_[0], index=feature_names)

print("\n=== Top 20 words pushing toward 'issue' ===")
print(coefficients.sort_values(ascending=False).head(20))

print("\n=== Top 20 words pushing toward 'clean' ===")
print(coefficients.sort_values(ascending=True).head(20))

# Saved under the SAME filenames scan_playbook.py already expects,
# so the scanning tool works without any changes.
joblib.dump(model, "detector_model.joblib")
joblib.dump(vectorizer, "detector_vectorizer.joblib")
print("\nSaved final model to detector_model.joblib")
print("Saved vectorizer to detector_vectorizer.joblib")
