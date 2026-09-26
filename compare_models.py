import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score, f1_score

df = pd.read_csv("detection_dataset_clean.csv")
print("Dataset shape:", df.shape)

X_text = df["snippet"].astype(str)
y = df["is_issue"]

# Same split for every model, so the comparison is fair
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=42, stratify=y
)

# Same features for every model
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

results = []

for name, model in models.items():
    print(f"\n{'=' * 60}")
    print(f"Training: {name}")
    print("=" * 60)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(classification_report(y_test, y_pred, target_names=["clean", "issue"]))

# Build a clean side-by-side summary table
from sklearn.metrics import precision_score, recall_score

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
print("SUMMARY - sorted by Issue F1 score (best first)")
print("=" * 60)
print(summary_df.to_string(index=False))

summary_df.to_csv("model_comparison.csv", index=False)
print("\nSaved comparison table to model_comparison.csv")
