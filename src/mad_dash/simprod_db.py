import os
from os.path import join
from pymongo import MongoClient

f = open(join(os.environ['HOME'],'.mongo'))
url = "mongodb://DBadmin:%s@mongodb-simprod.icecube.wisc.edu" % f.readline().strip()
spdb = MongoClient(url)