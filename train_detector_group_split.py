import pandas as pd
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("detection_dataset_clean.csv")
print("Dataset shape:", df.shape)

X_text = df["snippet"].astype(str)
y = df["is_issue"]

# NOUVEAU : on donne aussi les groupes (repository) au split, pour qu'un
# meme depot ne se retrouve jamais a la fois dans le train et dans le test.
groups = df["repository"]

# NOUVEAU : GroupShuffleSplit au lieu de train_test_split.
# Meme logique (80% train / 20% test), mais il decoupe par groupe entier,
# jamais ligne par ligne au hasard.
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X_text, y, groups=groups))

X_train_text, X_test_text = X_text.iloc[train_idx], X_text.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

# Preuve que ca marche : aucun depot ne doit apparaitre des deux cotes.
train_repos = set(groups.iloc[train_idx])
test_repos = set(groups.iloc[test_idx])
overlap = train_repos & test_repos
print(f"\nDepots en train: {len(train_repos)} | en test: {len(test_repos)}")
print(f"Depots presents des deux cotes (doit etre 0): {len(overlap)}")

# Le reste du code ne change pas du tout.
vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

model = RandomForestClassifier(
    n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\n=== Classification report (split PAR REPOSITORY) ===")
print(classification_report(y_test, y_pred, target_names=["clean", "issue"]))

print("=== Confusion matrix ===")
print(confusion_matrix(y_test, y_pred))

feature_names = vectorizer.get_feature_names_out()
importances = pd.Series(model.feature_importances_, index=feature_names)
print("\n=== Top 20 most important tokens ===")
print(importances.sort_values(ascending=False).head(20))

joblib.dump(model, "detector_model_group_split.joblib")
joblib.dump(vectorizer, "detector_vectorizer_group_split.joblib")
print("\nSaved trained model to detector_model_group_split.joblib")
print("Saved vectorizer to detector_vectorizer_group_split.joblib")
