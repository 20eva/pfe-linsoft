import pandas as pd

df = pd.read_csv("detection_dataset.csv")
print("Original shape:", df.shape)

# 1. Drop exact duplicate rows
df = df.drop_duplicates()
print("After dropping exact duplicates:", df.shape)

# 2. Normalize file paths
df["file"] = df["file"].astype(str).str.replace("\\", "/", regex=False)

# 3. Check missing values
print("\nMissing values per column:")
print(df.isna().sum())
df = df.dropna(subset=["snippet"])
print("After dropping rows with no snippet text:", df.shape)

# 4. Drop snippets that are too short to carry any real signal
#    (single characters, stray punctuation, etc.)
df["snippet_len"] = df["snippet"].astype(str).str.len()
too_short = (df["snippet_len"] < 5).sum()
df = df[df["snippet_len"] >= 5]
print(f"\nDropped {too_short} snippets shorter than 5 characters.")
print("Shape now:", df.shape)

# 5. Check for label conflicts: the SAME snippet text appearing as both
#    is_issue=1 and is_issue=0 would confuse the model (identical input,
#    contradictory label). This can legitimately happen since a common
#    line like "state: present" might be flagged in one context and not
#    another, but too much of it is a real problem worth knowing about.
snippet_conflict = (
    df.groupby("snippet")["is_issue"].nunique()
)
conflicting_snippets = snippet_conflict[snippet_conflict > 1].index
print(f"\n{len(conflicting_snippets)} distinct snippet texts appear as BOTH "
      f"issue and clean elsewhere in the dataset.")
conflict_rows = df["snippet"].isin(conflicting_snippets).sum()
print(f"({conflict_rows} total rows affected)")

# 6. Check class balance and per-repo balance after all cleaning
print("\nFinal is_issue distribution:")
print(df["is_issue"].value_counts())

print("\nTop 10 repos by row count (post-cleaning):")
print(df["repository"].value_counts().head(10))

df = df.drop(columns=["snippet_len"])
df.to_csv("detection_dataset_clean.csv", index=False)
print("\nSaved cleaned dataset to detection_dataset_clean.csv")
