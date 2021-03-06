#!/usr/bin/env python
# coding=utf8

import logging
from rdflib.graph import Dataset
from rdflib.term import URIRef
from rdflib.namespace import Namespace, OWL, RDF, RDFS
from uuid import uuid4

# @prefix spindle: <http://bbcarchdev.github.io/ns/spindle#> .
SPINDLE = Namespace('http://bbcarchdev.github.io/ns/spindle#')

class Rulebase:
  def __init__(self, dataset):
    self.graph = dataset.graph('rulebase.ttl')
    self.predicates = {
      URIRef(RDF.type): True,
      URIRef(OWL.sameAs): True,
    }
    for s, p, o in self.graph.triples((None, URIRef(SPINDLE.expressedAs) , None)):
      self.predicates[s] = True
      self.predicates[o] = True
      print(s)
      print(o)

logging.basicConfig(
  format="%(asctime)-15s [%(levelname)-7s] %(message)s",
  level=logging.INFO
)
logger = logging.getLogger(__file__)


def load_dataset(rdf_file, file_type='nquads'):
  """ load_graph( rdf_file )
    Load the graph from the supplied (nq) file.
    Returns a Dataset()
  """
  logger.info('load_graph("{}")'.format(rdf_file))
  dataset = Dataset()
  dataset.parse(rdf_file, format=file_type, publicID=rdf_file)
  graphs = len([g for g in dataset.graphs()])
  triples = sum([len(g) for g in dataset.graphs()])
  for graph in dataset.graphs():
    logger.info("load_graph: graph: {} {}".format(str(graph), len(graph)))
  logger.info('load_graph: graphs: {}, triples: {}'.format(graphs, triples))
  return dataset


def dump_dataset(dataset):
  for g in dataset.graphs():
    logger.info("graph : {}".format(g))
    for s, p, o in dataset.graph(g):
      logger.info("triple : {} {} {}".format(s, p, o))

def validate(dataset):
  """
    Check the licenses in the dataset
  """
  logger.info("validate: start")
  for g in dataset.graphs():
    rs = dataset.graph(g).query(
      """
      PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
      PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX cc: <http://creativecommons.org/ns#>
      PREFIX doap: <http://usefulinc.com/ns/doap#>
      PREFIX dct: <http://purl.org/dc/terms/>
      SELECT ?x ?type ?license WHERE {
          ?x rdf:type ?type .
          ?x ?licensetype ?license
      } VALUES ?licensetype {cc:license doap:license dct:license}
      """
    )
    for s, p, o in rs:
      logger.info("license : {}".format(str(o)))
  logger.info("validate: end")

def strip(dataset, rulebase):
  """
    Process a graph, stripping out triples using predicates which don't appear in the rule-base
    it is also meant to remove literals with a language that is not used by Spindle
  """
  logger.info("strip: start: {} triples".format(sum([len(g) for g in dataset.graphs()])))
  for g in dataset.graphs():
    for s, p, o in dataset.graph(g):
      if p not in rulebase.predicates:
        logger.info("strip : {} {} {}".format(s, p, o))
        dataset.remove( (s, p, o) )
      else:
        logger.info("leave : {} {} {}".format(s, p, o))
  logger.info("strip: end: {} triples".format(sum([len(g) for g in dataset.graphs()])))


def correlate(dataset):
  logger.info("correlate: start")
  proxy = {}
  index = {}
  for g in dataset.graphs():
    # TODO Handle rulebase equivalents to sameAs
    for s, p, o in dataset.graph(g).triples((None, OWL.sameAs, None)):
      logger.info("correlate: {} {}".format(s, o))
      # See if a proxy exists for <s> or <o>
      uuid = proxy.get(s) or proxy.get(o)
      # Generate proxy if not
      if uuid:
        logger.info("proxy: found: {}".format(uuid))
      else:
        uuid = uuid4()
        logger.info("proxy: create: {}".format(uuid))
      # Add <s> sameAs <proxy> triple
      proxy[s] = uuid
      # Add <o> sameAs <proxy> triple
      proxy[o] = uuid
      if uuid not in index:
        index[uuid] = []
      index[uuid].append(s)
      index[uuid].append(o)
  for uuid in index:
    logger.info("index: {} {}".format(uuid, index[uuid]))
  logger.info("correlate: end")


def generate(dataset):
  logger.info("generate: start")
  logger.info("generate: end")


dataset = load_dataset('likeit.nq')
#dataset = load_dataset('Iceland.nq')
#dataset = load_dataset('about.rdf', file_type='xml')
rulebase = Rulebase(load_dataset('rulebase.ttl', 'turtle'))

validate(dataset)
strip(dataset, rulebase)
correlate(dataset)
