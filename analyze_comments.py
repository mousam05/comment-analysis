import sys
import re
import os
import pickle
import csv

from nltk.stem import PorterStemmer

from nltk.tag.stanford import StanfordPOSTagger
from nltk.parse.stanford import StanfordDependencyParser

ps = PorterStemmer()
EDIT_DISTANCE_THRESHOLD = 2

COL_TYPE = 7
COL_LINE_BEGIN = 9
COL_LINE_END = 10

ROOT_PATH = "/home/mousam/Downloads/mtp2"
VOCABDICT_PATH = ROOT_PATH + "/ParserCheck/VocabDictionary.csv"
CORPUS_PATH = ROOT_PATH + "/codebases/corpus.csv"

stanford_pos_tagger = StanfordPOSTagger('english-bidirectional-distsim.tagger')
stanford_dep_parser = StanfordDependencyParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")

def get_edit_distance(str1, str2, m, n): 
	dp = [[0 for x in range(n+1)] for x in range(m+1)] 
  
	for i in range(m+1): 
		for j in range(n+1): 
  
			if i == 0: 
				dp[i][j] = j
  
			elif j == 0: 
				dp[i][j] = i
  
			elif str1[i-1] == str2[j-1]: 
				dp[i][j] = dp[i-1][j-1] 

			else: 
				dp[i][j] = 1 + min(dp[i][j-1],        # Insert substr
								   dp[i-1][j],        # Remove 
								   dp[i-1][j-1])    # Replace 
  
	return dp[m][n] 

def get_ngrams(tokens, n):
	result = []
	k = len(tokens)
	for i in range(0, k-n+1):
		ngram = ''
		for j in range(i, i+n):
			ngram = ngram + ' ' + tokens[j]
		result.append(ngram[1:])
	return result

def find_comment_concepts(comment, data_dict):
	tokens = comment.split()
	bigrams = get_ngrams(tokens, 2)
	trigrams = get_ngrams(tokens, 3)

	tokens.extend(bigrams)
	tokens.extend(trigrams)

	concepts = {}

	for token in tokens:
		matched = []
		for row in data_dict:
			#stemmed_token = ps.stem(token)
			stemmed_token = token
			if get_edit_distance(stemmed_token.lower(), row[0].lower(),
				len(stemmed_token), len(row[0])) <= EDIT_DISTANCE_THRESHOLD:
				matched.append(row)

		if len(matched):
			concepts[token] = matched

	return concepts

def get_symbol_types_and_scopes(symbols_db):
	tables = list(symbols_db.values())
	result = []
	for table in tables:
		for table_row in table[1]:
			result.append((table_row[COL_TYPE], table_row[COL_LINE_BEGIN], table_row[COL_LINE_END]))

	return result

def find_comment_scope(comment, fr_line, to_line, symbols_db):
	types_scopes = get_symbol_types_and_scopes(symbols_db)


	blocktypes = ['CompoundStmt', 'Function', 'IfStmt', 'WhileStmt',
		'ForStmt', 'DoStmt', 'SwitchStmt', 'CaseStmt']

	max_line = -1
	line_nos = set()
	for entry in types_scopes:
		line_nos.update([entry[1], entry[2]])
		if(max_line < entry[1]):
			max_line = entry[1]
		if(max_line < entry[2]):
			max_line = entry[2]

	#case 1: comment and code on same line

	#give priority to block types
	for entry in types_scopes:
		if fr_line == entry[1] or fr_line == entry[2]:
			if entry[0] in blocktypes:
				return (entry[1], entry[2])

	#if block type is not found, consider other types
	for entry in types_scopes:
		if fr_line == entry[1] or fr_line == entry[2]:
			return (entry[1], entry[2])

	#case 2: comment and code on different lines
	fr_line_new = to_line + 1

	while fr_line_new not in line_nos and fr_line_new < max_line:
		fr_line_new = fr_line_new + 1

	for entry in types_scopes:
		if fr_line_new == entry[1] or fr_line_new == entry[2]:
			if entry[0] in blocktypes:
				return (entry[1], entry[2])

	for entry in types_scopes:
		if fr_line_new == entry[1] or fr_line_new == entry[2]:
			return (entry[1], entry[2])

	# default case: scope is same as comment start and end lines
	return (fr_line, to_line)


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
def find_comment_nlp_categories(comment):
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

# extracts all comments from a c/cpp file using regexes,
# returns starting line no, ending line no, comment text
def find_comments(text):
	pattern = re.compile( r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE).findall(text)
	pattern1 = re.compile( r'//.*?$|/\*.*?\*/', re.DOTALL | re.MULTILINE)
	l = [(m.start(0), m.end(0)) for m in re.finditer(pattern1, text)]		
	pos = 0
	fr = []
	to = []
	for item in pattern:
		location = l[pos][0]
		s = text[:location+1]
		lineNo1 = s.count('\n') + 1
		location1 = l[pos][1]
		s = text[:location1 + 1]
		lineNo2 = s.count('\n')
		fr.append(lineNo1)
		to.append(lineNo2)
		print ("lineNo : ",lineNo1 , " to " , lineNo2  , " matched : " , item)
		pos = pos + 1
		
	return fr, to, pattern


def extract_comments_info(filename, symbols_db, data_dict):
	codefile = open(filename,'r')
	lines=codefile.read()
	result = []
	fr , to , list_of_comments = find_comments(lines)
	pos = 0
	for comment in list_of_comments:

		if comment[0:2] == "//":
			comment_to_write = comment[2:]
		else:
			comment_to_write = comment[2:-2]
			
		l = []

		comment_to_write = comment_to_write.strip()
		comment_tokens = comment_to_write.split()
		concepts = find_comment_concepts(comment_to_write, data_dict)
		scope = find_comment_scope(comment_to_write, fr[pos], to[pos], symbols_db)
		nlp_categories = find_comment_nlp_categories(comment_to_write)

		if len(comment_to_write)!=0:
			l.append(os.path.abspath(filename))
			l.append(fr[pos])
			l.append(to[pos])
			l.append(comment_to_write)
			#l.append(repr(comment_tokens))
			l.append(repr(concepts))
			l.append(repr(nlp_categories))
			l.append(repr(scope))
			result.append(l)
			
		pos = pos + 1
	return result


def process_file(filename, data_dict, corpus):
	if not (filename.endswith(".c") or filename.endswith(".cpp")):
		print ("Skipping " + filename)
		return

	if os.path.isfile(filename + ".symbols"):
		with open(filename + ".symbols", "rb") as fp:
			symbols_db = pickle.load(fp)
			fp.close()
	else:
		symbols_db = {}
		print ("Warning: Symbols file not found for " + filename)

	result = extract_comments_info(filename, symbols_db, data_dict)

	for result_row in result:
		corpus.writerow(result_row)


if __name__ == "__main__":

	data_dict = csv.reader(open(VOCABDICT_PATH), delimiter=',')
	corpus = csv.writer(open(CORPUS_PATH, "a"), delimiter='$', quoting=csv.QUOTE_MINIMAL)

	for pathname in sys.argv[1:]:

		if pathname.endswith("/"):
			pathname = pathname[:-1]

		if os.path.isdir(pathname) == True:

			files = os.listdir(pathname)
			for file in files:
				filename = pathname + "/" + file
				process_file(filename, data_dict, corpus)

		else:
			process_file(pathname, data_dict, corpus)