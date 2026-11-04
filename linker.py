import time

from SPARQLWrapper import JSON, SPARQLWrapper

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "KNU-SemanticWeb-Lab1/1.0 (educational project)"

LOOKUP = """
SELECT ?item WHERE {
  ?item rdfs:label "%s"@en ;
        wdt:P31/wdt:P279* wd:%s .
}
LIMIT 1
"""

DETAILS = """
SELECT ?label ?inception ?country ?countryLabel WHERE {
  wd:%s rdfs:label ?label .
  OPTIONAL { wd:%s wdt:P571 ?inception }
  OPTIONAL { wd:%s wdt:P17 ?country . ?country rdfs:label ?countryLabel .
             FILTER (lang(?countryLabel) = "en") }
  FILTER (lang(?label) = "en")
}
LIMIT 1
"""


class WikidataLinker:
    STUDIO_CLASS = "Q210167"
    GAME_CLASS = "Q7889"

    def __init__(self, pause=2):
        self.client = SPARQLWrapper(ENDPOINT, agent=USER_AGENT)
        self.client.setReturnFormat(JSON)
        self.client.setTimeout(60)
        self.pause = pause

    def _ask(self, query):
        self.client.setQuery(query)
        return self.client.query().convert()["results"]["bindings"]

    def find(self, label, class_id):
        rows = self._ask(LOOKUP % (label, class_id))
        time.sleep(self.pause)
        return rows[0]["item"]["value"] if rows else None

    def describe(self, entity_id):
        rows = self._ask(DETAILS % (entity_id, entity_id, entity_id))
        time.sleep(self.pause)
        return rows[0] if rows else {}

    def attach(self, knowledge_graph, pairs):
        linked = []
        for kind, label, class_id in pairs:
            uri = self.find(label, class_id)
            if uri is None:
                print(f"  не знайдено у Wikidata: {label}")
                continue
            knowledge_graph.link_to(kind, label, uri)
            linked.append((kind, label, uri))
            print(f"  {label:34s} -> {uri}")
        return linked
