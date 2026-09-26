import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score

df = pd.read_csv("detection_dataset_clean.csv")
print("Dataset shape:", df.shape)

X_text = df["snippet"].astype(str)
y = df["is_issue"]
groups = df["repository"]

# Group split by repository - same repo never appears in both train and test
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X_text, y, groups=groups))

X_train_text, X_test_text = X_text.iloc[train_idx], X_text.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

train_repos = set(groups.iloc[train_idx])
test_repos = set(groups.iloc[test_idx])
print(f"\nRepos in train: {len(train_repos)} | in test: {len(test_repos)}")
print(f"Repos present in BOTH (must be 0): {len(train_repos & test_repos)}")

# Same TF-IDF features for every model, fit on training text only
vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1
    ),
    "Logistic Regression": LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=42
    ),
    "Multinomial Naive Bayes": MultinomialNB(),
    "Linear SVM": LinearSVC(
        class_weight="balanced", random_state=42, max_iter=5000
    ),
}

for name, model in models.items():
    print(f"\n{'=' * 60}")
    print(f"Training: {name}  (GROUP SPLIT by repository)")
    print("=" * 60)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["clean", "issue"]))

summary = []
for name, model in models.items():
    y_pred = model.predict(X_test)
    summary.append({
        "Model": name,
        "Accuracy": round(accuracy_score(y_test, y_pred), 3),
        "Issue Precision": round(precision_score(y_test, y_pred, pos_label=1), 3),
        "Issue Recall": round(recall_score(y_test, y_pred, pos_label=1), 3),
        "Issue F1": round(f1_score(y_test, y_pred, pos_label=1), 3),
    })

summary_df = pd.DataFrame(summary).sort_values("Issue F1", ascending=False)
print("\n" + "=" * 60)
print("SUMMARY (GROUP SPLIT) - sorted by Issue F1 score (best first)")
print("=" * 60)
print(summary_df.to_string(index=False))

summary_df.to_csv("model_comparison_group_split.csv", index=False)
print("\nSaved comparison table to model_comparison_group_split.csv")
