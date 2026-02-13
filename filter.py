import pandas as pd

INPUT_FILE = "Dermatologist_in_India_results_all_2026-02-04.csv"
OUTPUT_FILE = "Dermatologist_Sorted_Output.xlsx"

df = pd.read_csv(INPUT_FILE)

raw_data = df.copy()

# Data Cleaning
df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce").fillna(0)
df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)

#Remove Extra Spaces
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Helper Columns
df["Has_Mobile"] = ((df["Phone"].notna()) & (df["Phone"] != "")).astype(int)
df["Has_Website"] = ((df["Website"].notna()) & (df["Website"] != "")).astype(int)
df["Has_Email"] = ((df["Email"].notna()) & (df["Email"] != "")).astype(int)

social_cols = ["Facebook", "Instagram", "Twitter", "LinkedIn"]
existing_social = [col for col in social_cols if col in df.columns]

if existing_social:
    df["Has_Social"] = df[existing_social].notna().any(axis=1).astype(int)
else:
    df["Has_Social"] = 0

sheet2 = df.sort_values(by="Reviews", ascending=False)
sheet3 = df.sort_values(by="Rating", ascending=False)
sheet4 = df.sort_values(by="Has_Mobile", ascending=False)
sheet5 = df.sort_values(by="Category", ascending=True)
sheet6 = df.sort_values(by="Has_Website", ascending=False)
sheet7 = df.sort_values(by="Has_Email", ascending=False)
sheet8 = df.sort_values(by="Has_Social", ascending=False)

# Remove helper columns before saving
for s in [sheet2, sheet3, sheet4, sheet5, sheet6, sheet7, sheet8]:
    s.drop(columns=["Has_Mobile","Has_Website","Has_Email","Has_Social"], inplace=True)

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    raw_data.to_excel(writer, sheet_name="Sheet1_Raw_Data", index=False)
    sheet2.to_excel(writer, sheet_name="Sheet2_Highest_Review", index=False)
    sheet3.to_excel(writer, sheet_name="Sheet3_Highest_Rating", index=False)
    sheet4.to_excel(writer, sheet_name="Sheet4_Mobile_Priority", index=False)
    sheet5.to_excel(writer, sheet_name="Sheet5_Category_Similar", index=False)
    sheet6.to_excel(writer, sheet_name="Sheet6_Website_Priority", index=False)
    sheet7.to_excel(writer, sheet_name="Sheet7_Email_Priority", index=False)
    sheet8.to_excel(writer, sheet_name="Sheet8_Social_Priority", index=False)

print("Excel file created with RAW DATA + All Sorting Sheets successfully!")
