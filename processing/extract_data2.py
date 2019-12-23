import io
import requests
import csv
from bs4 import BeautifulSoup
import zipfile
from processing.connection import Connection

maps = {
    "SC_CODE" : "code",
    "SC_NAME": "name",
    "OPEN": "open",
    "HIGH": "high",
    "LOW" : "low",
    "CLOSE" : "close"
}

r = Connection().conn


def get_csv_url():
    url = "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx"
    csv_url = ""

    response = requests.request("GET", url=url)
    print(response)
    # print(response.text)

    soup = BeautifulSoup(response.text, features="html.parser")
    for a in soup.find_all("a", href=True):
        try:
            if a["id"] == "ContentPlaceHolder1_btnhylZip":
                print(a["href"])
                csv_url = a["href"]
        except:
            continue
    return csv_url


def insert_data_to_db(csv_url):
    response = requests.request("GET", url=csv_url)
    with io.BytesIO(response.content) as zip_file:
        with zipfile.ZipFile(zip_file) as zip_file:
            # Get first file in the archive
            for zip_info in zip_file.infolist():
                # Open file
                with zip_file.open(zip_info) as file:
                    # Load CSV file, decode binary to text
                    with io.TextIOWrapper(file) as text:

                        reader = csv.DictReader(text)

                        for row in reader:

                            keys = ["SC_CODE", "OPEN", "HIGH", "LOW", "CLOSE"]

                            data = []
                            for key in keys:
                                data.append(row[key].strip())

                            if r.exists(row["SC_NAME"].strip()):
                                r.delete(row["SC_NAME"].strip())
                            r.rpush(row["SC_NAME"].strip(), *data)


def get_data_from_db(name):
    data = []
    name = name.upper().strip()
    data = r.lrange(name, 0, -1)
    return data

    # print(r.lrange('HDFC', 0, -1))


if __name__ == '__main__':
    csv_url = get_csv_url()

    if csv_url:
        insert_data_to_db(csv_url)
    else:
        print("file not on website")

    data = get_data_from_db("hdfc")
    if data:
        print(data)
    else:
        print("Details for this name are not found, Please try some other name")