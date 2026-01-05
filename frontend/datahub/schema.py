import os
import glob
import json
import pandas as pd

def make_schema_from_excels(folder, pattern="*.xlsx"):
    schema = {}
    for path in glob.glob(os.path.join(folder, pattern)):
        name = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_excel(path, nrows=0)  # just header
        schema[name] = list(df.columns)
    return schema

if __name__ == "__main__":
    folder = "path/to/your/excels"
    schema = make_schema_from_excels(folder)
    print(json.dumps(schema, indent=2))