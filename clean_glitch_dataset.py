import pandas as pd

df = pd.read_csv("merged_glitch_findings.csv")
print("Original shape:", df.shape)

# 1. Drop exact duplicate rows
df = df.drop_duplicates()
print("After dropping duplicates:", df.shape)

# 2. Normalize file paths - make every path use forward slashes consistently
df["file"] = df["file"].str.replace("\\", "/", regex=False)

# 3. Check for missing values anywhere
print("\nMissing values per column:")
print(df.isna().sum())

# 4. Exclude low-value / too-rare categories from the TRAINING target,
#    but keep them in the full findings log (separate file) for reference.
EXCLUDE_FROM_TRAINING = [
    "design_avoid_comments",              # 76% of all rows, low defect-relevance (style opinion)
    "implementation_improper_alignment",  # only ~4 examples, too rare to learn
]

# Save the full, untouched findings (for reference / reporting)
df.to_csv("glitch_findings_full.csv", index=False)

# Save the training-ready subset (excludes the two categories above)
df_train = df[~df["smell_code"].isin(EXCLUDE_FROM_TRAINING)].copy()
print("\nShape after excluding low-value categories for training:", df_train.shape)

print("\nRemaining smell type distribution (training set):")
print(df_train["smell_description"].value_counts())

# 5. Add a clean numeric label column, ready for a classifier to predict.
#    smell_code looks like "sec_hard_secr", "design_duplicate_block",
#    "implementation_long_statement" - the prefix before the first "_"
#    is a natural higher-level category (security / design / implementation).
df_train["category"] = df_train["smell_code"].str.split("_").str[0]

print("\nHigh-level category distribution:")
print(df_train["category"].value_counts())

# Numeric encoding of the specific smell type (this is your actual
# multiclass training label - one number per distinct smell_code)
df_train["label_id"], label_names = pd.factorize(df_train["smell_code"])

# Save the mapping separately so you can always translate label_id back
# to a real smell name later (for reading predictions / building the
# recommendation table)
label_mapping = pd.DataFrame({
    "label_id": range(len(label_names)),
    "smell_code": label_names,
})
label_mapping.to_csv("label_mapping.csv", index=False)

print(f"\n{len(label_names)} distinct smell types encoded as label_id 0-{len(label_names)-1}.")
print("Mapping saved to label_mapping.csv")

df_train.to_csv("glitch_findings_clean.csv", index=False)
print("\nSaved:")
print("  glitch_findings_full.csv  (everything, for reference)")
print("  glitch_findings_clean.csv (training-ready subset, with category + label_id)")
print("  label_mapping.csv         (label_id -> smell_code lookup table)")