import pandas as pd
import requests

# Load the Excel file
df = pd.read_excel("utlånsystem_objekt_bibliotek.xlsx")

# Loop through rows with a valid ISBN-13
for index, row in df.iterrows():
    isbn = row["isbn-13"]
    if pd.notna(isbn):
        # Query Google Books API
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        data = response.json()

        if "items" in data:
            info = data["items"][0]["volumeInfo"]

            # Fill in book metadata
            df.at[index, "Bok Tittel"] = info.get("title")
            df.at[index, "Forfatter"] = ", ".join(info.get("authors", []))
            df.at[index, "Utgave"] = info.get("contentVersion")
            df.at[index, "Binding"] = info.get("printType")
            df.at[index, "Utgiver"] = info.get("publisher")
            df.at[index, "Publisert"] = info.get("publishedDate")

# Save the updated file
df.to_excel("oppdatert_bokliste.xlsx", index=False)
