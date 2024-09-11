import csv
import argparse
import re


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('file1', metavar='file1', nargs=1,
                    help='原始坐标文件')
parser.add_argument('file2', metavar='file2', nargs=1,
                    help='JLC坐标文件')

args = parser.parse_args()

wfile =  open(args.file2[0], 'w', newline='')
    
spamwriter = csv.writer(wfile, delimiter=',',
                        quotechar='\"', quoting=csv.QUOTE_MINIMAL)
spamwriter.writerow(['Designator', 'Value', 'Footprint', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])

with open(args.file1[0], newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='\"')

    i = 0
    for row in spamreader:
        if i > 0:
            if row[6] == 'top':
                row[6] = 'T'
            else:
                row[6] = 'B'

            spamwriter.writerow(row)

        i += 1
