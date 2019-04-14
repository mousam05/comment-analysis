import sys
import re
import os
import pickle
import csv
import editdistance

from nltk.stem import PorterStemmer
from nltk.tag.stanford import StanfordPOSTagger
from nltk.parse.stanford import StanfordDependencyParser

ps = PorterStemmer()

EDIT_DISTANCE_APPLICATION_THRESHOLD = 6
EDIT_DISTANCE_MATCH_THRESHOLD = 2

ROOT_PATH = os.getcwd()
PROGRAM_DOMAIN_CONCEPTS_FILE_PATH =  os.path.join(ROOT_PATH, "ProgramDomainConcepts.p")
PROBLEM_DOMAIN_CONCEPTS_FILE_NAME = "ProblemDomainConcepts.txt"
PROBLEM_DOMAIN_CONCEPTS_GRAM_LENGTH = 3

CATEGORY_COUNT = 30
CAT_CONCEPTS_MATCH_SYMBOLS = 1
CAT_CONCEPTS_MATCH_TYPE = 2
CAT_CONCEPTS_NOT_MATCH_SYMBOLS = 3
CAT_CONCEPTS_PARTIALLY_MATCH_SYMBOLS = 4
CAT_CONCEPTS_MATCH_STRUCTURE = 5
CAT_NO_PROGRAM_DOMAIN_CONCEPTS = 6
CAT_NO_PROBLEM_DOMAIN_CONCEPTS = 7
CAT_LOW_PROGRAM_DOMAIN_CONCEPTS = 8
CAT_HIGH_PROGRAM_DOMAIN_CONCEPTS = 9
CAT_LOW_PROBLEM_DOMAIN_CONCEPTS = 10
CAT_HIGH_PROBLEM_DOMAIN_CONCEPTS = 11
CAT_CODE_COMMENT = 12
CAT_SHORT = 13
CAT_HIGH_SCOPE = 14
CAT_LOW_SCOPE = 15
CAT_COPYRIGHT_LICENSE = 16
CAT_DATE = 17
CAT_EMAIL = 18
CAT_CONTACT = 19
CAT_BUG_VERSION = 20
CAT_AUTHOR_NAME = 21
CAT_BUILD = 22
CAT_EXCEPTION = 23
CAT_PERFORMANCE = 24
CAT_DESIGN = 25
CAT_MEMORY = 26
CAT_SYSTEM_SPEC = 27
CAT_LIBRARY = 28
CAT_OUTPUT_RETURN = 29
CAT_JUNK = 30

OUTPUT_COMMENTS_FILE_PATH = os.path.join(ROOT_PATH, "comments.csv")

stanford_pos_tagger = StanfordPOSTagger('english-bidirectional-distsim.tagger')
stanford_dep_parser = StanfordDependencyParser(model_path=os.path.join("edu", "stanford", "nlp", "models", "lexparser", "englishPCFG.ser.gz"))

def get_ngrams(tokens, n):
	result = []
	k = len(tokens)
	for i in range(0, k-n+1):
		ngram = ''
		for j in range(i, i+n):
			ngram = ngram + ' ' + tokens[j]
		result.append(ngram[1:])
	return result

def find_program_domain_concepts(comment, program_domain_concepts_dict):

	comment = comment.lower()
	concepts = {}
	tokens = comment.split()

	# attempt 1: stemming
	for token in tokens:
		token = token.strip(" .!,&()-={}[]\/\\\"\';:<>\n\t")
		stemmed_token = ps.stem(token)
		if stemmed_token in program_domain_concepts_dict:
			concepts[token] = [stemmed_token, program_domain_concepts_dict[stemmed_token]]


	bigrams = get_ngrams(tokens, 2)
	trigrams = get_ngrams(tokens, 3)
	tokens.extend(bigrams)
	tokens.extend(trigrams)

	# attempt 2: edit-distance
	for token in tokens:
		if len(token) >= EDIT_DISTANCE_APPLICATION_THRESHOLD:
			for concept in program_domain_concepts_dict:
				if editdistance.eval(token, concept) <= EDIT_DISTANCE_MATCH_THRESHOLD:
					concepts[token] = [concept, program_domain_concepts_dict[concept]]

	return concepts


def find_problem_domain_concepts_grams(problem_domain_concepts_list):

	result = set()
	for concept in problem_domain_concepts_list:
		for gram_length in range(1, min(len(concept.split()), PROBLEM_DOMAIN_CONCEPTS_GRAM_LENGTH) + 1):
			result.update(get_ngrams(concept.split(), gram_length))

	return result

def find_problem_domain_concepts(comment, problem_domain_concepts_grams):

	comment = comment.lower()
	result = set()
	for gram in problem_domain_concepts_grams:
		if gram in comment:
			result.add(gram)

	return list(result)

# def find_scope(comment, fr_line, to_line):
# 	TODO


def is_verb(tag):
	return tag in ['VB', 'VBZ', 'VBN', 'VBP', 'VBG', 'VBD']

def is_conditional(postags, dependencies):
	for postag in postags:
		if postag[1]=='IN':
			for dependency in dependencies:
				if dependency[1] == 'mark' and (dependency[0][1] == 'IN' or dependency[2][1] == 'IN'):
					return True
	return False

# use stanford parser to categories comments based on postags and dependencies
# list of categories:
# CONDITIONAL: contains 'IN' tag and has a 'mark' dependency involving the 'IN' tag
# NN_JJ_SYM_ROOT: there is a NN, JJ or SYM tag as ROOT
# VERB_ROOT:  there is a verb (VB, VBZ, VBN, VBP, VBG, VBD) tag as ROOT
# VERB_AUXILIARY: the ROOT is not verb, but there is an auxiliary verb
# 
def find_nlp_categories(comment):
	result = []

	postags = stanford_pos_tagger.tag(comment.split())
	raw_dependencies = [parse for parse in stanford_dep_parser.raw_parse(comment)]
	dependencies = [list(dep.triples()) for dep in raw_dependencies]

	#for now, assume a single dependency tree
	raw_dependencies = raw_dependencies[0]
	dependencies = dependencies[0]

	#check for each category

	if is_conditional(postags, dependencies):
		result.append('CONDITIONAL')

	if raw_dependencies.root['tag'] in ['NN', 'JJ', 'SYM']:
		result.append('NN_JJ_SYM_ROOT')

	if is_verb(raw_dependencies.root['tag']):
		result.append('VERB_ROOT')
	else:
		for postag in postags:
			if is_verb(postag[1]):
				result.append('VERB_AUXILIARY')
				break

	return result

def matches_with_keywords(text, keywords):
	text = text.lower()

	for keyword in keywords:
		if keyword in text:
			return True

	return False

def is_copyright_or_license_comment(comment):

	keywords = [
				"copyright", "copyleft", "copy-right", "license", "licence", "trademark", "open source", "open-source"
				]
	return matches_with_keywords(comment, keywords)

def is_bug_or_version_related_comment(comment):

	keywords = [
				" bug", "bug #", "bugid", "bug id", "bug number", "bug no", "bugno", "bugzilla",    # debug should not match
				" fix", "fix #", "fixid", "fix id", "fix number", "fix no", "fixno",   				# postfix, suffix etc should not match
				"patch", "patch #", "patchid", "patch id", "patch number", "patch no", "patchno",
				]

	return matches_with_keywords(comment, keywords) or \
		((re.search("bug [0-9]|fix [0-9]|version [0-9]", comment) is not None) and not is_copyright_or_license_comment(comment))



def is_build_related_comment(comment):

	keywords = [
				"cmake", "makefile", "build", "g++", "gcc", "dependencies", "apt-get",
				"git clone", "debug", "bin/"
				]

	return matches_with_keywords(comment, keywords)

def is_system_spec_related_comment(comment):

	keywords = [
				"ubuntu", "endian", "gpu", "hyperthreading", "32-bit", "64-bit", "128-bit", "configuration", "specification"
				"32bit", "64bit", "128bit", "configure"
				]

	return matches_with_keywords(comment, keywords) or (re.search("[0-9] [gG][bB]|[0-9] [mM][bB]|[0-9] [kK][bB]|Windows", comment) is not None)

def is_author_name_comment(comment):
	keywords = [
				"written by", "coded by", "developed by", "edited by", "modified by", "author", "contact",
				"fixed by"
				]
	return matches_with_keywords(comment, keywords)

def is_date_comment(comment):
	keywords = [
				"date of", "edited on", "written on", "created on", "modified on"
				]

	return matches_with_keywords(comment, keywords) or \
		(re.search("\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}[\-\/][a-zA-Z]{3}[\-\/]\d{2,4}", comment) is not None)

def is_email_comment(comment):
	keywords = [
				"mail dot com", "mail dot in", "email"
				]

	return matches_with_keywords(comment, keywords) or \
		(re.search("([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)", comment) is not None)


def is_todo_comment(comment):

	keywords = ["todo", "to-do"]
	return matches_with_keywords(comment, keywords)

def is_junk_comment(comment):
	# there are no letters or numbers in the comment
	return re.search("[a-zA-Z0-9]", comment) is None

def get_comments(filename):

	file = open(filename , "r")
	text = file.read()
	file.close()
	file = open(filename , "r")
	lines = file.readlines()
	file.close()

	all_comments = re.compile( r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE).findall(text)
	comment_iterator = re.compile( r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE)
	l = [(m.start(0), m.end(0)) for m in re.finditer(comment_iterator, text)]	

	start_line = []
	end_line = []
	for pos in range(0, len(all_comments)):
		location = l[pos][0]
		s = text[:location + 1]
		lineNo1 = s.count('\n') + 1
		location1 = l[pos][1]
		s = text[:location1 + 1]
		lineNo2 = s.count('\n')
		start_line.append(lineNo1)
		end_line.append(lineNo2)

		if all_comments[pos].startswith("//"):
			all_comments[pos] = all_comments[pos][2:]
		else:
			all_comments[pos] = all_comments[pos][2:-2]

		all_comments[pos] = all_comments[pos].strip()


	result = []

	for pos in range(0, len(all_comments)):

		text = all_comments[pos]
		start = start_line[pos]
		end = end_line[pos]

		#bundling consecutive single line comments
		if len(result) > 0 and lines[start - 1].strip().startswith("//") and result[-1][2] == start - 1:
			result[-1][0] = result[-1][0] + "\n" + text
			result[-1][2] = start

		else:
			result.append([text, start, end])

	return result

def extract_comments_info(filename, program_domain_concepts_dict, problem_domain_concepts_grams):

	result = []
	comments = get_comments(filename)

	for comment in comments:

		[comment_text, start_line, end_line] = comment
		number_of_words = len(comment_text.split())
		program_domain_concepts = find_program_domain_concepts(comment_text, program_domain_concepts_dict)
		problem_domain_concepts = find_problem_domain_concepts(comment_text, problem_domain_concepts_grams)
		# scope = find_scope(comment_text, start_line, end_line)
		# nlp_categories = find_nlp_categories(comment_text)
		is_copyright_or_license = is_copyright_or_license_comment(comment_text)
		is_bug_or_version_related = is_bug_or_version_related_comment(comment_text)
		is_build_related = is_build_related_comment(comment_text)
		is_system_spec_related = is_system_spec_related_comment(comment_text)
		is_authorship_related = is_author_name_comment(comment_text)
		is_email = is_email_comment(comment_text)
		is_date = is_date_comment(comment_text)
		is_todo = is_todo_comment(comment_text)
		is_junk = is_junk_comment(comment_text)
		
		entry = []
		if len(comment_text) != 0:
			entry.append(filename)
			entry.append(comment_text)
			entry.append(start_line)
			entry.append(end_line)
			entry.append(repr(number_of_words))
			entry.append(repr(program_domain_concepts))
			entry.append(repr(problem_domain_concepts))
			# entry.append(repr(scope))
			# entry.append(repr(nlp_categories))
			entry.append(repr(is_copyright_or_license))
			entry.append(repr(is_bug_or_version_related))
			entry.append(repr(is_build_related))
			entry.append(repr(is_system_spec_related))
			entry.append(repr(is_authorship_related))
			entry.append(repr(is_email))
			entry.append(repr(is_date))
			entry.append(repr(is_todo))
			entry.append(repr(is_junk))

			# categories
			categories = [False] * CATEGORY_COUNT
			if len(program_domain_concepts) == 0:
				categories[CAT_NO_PROGRAM_DOMAIN_CONCEPTS - 1] = True
			elif len(program_domain_concepts) < 3:
				categories[CAT_LOW_PROGRAM_DOMAIN_CONCEPTS - 1] = True
			else:
				categories[CAT_HIGH_PROGRAM_DOMAIN_CONCEPTS - 1] = True

			if len(problem_domain_concepts) == 0:
				categories[CAT_NO_PROBLEM_DOMAIN_CONCEPTS - 1] = True
			elif len(problem_domain_concepts) < 3:
				categories[CAT_LOW_PROBLEM_DOMAIN_CONCEPTS - 1] = True
			else:
				categories[CAT_HIGH_PROBLEM_DOMAIN_CONCEPTS - 1] = True

			categories[CAT_SHORT - 1] = (number_of_words < 4)
			categories[CAT_COPYRIGHT_LICENSE - 1] = is_copyright_or_license
			categories[CAT_DATE - 1] = is_date
			categories[CAT_EMAIL - 1] = is_email
			categories[CAT_BUG_VERSION - 1] = is_bug_or_version_related
			categories[CAT_AUTHOR_NAME - 1] = is_authorship_related
			categories[CAT_BUILD - 1] = is_build_related
			categories[CAT_SYSTEM_SPEC - 1] = is_system_spec_related
			categories[CAT_JUNK - 1] = is_junk

			categories_1_or_blank = []
			for category in categories:
				if category:
					categories_1_or_blank.append("1")
				else:
					categories_1_or_blank.append("")

			entry.extend(categories_1_or_blank)
			result.append(entry)
			
	return result

def get_column_headings():
	headings = [
			"Filename",
			"Comment text",
			"Start line",
			"End line",
			"No. of words",
			"Program Domain Concepts",
			"Problem Domain Concepts",
			# "Scope",
			# "NLP categories",
			"Copyright/License",
			"Bug/Fix/Patch/Version",
			"Build",
			"System spec",
			"Authorship",
			"Email",
			"Date",
			"Todo",
			"Junk"
			]
	headings.extend([("C" + repr(i)) for i in range(1, CATEGORY_COUNT + 1)])
	return headings


def get_problem_domain_concepts_list(pathname):
	problem_domain_concepts_file_path = os.path.join(pathname, PROBLEM_DOMAIN_CONCEPTS_FILE_NAME)
	if not os.path.isfile(problem_domain_concepts_file_path):
		print("Problem domain concepts file not found in folder " + pathname)
		return []
	else:
		problem_domain_concepts_file = open(problem_domain_concepts_file_path, "r")
		problem_domain_concepts_list = problem_domain_concepts_file.readlines()
		problem_domain_concepts_file.close()

		problem_domain_concepts_list = set([concept.strip() for concept in problem_domain_concepts_list])
		if "" in problem_domain_concepts_list:
			problem_domain_concepts_list.remove("")
		return list(problem_domain_concepts_list)

def process_file(filename, program_domain_concepts_dict, problem_domain_concepts_grams, comments_file):

	print ("Processing " + filename)
	result = extract_comments_info(filename, program_domain_concepts_dict, problem_domain_concepts_grams)

	for result_row in result:
		comments_file.writerow(result_row)

if __name__ == "__main__":

	if not os.path.isfile(PROGRAM_DOMAIN_CONCEPTS_FILE_PATH):
		print ("Program domain concepts file not found in cwd")

	program_domain_concepts_file = open(PROGRAM_DOMAIN_CONCEPTS_FILE_PATH, "rb")
	program_domain_concepts_dict = pickle.load(program_domain_concepts_file)

	if not os.path.isfile(OUTPUT_COMMENTS_FILE_PATH):
		comments_file = csv.writer(open(OUTPUT_COMMENTS_FILE_PATH, "w"), delimiter = '$', quoting = csv.QUOTE_MINIMAL)
		col_headings = get_column_headings()
		comments_file.writerow(col_headings)

	else:
		comments_file = csv.writer(open(OUTPUT_COMMENTS_FILE_PATH, "a"), delimiter = '$', quoting = csv.QUOTE_MINIMAL)

	for pathname in sys.argv[1:]:

		if os.path.isdir(pathname):

			problem_domain_concepts_grams = find_problem_domain_concepts_grams(get_problem_domain_concepts_list(pathname))
			print ("Problem domain concepts set: " + repr(problem_domain_concepts_grams))

			for root, directories, files in os.walk(pathname):
				for file in files: 
					if file.endswith(".c") or file.endswith(".cpp"):
						filename =  os.path.join(root, file)
						process_file(filename, program_domain_concepts_dict, problem_domain_concepts_grams, comments_file)

		else:
			print ("You must pass a folder name")