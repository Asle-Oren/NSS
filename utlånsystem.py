import csv
import datetime
import os
import time


def read(scan):
    temp_list = []
    k = 0
    string = ""
    for i in range(len(scan)):
        if scan[i] == "$":
            temp_list.append(string)
            k += 1
            string = ""
        else:
            string = string + scan[i]
    temp_list.append(string)
    print(temp_list)
    return temp_list


def lookup(object_list, barcode):
    try:
        for i in object_list:
            if barcode == i["strekkode"]:
                return object_list.index(i)

        return -1
    except:
        print("An error occured")

def register(scan):
    pass

def main():
    # check if csv files exist, if not create the files

    exists1 = os.path.isfile("Utlånsystem.csv")
    if not exists1:
        f1 = open("Utlånsystem.csv", "x", encoding='utf-8')
        f1.write("navn;ting;tilhørighet;status;dato status endring;strekkode\n")
        f1.close()
        time.sleep(0.5)

    exists2 = os.path.isfile("historikk.csv")
    if not exists2:
        f2 = open("historikk.csv", "x", encoding='utf-8')
        f2.close()
        time.sleep(0.5)

    object_list = []
    with open('Utlånsystem.csv', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')

        for i in reader:
            object_list.append(i)

        print(object_list)

    mode = "loan"
    card = None
    card_timer = time.time()
    while True:
        if card == None:
            scan = input("Waiting for ID card scan: ")
        else:
            scan = input("Waiting for scan: ")

        if time.time() - card_timer > 59:
            card = None

        if scan == "exit":
            exit()
        elif scan.lower() == "register":
            mode = "register"
            print("Mode set to register")
        elif scan.lower() == "loan":
            mode = "loan"
            print("Mode set to loan")
        elif scan.lower() == "return":
            mode = "return"
            print("Mode set to return")
        elif scan[0:3].upper() == "UIT":  # student id
            if scan == card:
                card = None
                print("Card cleared")
            else:
                card = scan
                print("Card scanned, scan objects to loan")
                card_timer = time.time()


        else:  # object scanned
            if mode == "return":
                scan = read(scan)
                name, object_type, owner, barcode = scan[0], scan[1], scan[2], scan[3]

                #rewrite lookup function to look for unique id instead
                index = lookup(object_list, barcode)
                if index != -1:  # if object is in the system
                    if object_list[index]["status"].capitalize() == "Utlånt":
                        object_list[index]["status"] = "Levert"
                        object_list[index]["dato status endring"] = datetime.datetime.now().strftime(
                            '%d.%m.%Y %H:%M:%S')

                        # update csvfile
                        with open('Utlånsystem.csv', encoding='utf-8', newline='') as in_file:
                            reader = csv.reader(
                                in_file.readlines(), delimiter=';')

                        with open('Utlånsystem.csv', 'w', encoding='utf-8', newline='') as out_file:
                            writer = csv.writer(out_file, delimiter=';')
                            for line in reader:
                                if line[5] == barcode:
                                    writer.writerow([line[0], line[1], line[2], "Levert", str(
                                        datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), line[5]])
                                    break
                                else:
                                    writer.writerow(line)
                            writer.writerows(reader)

                        # add history
                        with open('historikk.csv', 'a', encoding='utf-8', newline='') as csvfile:
                            writer = csv.writer(csvfile, delimiter=';')
                            writer.writerow([name, object_type, owner, "Levert", str(
                                datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), barcode])
                        print("Object has been returned")
                    else:
                        print("Object has already been returned")

            elif mode == "register":  # code to add new entry to csv file

                register(scan)

                scan = read(scan)
                name, object_type, owner, barcode = scan[0], scan[1], scan[2], scan[3]

                if lookup(object_list, barcode) == -1:  # check if object is in the system
                    object_list.append({'navn': name, 'ting': object_type, 'tilhørighet': owner, 'status': "registrert", 'dato status endring': str(
                        datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), 'strekkode': barcode})
                    with open('Utlånsystem.csv', 'a', encoding='utf-8', newline='') as csvfile:
                        writer = csv.writer(csvfile, delimiter=';')
                        writer.writerow([name, object_type, owner, "Levert", str(
                            datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), barcode])

                    with open('historikk.csv', 'a', encoding='utf-8', newline='') as csvfile:
                        writer = csv.writer(csvfile, delimiter=';')
                        writer.writerow([name, object_type, owner, "registrert", str(
                            datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), barcode])
                    print("Object has been registered in the system.")
                else:
                    print("Object already in system")

            elif mode == "loan":
                if card == None:
                    print("Please scan id card to loan objects")
                else:
                    scan = read(scan)
                    try:
                        name, object_type, owner, barcode = scan[0], scan[1], scan[2], scan[3]
                    except:
                        print("An error occured with the scanned item")
                        continue

                    index = lookup(object_list, barcode)
                    if index != -1:  # if object is in the system
                        if object_list[index]["status"].capitalize() != "Utlånt":
                            object_list[index]["status"] = "Utlånt"
                            object_list[index]["dato status endring"] = datetime.datetime.now().strftime(
                                '%d.%m.%Y %H:%M:%S')
                            print("Object has been registered as loaned by: ", card)

                            # update csvfile
                            with open('Utlånsystem.csv', encoding='utf-8', newline='') as in_file:
                                reader = csv.reader(
                                    in_file.readlines(), delimiter=';')

                            with open('Utlånsystem.csv', 'w', encoding='utf-8', newline='') as out_file:
                                writer = csv.writer(out_file, delimiter=';')
                                for line in reader:
                                    if line[5] == barcode:
                                        writer.writerow([line[0], line[1], line[2], "Utlånt", str(
                                            datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), line[5]])
                                        break
                                    else:
                                        writer.writerow(line)
                                writer.writerows(reader)

                            # add history
                            with open('historikk.csv', 'a', encoding='utf-8', newline='') as csvfile:
                                writer = csv.writer(csvfile, delimiter=';')
                                writer.writerow([name, object_type, owner, "Utlånt", str(
                                    datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')), barcode, card])

                        else:
                            print("This object is already being borrowed by someone")
                    else:
                        print("This object has not been registered in the system")


if __name__ == "__main__":
    main()

# code-39
