import shutil
import os
import sys

# recursively traverses a directory and copies all c/cpp files
# to a separate directory
def extract_c_cpp_files(src_dir, dest_dir):
	os.makedirs(dest_dir)
	for root, directories, filenames in os.walk(src_dir):
		for filename in filenames: 
				if filename.endswith(".c") or filename.endswith(".cpp"):
					file =  os.path.join(root, filename)
					print ("Copying " + file)
					shutil.copy2(file, dest_dir + "/" + filename)


if __name__ == "__main__":
	for pathname in sys.argv[1:]:
		if pathname.endswith("/"):
			pathname = pathname[:-1]
		if os.path.isdir(pathname) == True:
			dest_dir = pathname + "_codes"
			extract_c_cpp_files(pathname, dest_dir)
		else:
			print ("Skipping " + pathname)
