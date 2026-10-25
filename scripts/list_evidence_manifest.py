import pandas as pd

df = pd.read_csv("dataset/evidence_files.csv")
for idx, row in df.iterrows():
    print(f"{row['file_id']} | {row['file_path']} | {row['origin']} | {row['captured_at']}")
