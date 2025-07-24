import pandas as pd
from fitparse import FitFile

def charger_donnees(fichier, extension):
    if extension == '.xlsx':
        df = pd.read_excel(fichier, sheet_name='DataAverage')
    elif extension == '.fit':
        fitfile = FitFile(fichier)
        data = []
        for record in fitfile.get_messages('record'):
            record_data = {field.name: field.value for field in record}
            data.append(record_data)
        df = pd.DataFrame(data)
    else:
        raise ValueError("Format non pris en charge (.xlsx ou .fit)")
    
    return harmoniser_colonnes(df)

def harmoniser_colonnes(df):
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'time' in col_lower:
            col_map[col] = 'time'
        elif 'power' in col_lower:
            col_map[col] = 'power'
        elif 'smo2' in col_lower or 'muscle_oxygen' in col_lower:
            col_map[col] = 'smO2'
        elif 'heart rate' in col_lower or 'hr' == col_lower.strip():
            col_map[col] = 'hr'
    
    df = df.rename(columns=col_map)
    return df
