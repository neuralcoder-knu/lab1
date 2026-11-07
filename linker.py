import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import certifi
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

ENDPOINT = "https://query.wikidata.org/sparql"
ACTION_API = "https://www.wikidata.org/w/api.php"
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
ORDER BY ?inception
LIMIT 1
"""


SPARQL_UNAVAILABLE = (urllib.error.URLError, EndPointInternalError, TimeoutError)


class WikidataActionApi:
    """Запасний шлях через Action API, коли SPARQL-сервіс недоступний."""

    def _get(self, **params):
        url = ACTION_API + "?" + urllib.parse.urlencode({"format": "json", **params})
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    def _claims(self, entity_ids):
        entities = self._get(action="wbgetentities", ids="|".join(entity_ids), props="claims")
        return {key: value.get("claims", {}) for key, value in entities["entities"].items()}

    @staticmethod
    def _values(claims, prop):
        for claim in claims.get(prop, []):
            value = claim["mainsnak"].get("datavalue", {}).get("value")
            if value and claim.get("rank") != "deprecated":
                yield value

    def find(self, label, class_id):
        found = self._get(action="wbsearchentities", search=label, language="en", limit=10)
        ids = [item["id"] for item in found["search"] if item.get("label") == label]
        if not ids:
            return None
        claims = self._claims(ids)
        for entity_id in ids:
            if class_id in (value["id"] for value in self._values(claims[entity_id], "P31")):
                return f"http://www.wikidata.org/entity/{entity_id}"
        return None

    def describe(self, entity_id):
        claims = self._claims([entity_id])[entity_id]
        dates = sorted(self._normalise(value["time"]) for value in self._values(claims, "P571"))
        return {"inception": {"value": dates[0]}} if dates else {}

    @staticmethod
    def _normalise(value):
        year, month, day = re.match(r"\+?(\d{4})-(\d{2})-(\d{2})T", value).groups()
        return f"{year}-{max(month, '01')}-{max(day, '01')}T00:00:00Z"


class WikidataLinker:
    STUDIO_CLASS = "Q210167"
    GAME_CLASS = "Q7889"

    def __init__(self, pause=2):
        self.client = SPARQLWrapper(ENDPOINT, agent=USER_AGENT)
        self.client.setReturnFormat(JSON)
        self.client.setTimeout(60)
        self.pause = pause
        self.fallback = None

    def _ask(self, query):
        self.client.setQuery(query)
        return self.client.query().convert()["results"]["bindings"]

    def _switch_to_fallback(self, error):
        self.fallback = WikidataActionApi()
        code = getattr(error, "code", type(error).__name__)
        print(f"  SPARQL-сервіс Wikidata недоступний ({code}), використовую Action API")

    def find(self, label, class_id):
        if not self.fallback:
            try:
                rows = self._ask(LOOKUP % (label, class_id))
                time.sleep(self.pause)
                return rows[0]["item"]["value"] if rows else None
            except SPARQL_UNAVAILABLE as error:
                self._switch_to_fallback(error)
        return self.fallback.find(label, class_id)

    def describe(self, entity_id):
        if not self.fallback:
            try:
                rows = self._ask(DETAILS % (entity_id, entity_id, entity_id))
                time.sleep(self.pause)
                return rows[0] if rows else {}
            except SPARQL_UNAVAILABLE as error:
                self._switch_to_fallback(error)
        return self.fallback.describe(entity_id)

    def attach(self, knowledge_graph, pairs):
        linked = []
        for kind, label, class_id, wikidata_label in pairs:
            uri = self.find(wikidata_label, class_id)
            if uri is None:
                print(f"  не знайдено у Wikidata: {wikidata_label}")
                continue
            knowledge_graph.link_to(kind, label, uri)
            inception = self.describe(uri.rsplit("/", 1)[-1]).get("inception")
            if inception:
                knowledge_graph.add_inception(uri, inception["value"])
            linked.append((kind, label, uri))
            print(f"  {label:34s} -> {uri}")
        return linked
