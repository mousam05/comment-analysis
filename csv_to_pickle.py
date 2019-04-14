import csv
import pickle
import sys

if __name__ == "__main__":
	filename = sys.argv[1]
	file = csv.reader(open(filename), delimiter=',')
	result = {}
	for row in file:
		result[row[0].lower()] = row[1].lower()
	fp = open("result.p", "wb")
	pickle.dump(result, fp)
	fp.close()
