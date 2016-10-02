import urllib2
import base64
import xml.etree.ElementTree as ET
import json
from pprint import pprint
import heapq
import math
import sys

def information_retrieve(precision, total_docs):
  # the major functionality requiring user interactions
  stop_word = get_stop_word("stop_word.txt")

  input = raw_input('Type the word you want to search, separated by space: ')
  query = parse_first_query_to_dictionary(input)
  results = get_search_result(input)
  num = show_search_result(results)
  if num < total_docs:
    print "Not Enought Search Results. Program exit..."
    sys.exit(1)
  relevance_index = get_user_rating()

  while True:
    while not is_valid_index(relevance_index, total_docs):
      print "Invalid input! The input should be between 1 and {}".format(total_docs)
      relevance_index = get_user_rating()
    if len(relevance_index)/total_docs >= precision:
      print "All results are related. Program exit..."
      break
    if len(relevance_index) == 0:
      print "Find no qualified results at all. Program exit..."
    docs = construct_docs(results)
    query_next = get_next_top_query(query, relevance_index, stop_word, total_docs, docs)
    query_string = constrcut_string_from_list(query_next)
    results = get_search_result(query_string)
    print "====="
    print results
    print "====="
    show_search_result(results)
    relevance_index = get_user_rating()

def get_next_top_query(q_pre, relevance_index, stop_word, total_docs, docs):
  # tune the parameters here ~~~
  alpha = 0.9
  beta = 0.2
  gamma = 0.4
  top_num = min(total_docs, 5)

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
    construct_global_dictionary(doc, stop_word, dictionary)
    vector = construct_vector_from_doc(doc, stop_word)
    normalize(vector)
    if i in relevance_index:
      relevance_vectors.append(vector)
    else:
      irrelevance_vectors.append(vector)

  #calculate next q vector
  dummy_list = list()
  dummy_list.append(q_pre) # make sure q_pre has all the keys from the dictionary 
  q = dictionary_summation(
      vector_list_summation(dummy_list, dictionary), alpha,
      vector_list_summation(relevance_vectors, dictionary), beta/len(relevance_index),
      vector_list_summation(irrelevance_vectors, dictionary), -gamma/(total_docs-len(relevance_index)),
      dictionary)
  return q

def normalize(vector):
  denominator = 0
  for key in vector:
    denominator += (vector[key]*vector[key])
  for key in vector:
    vector[key] = vector[key]/denominator

def construct_vector_from_doc(doc, stop_word):
  vector = dict()
  for w in doc:
    if w not in stop_word:
      vector[w] = (vector[w]+1 if w in vector else 1)
  return vector 

def construct_global_dictionary(doc, stop_word, set):
  for w in doc:
    if w not in set and w not in stop_word:
      set.add(w)

def vector_list_summation(vector_list, dictionary):
  summation_vector = dict()
  for w in dictionary:
    summation_vector[w] = 0
    for vector in vector_list:
      summation_vector[w] += (vector[w] if w in vector else 0)
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

def get_stop_word(file_name):
  stop_word = set()
  with open(file_name) as f:
    for line in f:
        stop_word.add(line)
  return stop_word

def get_search_result(search_content):
  search_content_encode = search_content.replace(' ', '%20')
  bingUrl = "https://api.datamarket.azure.com/Bing/Search/Web?Query=%27"\
            +search_content_encode\
            +"%27&$top=10&$format=json"
  print "======"
  print "bingUrl"
  print bingUrl
  print "======="
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
  print "======"
  print "show_search_result called"
  print results
  print "======="
  index = 1
  for entry in results:
    print "{} : {}".format(index, entry['Title'].encode('ascii', 'ignore'))
    print entry['Description'].encode('ascii', 'ignore')
    index += 1
  return index

def get_user_rating():
  input = raw_input("Input all relevant entry number, separated by space: ")
  list = input.split()
  results = map(int, list)
  return results

def is_valid_index(list, total_docs):
  for num in list:
    if num not in range(1, total_docs+1):
      return False
  return True

def parse_first_query_to_dictionary(string):
  query = string.split()
  dic = dict()
  for w in query:
    dic[w] = 1
  return dic

def construct_docs(results):
  docs = list()
  index = 1
  for entry in results:
    string = entry['Title'].encode('ascii', 'ignore') + entry['Description'].encode('ascii', 'ignore')
    ## !!!!!!!!!!!!!!!!!!
    doc = ''.join(c for c in string if c.isalnum() or c.isspace()).split()
    docs.append(doc)
    index += 1
  return docs

def constrcut_string_from_list(string_list):
  return ' '.join(string_list)


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