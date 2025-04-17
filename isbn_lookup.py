import pandas as pd
import requests

# Load Excel file
df = pd.read_excel("utlånsystem_objekt_bibliotek.xlsx")

# Iterate through rows with a valid ISBN
for index, row in df.iterrows():
    isbn = row["isbn-13"]
    if pd.notna(isbn):
        # Query Google Books API
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        data = response.json()
        
        if "items" in data:
            volume_info = data["items"][0]["volumeInfo"]
            
            df.at[index, "Bok Tittel"] = volume_info.get("title")
            df.at[index, "Forfatter"] = ", ".join(volume_info.get("authors", []))
            df.at[index, "Utgave"] = volume_info.get("contentVersion")
            df.at[index, "Binding"] = volume_info.get("printType")
            df.at[index, "Utgiver"] = volume_info.get("publisher")
            df.at[index, "Publisert"] = volume_info.get("publishedDate")

# Save updated Excel file
df.to_excel("updated_books.xlsx", index=False)
