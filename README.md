# comment-analysis
Code for my MTech Project (MTP) on analysis of comments in C/C++ programs. (IIT Kharagpur, Spring 2019)

The aim of this project is to assign a usefulness score to each comment.

## Setting up

This project is written in Python 3.

The following python packages must be installed. (You can do this by `pip3 install <package-name>`.)
* editdistance
* nltk

## Running on a code repo

#### Problem domain concepts file:

The C/C++ code repository on which you want to run comment analysis must have a `ProblemDomainConcepts.txt` file in the top-level directory of the repository, containing the relevant problem domain words and phrases corresponding to that repository.

For example, for this [GenePrediction](https://github.com/AceRoqs/GenePrediction) repo based on computational biology, the concepts file might look somewhat like this:

>amino acid  
residue  
hemoglobin  
haemoglobin  
taxonomic  
beta chain  
insulin  
peptide  
nucleotide  
protein  
gene  
codon  
genome  
viterbi  
genomic background  
base pair

#### Running the project

Run this command:  
`python3 analyze_comments.py <path-to-repo>`

For example,  
`python3 analyze_comments.py repos/GenePrediction/`

#### Output

A `comments.csv` file will be generated in the current directory, containing the extracted comments along with rich metadata information, including the following fields:  
* Filename
* Comment text, Start line, End line
* Number of words
* Program domain concepts extracted from a comment
* Problem domain concepts extracted from a comment
* Whether a comment contains one or more of the following kinds of data:
  * Copyright/License information
  * Build instructions
  * Code author related info - name/email/contact
  * Date related info - modified on/created on
  * TODO information
  * Junk (strings of symbols without any alphanumeric data)
  * System requirements (OS, GPU, RAM, Cache, server etc)
  * Bug/Version related information
  
#### Understanding categories and usefulness score

TODO
