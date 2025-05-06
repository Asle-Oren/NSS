import pandas as pd
import datetime
import os
import time
import asyncio
import threading
import requests
from barcode import Code39
from barcode.writer import ImageWriter
from PIL import Image
from threading import Lock

class CardTracker:
    def __init__(self):
        self.card = None
        self.card_timer = time.time()

bulk_isbn_buffer = []
bulk_timer = None
bulk_lock = Lock()
object_list = None
df_library = None
bulk_timer = None

def read_scan(scan):
    return scan #Used to do more stuff before


def lookup(object_list, barcode):
    print(f'{object_list=}')
    for i, obj in enumerate(object_list):
        print(f'{obj=}')
        if barcode == obj.get("NSS Barcode"):
            return i
    return -1


def make_excel_files():
    if not os.path.isfile("loan_system_object_library.xlsx"):
        df = pd.DataFrame(columns=["Name", "Type Object", "Belongs To", "NSS Barcode", "State", "ISBN", "Registered Date", "Author", "Publisher", "Published"])
        df.to_excel("loan_system_object_library.xlsx", index=False)
    if not os.path.isfile("activity_history.xlsx"):
        df = pd.DataFrame(columns=["Name", "Type Object", "Belongs To", "Action", "Timestamp", "NSS Barcode", "Card"])
        df.to_excel("activity_history.xlsx", index=False)


def read_library():
    try:
        df = pd.read_excel("loan_system_object_library.xlsx")
        return df.to_dict(orient='records'), df
    except Exception as e:
        print(f"Error reading library file: {e}")
        return [], pd.DataFrame(columns=["Name", "Type Object", "Belongs To", "NSS Barcode", "State", "ISBN", "Registered Date", "Author", "Publisher", "Published"])


def save_library(df):
    df.to_excel("loan_system_object_library.xlsx", index=False)


def append_history(entry):
    try:
        df = pd.read_excel("activity_history.xlsx")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "Type Object", "Belongs To", "Action", "Timestamp", "NSS Barcode", "Card"])
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_excel("activity_history.xlsx", index=False)


def handle_return(object_list, df_library, scan, card_tracker):
    barcode = read_scan(scan)
    index = lookup(object_list, barcode)
    if index != -1 and object_list[index].get("State", "").lower() == "loaned":
        now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        df_library.at[index, "State"] = "available"
        save_library(df_library)
        object_list = df_library.to_dict(orient='records')

        obj = object_list[index]
        name = obj.get("Name", "")
        object_type = obj.get("Type Object", "")
        owner = obj.get("Belongs To", "")

        append_history({
            'Name': name,
            'Type Object': object_type,
            'Belongs To': owner,
            'Action': 'Handed In',
            'Timestamp': now,
            'NSS Barcode': barcode,
            'Card': card_tracker.card
        })
        print("Object has been returned")
    else:
        print("Object not found or already available")
    return object_list, df_library


def handle_loan(object_list, df_library, scan, card_tracker):
    if card_tracker.card is None:
        print("Please scan ID card first")
        return object_list, df_library

    barcode = read_scan(scan)
    index = lookup(object_list, barcode)
    if index == -1:
        print("Object not registered")
    elif object_list[index].get("State", "").lower() == "loaned":
        print("Object already loaned")
    else:
        now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        df_library.at[index, "State"] = "loaned"
        save_library(df_library)
        object_list = df_library.to_dict(orient='records')

        obj = object_list[index]
        name = obj.get("Name", "")
        object_type = obj.get("Type Object", "")
        owner = obj.get("Belongs To", "")

        append_history({
            'Name': name,
            'Type Object': object_type,
            'Belongs To': owner,
            'Action': 'Loaned',
            'Timestamp': now,
            'NSS Barcode': barcode,
            'Card': card_tracker.card
        })
        print(f"Object loaned to: {card_tracker.card}")
    return object_list, df_library


def handle_barcode_print(isbn, card_tracker):
    global object_list
    logo_path = "logo_icon.png"
    if not os.path.exists(logo_path):
        try:
            logo_url = "https://static.wixstatic.com/media/ff5881_574575c2c3ff476abfcb99be4eb87da5~mv2.png/v1/fill/w_374,h_342,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Logo%20Skjold%20NSS.png"
            img_data = requests.get(logo_url).content
            with open(logo_path, 'wb') as f:
                f.write(img_data)
        except Exception as e:
            print(f"Failed to download logo: {e}")
            return None

    print(f"Looking up book info for ISBN {isbn}...")
    try:
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch or parse book data: {e}")
        return None

    if "items" not in data:
        print("No book info found for that ISBN.")
        return None

    volume = data["items"][0].get("volumeInfo", {})
    title = volume.get("title", "Unknown Title")
    author = ", ".join(volume.get("authors", []))
    publisher = volume.get("publisher", "")
    published = volume.get("publishedDate", "")
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    try:
        df_library = pd.read_excel("loan_system_object_library.xlsx")
    except:
        df_library = pd.DataFrame(columns=["Name", "Type Object", "Belongs To", "NSS Barcode", "State", "ISBN", "Registered Date", "Author", "Publisher", "Published"])

    copy_id = (df_library["NSS Barcode"].astype(str).str.startswith(f"{isbn}+")).sum() + 1
    barcode = f"{isbn}+{copy_id}"

    if barcode in df_library.get("NSS Barcode", []):
        print(f"Barcode {barcode} already exists. Skipping.")
        return None

    new_entry = {
        "Name": title,
        "Type Object": "Book",
        "Belongs To": "NSS",
        "NSS Barcode": barcode,
        "State": "Registered",
        "ISBN": isbn,
        "Registered Date": now,
        "Author": author,
        "Publisher": publisher,
        "Published": published
    }

    df_library = pd.concat([df_library, pd.DataFrame([new_entry])], ignore_index=True)
    save_library(df_library)
    object_list = df_library.to_dict(orient='records')
    print("Book information added to the library.")
    append_history({'Name': title, 'Type Object': "Book", 'Belongs To': "NSS",
                    'Action': 'Registered', 'Timestamp': now, 'NSS Barcode': barcode, 'Card': card_tracker.card})

    filename = f"barcodes/barcode_{isbn}_{copy_id}"
    os.makedirs("barcodes", exist_ok=True)
    Code39(barcode, writer=ImageWriter(), add_checksum=False).save(filename)

    logo_height = 100
    margin = 10
    with Image.open(filename+".png") as barcode_img:
        base_width, base_height = barcode_img.size
        barcode_img_logo = Image.new('RGBA', (base_width, base_height+logo_height+margin),(255,255,255,255))
        with Image.open(logo_path).convert("RGBA") as logo_img:
            logo_size = (109, 100) # org img dimensions 374x342
            logo_img.thumbnail(logo_size, Image.Resampling.LANCZOS)
            logo_x = (barcode_img.width-logo_img.width)//2
            logo_y = margin
            barcode_img_logo.paste(barcode_img, (0, margin+logo_height))
            barcode_img_logo.paste(logo_img, (logo_x, logo_y), logo_img)
            barcode_img_logo.save(filename+".png")
    print(f"Saved barcode image to {filename+".png"}")
    return filename


def handle_barcode_layout(filenames, cleanup=True):
    from PIL import Image

    images = []
    for f in filenames:
        try:
            with Image.open(f + ".png") as img:
                images.append(img.copy())
        except Exception as e:
            print(f"Failed to open image {f+'.png'}: {e}")
    if not images:
        print("No valid images to print.")
        return

    # Constants
    DPI = 300
    A4_WIDTH, A4_HEIGHT = 2480, 3508  # A4 at 300 DPI
    MARGIN = 10
    SPACING = 10
    ASPECT_RATIO = 0.3799
    MAX_BARCODE_WIDTH = 1000  # Resize to fit more per page
    MAX_BARCODE_HEIGHT = round(MAX_BARCODE_WIDTH*ASPECT_RATIO) + 109 # height = width x 0.3799 rounded, adding logo height

    pages = []
    layout = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
    x, y = MARGIN, MARGIN
    max_height = 0

    for img in images:
        img = img.resize((MAX_BARCODE_WIDTH, MAX_BARCODE_HEIGHT), Image.Resampling.LANCZOS)

        if x + img.width > A4_WIDTH - MARGIN:
            x = MARGIN
            y += max_height + SPACING
            max_height = 0
        if y + img.height > A4_HEIGHT - MARGIN:
            pages.append(layout)
            layout = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
            x, y = MARGIN, MARGIN
            max_height = 0

        layout.paste(img, (x, y))
        x += img.width + SPACING
        max_height = max(max_height, img.height)

    pages.append(layout)

    os.makedirs("barcodes", exist_ok=True)
    pdf_filename = "barcodes/barcode_sheet_all.pdf"
    pages_rgb = [p.convert('RGB') for p in pages]
    pages_rgb[0].save(
        pdf_filename,
        save_all=True,
        append_images=pages_rgb[1:],
        format='PDF',
        resolution=DPI,
        dpi=(DPI, DPI)
    )

    print(f"Saved combined A4 barcode PDF as {pdf_filename}")

    print(f'Cleaning up pngs.')
    if cleanup:
        for f in filenames:
            try:
                os.remove(f + ".png")
            except Exception as e:
                print(f"Failed to delete {f+'.png'}: {e}")


def handle_bulk_buffered_isbn(scan):
    global bulk_timer
    with bulk_lock:
        bulk_isbn_buffer.append(scan)
        bulk_timer = time.time()


def check_bulk_timeout(card_tracker):
    global bulk_timer, object_list
    with bulk_lock:
        if bulk_timer is not None and time.time() - bulk_timer > 30:
            print("\n30 seconds passed. Generating barcode sheet...")
            filenames = [handle_barcode_print(isbn, card_tracker) for isbn in bulk_isbn_buffer if isbn]
            handle_barcode_layout([f for f in filenames if f])
            bulk_isbn_buffer.clear()
            bulk_timer = None


async def auto_clear(card_tracker, timeout=60):
    while True:
        await asyncio.sleep(1)
        if card_tracker.card is not None and time.time() - card_tracker.card_timer > timeout:
            card_tracker.card = None
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Card automatically cleared due to inactivity")
            print("Waiting for ID card scan: ", end="")
        check_bulk_timeout(card_tracker)


def start_async_loop(card_tracker, timeout):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(auto_clear(card_tracker, timeout))


def main():
    global object_list, df_library, bulk_timer
    make_excel_files()
    object_list, df_library = read_library()
    mode = "loan"
    card_tracker = CardTracker()
    threading.Thread(target=start_async_loop, args=(card_tracker, 60), daemon=True).start()
    while True:
        if card_tracker.card == None and mode == "loan":
            scan = input("Waiting for ID card scan: ")
        else:
            scan = input("Waiting for scan: ")
        if scan == "exit":
            break
        elif scan.lower() in ["loan", "return", "print barcode", "bulk import", "print layout"]:
            if scan.lower() == "print layout" and bulk_isbn_buffer:
                bulk_timer = None
                with bulk_lock:
                    filenames = [handle_barcode_print(isbn, card_tracker) for isbn in bulk_isbn_buffer if isbn]
                    handle_barcode_layout([f for f in filenames if f])
                    bulk_isbn_buffer.clear()
                    mode = "loan"
            else:
                mode = scan.lower()
                print(f"Mode set to {mode}")
        elif scan[0:3].upper() == "UIT":
            if scan == card_tracker.card:
                card_tracker.card = None
                print("Card cleared")
            else:
                card_tracker.card = scan
                card_tracker.card_timer = time.time()
                print("Card scanned")
        else:
            if mode == "return":
                object_list, df_library = handle_return(object_list, df_library, scan, card_tracker)
            elif mode == "loan":
                card_tracker.card_timer = time.time()
                object_list, df_library = handle_loan(object_list, df_library, scan, card_tracker)
            elif mode == "print barcode":
                handle_barcode_print(scan, card_tracker)
            elif mode == "bulk import":
                handle_bulk_buffered_isbn(scan)
                print(f'Scanned: {scan}')
                print(f'Mode is currently set to: {mode}, scan all ISBNs. \n Use "print layout" to generate barcodes')


if __name__ == "__main__":
    main()
