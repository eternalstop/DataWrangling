import csv
import json


def read_csv():
    dataList = []
    csvfile = 'data/data.csv'
    with open(csvfile, 'r') as f:
        csvdata = csv.DictReader(f)
        for row in csvdata:
            dataList.append(row)
    return dataList


def read_json():
    jsonfile = 'data/data.json'
    with open(jsonfile, 'rb') as f:
        jsondata = json.loads(f)
    print('111111')
    return jsondata


if __file__ == '__main__':
    # read_csv()
    read_json()