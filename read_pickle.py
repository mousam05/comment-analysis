import sys
import pickle

if __name__ == "__main__":
	pickleName = open(sys.argv[1], "rb")
	result = pickle.load(pickleName)
	print(result)
