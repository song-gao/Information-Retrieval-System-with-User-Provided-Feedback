import urllib2
import base64
import xml.etree.ElementTree as ET
import json
from pprint import pprint
import heapq
import math
import sys
import re

def information_retrieve(precision, total_docs):
  # the major functionality requiring user interactions
  stop_word = get_stop_word("stop_word.txt")

  input = raw_input('Type the word you want to search, separated by space:\n').lower()
  query_list = input.split()
  query = parse_query_list_to_dictionary(query_list)
  results = get_search_result(input)
  if not results:
    print "Find no results at the first time. Program exit..."
    sys.exit(1)
  show_search_result(results)
  relevance_index = get_user_rating(total_docs)
  if not relevance_index:
    print "Find no qualified results at all at the first time. Program exit..."
    sys.exit(1)
  while True:
    # ==========================  
    # probably need to delete this one
    if not relevance_index:
      print "Find no qualified results at all. Program exit..."
      break
    # ==========================
    if len(relevance_index)*1.0/total_docs >= precision:
      print "Presicion is achieved. Program exit..."
      break
    docs = construct_docs_from_results(results)
    query_list_next = get_next_top_query(query, relevance_index, stop_word, total_docs,docs)
    if is_query_same_as_last(construct_query_string_from_list(query), construct_query_string_from_list(parse_query_list_to_dictionary(query_list_next))):
      print "This query is the same as the last one. Program exit..."
      break
    query = parse_query_list_to_dictionary(query_list_next)
    query_string = construct_query_string_from_list(query_list_next)
    print "The calulated query this time is: "
    print query_string
    results = get_search_result(query_string)
    if not results:
      print "Find no results at this first time. Program exit..."
      sys.exit(1)
    show_search_result(results)
    relevance_index = get_user_rating(total_docs)

def get_next_top_query(q_pre, relevance_index, stop_word, total_docs, docs):
  # tune the parameters here ~~~
  alpha = 0.9
  beta = 0.2
  gamma = 0.4
  top_num = min(total_docs, 3)

  q = get_next_query_vector(q_pre, relevance_index, docs, stop_word, total_docs, alpha, beta, gamma)
  return dict_nlargest(q, top_num)

###################################################
#start of helper methods for get_next_top_query()
###################################################

def dict_nlargest(d,n):
  return heapq.nlargest(n ,d, key = lambda k: d[k])

def get_next_query_vector(q_pre, relevance_index, docs, stop_word, total_docs, alpha, beta, gamma):
  #docs are dict() retrived from last search result
  ## Note the relevance_index is from 0 not 1 !!!! take care when passing argument
  dictionary = set()
  relevance_vectors = list() 
  irrelevance_vectors = list()
  q = dict()

  for i in range(0, total_docs):
    doc = docs[i]
    construct_dict_from_doc(doc, stop_word, dictionary)
    vector = construct_vector_from_doc(doc, stop_word)
    normalize(vector)
    if i+1 in relevance_index:
      relevance_vectors.append(vector)
    else:
      irrelevance_vectors.append(vector)
  #calculate next q vector
  dummy_list = list()
  dummy_list.append(q_pre) # make sure q_pre has all the keys from the dictionary 
  q = dictionary_summation(
      vector_list_summation(dummy_list, dictionary), alpha*1.0,
      vector_list_summation(relevance_vectors, dictionary), 1.0*beta/len(relevance_index),
      vector_list_summation(irrelevance_vectors, dictionary), -1.0*gamma/(total_docs-len(relevance_index)),
      dictionary)
  return q

def normalize(vector):
  denominator = 0
  for key in vector:
    denominator += vector[key]*vector[key]
  for key in vector:
    vector[key] = 1.0*vector[key]/denominator

def construct_vector_from_doc(doc, stop_word):
  vector = dict()
  for w in doc:
    if w not in stop_word:
      vector[w] = vector[w]+1 if w in vector else 1
  return vector 

def construct_dict_from_doc(doc, stop_word, set):
  for w in doc:
    if w not in set and w not in stop_word:
      set.add(w)

def vector_list_summation(vector_list, dictionary):
  summation_vector = dict()
  for w in dictionary:
    summation_vector[w] = 0
    for vector in vector_list:
      summation_vector[w] += (vector[w] if w in vector else 0)
      #summation_vector[w] += [vector[w],0][w in vector]
        
  return summation_vector

def dictionary_summation(dict1, coefficient1, dict2, coefficient2, dict3, coefficient3, dictionary):
  res = dict()
  for w in dictionary:
    res[w] = 0
    res[w] += (coefficient1*dict1[w] + coefficient2*dict2[w] + coefficient3*dict3[w])
  return res

###################################################
#end of helper methods for get_next_top_query()
###################################################


###################################################
#start of helper methods for information_retrieve()
###################################################
def is_query_same_as_last(query1, query2):
  return set(query2) == (set(query1) & set(query2))

def construct_query_string_from_list(list):
  return ' '.join(list)

def get_stop_word(file_name):
  stop_word = set()
  with open(file_name) as f:
    for line in f:
        stop_word.add(line.rstrip())
  return stop_word

def get_search_result(search_content):
  search_content_encode = search_content.replace(' ','%20')
  bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=%27"\
            +search_content_encode\
            +"%27&$top=10&$format=json"
  #Provide your account key here
  accountKey = "y/Le5zhlILnVq7+cJiEE/2adH7pL7s7kpNAkZ/mxLt0"

  accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
  headers = {'Authorization': 'Basic ' + accountKeyEnc}
  req = urllib2.Request(bingUrl, headers = headers)
  response = urllib2.urlopen(req)
  content = response.read()
  content_json = json.loads(content)
  return  content_json['d']['results']

def show_search_result(results):
  index = 1
  for entry in results:
    print "{} : {}".format(index, entry['Title'].encode('utf8'))
    print entry['Description'].encode('utf8')
    index += 1
  print "\n"

def get_user_rating(total_docs):
  input = raw_input("Input all relevant entry number, separated by space:\n").lower()
  input_list = input.split()
  while not is_valid_user_rating(input_list, total_docs):
    print "Invalid input! The input should be between 1 and {}".format(total_docs)
    input = raw_input("Input all relevant entry number, separated by space:\n").lower()
    input_list = input.split()
  results = (map(int, input_list) if input_list else list())
  return results

def is_valid_user_rating(input_list, total_docs):
  if len(input_list) == 0:
    return True
  for element in input_list: 
    try:
      int(element)
    except ValueError:
      return False
  for element in map(int, input_list):
    if element < 1 or element > total_docs:
      return False
  return True

def parse_query_list_to_dictionary(query):
  dic = dict()
  for w in query:
    dic[w] = 1
  return dic

def construct_docs_from_results(results):
  regex = re.compile('[^a-zA-Z]')
  docs = list()
  index = 1
  for entry in results:
    string = (entry['Title'].encode('utf8') + entry['Description'].encode('utf8')).lower()
    print string

    doc = (''.join(c for c in string if c.isalpha() or c.isspace())).split()
    index += 1
    docs.append(doc)
  return docs


###################################################
#end of helper methods for information_retrieve()
###################################################

if __name__ == "__main__":

  if len(sys.argv) != 3:
      print "Should pass exactly 2 arguments: precision and total_docs"
      sys.exit(1)
  precision = float(sys.argv[1])
  total_docs = int(sys.argv[2])

  if precision <= 0 or precision >= 1:
      print "Precision must be a number between 0 and 1"
      sys.exit(1)
  if not isinstance(total_docs, (int, long)) or total_docs <= 0:
    print "total number of docs should be a positive integer"

  information_retrieve(precision, total_docs)