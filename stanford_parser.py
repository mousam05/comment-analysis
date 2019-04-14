from nltk.tag.stanford import StanfordPOSTagger
from nltk.tag import StanfordNERTagger
from nltk.parse.stanford import StanfordParser, StanfordDependencyParser

stanford_pos_tagger = StanfordPOSTagger('english-bidirectional-distsim.tagger')
st_ner = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
stanford_parser = StanfordParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
stanford_dep_parser = StanfordDependencyParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")

str = ""
while True:
	str = input ("Enter a string: ")
	if str == "0":
		break

	result = stanford_pos_tagger.tag(str.split())
	print ("Postagger: " + repr(result))

	result = st_ner.tag(str.split())
	print ("NERtagger: " + repr(result))

	result = list(stanford_parser.raw_parse(str))
	print ("Parser: " + repr(result))

	result = [list(parse.triples()) for parse in stanford_dep_parser.raw_parse(str)]
	print ("DepParser: " + repr(result))




