import os
import sys
import pickle
import MySQLdb

MYSQL_SERVER = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "mrox"

ROOT_PATH = "/home/mousam/Downloads/mtp2"

# extracts the contents of a MySQL database and returns it as a dict:
	# keys are table names and values are table contents;
	# the table contents is a list with 2 elements:
	# the first element is a tuple of column names, and
	# the second element is tuple of tuples representing rows
def extract_db(db_name):

	db = MySQLdb.connect(MYSQL_SERVER, MYSQL_USER, MYSQL_PASSWORD,
		db_name, charset='utf8', use_unicode=True )

	cursor = db.cursor()
	sql = "show tables"
	cursor.execute(sql)
	tables = cursor.fetchall()

	result = {}
	for table in tables:
		table_name = table[0]
		sql = "select * from " + table_name
		cursor.execute(sql)
		columns = [column[0] for column in cursor.description]
		fetchedTable = cursor.fetchall()
		result[table_name] = []
		result[table_name].append(tuple(columns))
		result[table_name].append(fetchedTable)

	db.close()
	return result


# takes a c or cpp file as input and creates a pickle file containing symbols
	# a.cpp => a.cpp.symbols
def process_file(filename):

	pickle_name = filename + ".symbols"
	if os.path.isfile(pickle_name):
		print ("Symbols file already exists for " + filename)
		return

	# run find-class-decls or syntax-tree on this file, depending on .c/.cpp type
	if filename.endswith(".c"):
		rc = os.system(ROOT_PATH + "/llvm/build/bin/find-class-decls " + filename)
	elif filename.endswith(".cpp"):
		rc = os.system(ROOT_PATH + "/llvm/build/bin/syntax-tree " + filename)
	else:
		print ("Skipping " + filename)
		return

	if rc != 0:
		print ("Extraction of symbols failed for " + filename)
		return

	# extract the 'test' database contents to pickle
	symbols_db = extract_db("test")
	with open(pickle_name, "wb") as fp:
		rc = pickle.dump(symbols_db, fp)
		if rc == 0:
			print ("Symbols from " + filename + " saved in " + pickle_name)


if __name__ == "__main__":

	for pathname in sys.argv[1:]:

		if pathname.endswith("/"):
			pathname = pathname[:-1] # remove the trailing slash(/)

		# process all files in a directory
		if os.path.isdir(pathname) == True: 
			for file in os.listdir(pathname):
				filename = pathname + "/" + file
				process_file(filename)

		else:
			# process single file
			process_file(pathname)