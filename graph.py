import re
import unicodedata

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, RDFS, XSD

BASE = "https://example.org/games/"
SCHEMA = Namespace("https://schema.org/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")


class Slugger:
    CYRILLIC = {
        "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
        "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
        "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "",
        "ю": "iu", "я": "ia", "'": "",
    }

    @classmethod
    def transliterate(cls, value):
        return "".join(cls.CYRILLIC.get(char, char) for char in value.lower())

    @classmethod
    def make(cls, value):
        latin = cls.transliterate(value)
        folded = unicodedata.normalize("NFKD", latin)
        ascii_only = folded.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^A-Za-z0-9]+", "-", ascii_only).strip("-").lower()


class KnowledgeGraph:
    def __init__(self, catalog, base=BASE):
        self.catalog = catalog
        self.ns = Namespace(base)
        self.graph = Graph()
        self._bind_namespaces()

    def _bind_namespaces(self):
        self.graph.bind("gm", self.ns)
        self.graph.bind("schema", SCHEMA)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("owl", OWL)
        self.graph.bind("wdt", WDT)

    def uri(self, kind, value):
        return self.ns[f"{kind}/{Slugger.make(value)}"]

    def _declare_classes(self):
        classes = {
            "Game": SCHEMA.VideoGame,
            "Studio": SCHEMA.Organization,
            "Publisher": SCHEMA.Organization,
            "Platform": SCHEMA.Thing,
            "Genre": SCHEMA.Thing,
            "Person": SCHEMA.Person,
            "Country": SCHEMA.Country,
        }
        for name, parent in classes.items():
            node = self.ns[name]
            self.graph.add((node, RDF.type, RDFS.Class))
            self.graph.add((node, RDFS.subClassOf, parent))
            self.graph.add((node, RDFS.label, Literal(name, lang="en")))

    def _declare_properties(self):
        properties = [
            ("developedBy", "Game", "Studio"),
            ("publishedBy", "Game", "Publisher"),
            ("releasedOn", "Game", "Platform"),
            ("hasGenre", "Game", "Genre"),
            ("foundedBy", "Studio", "Person"),
            ("basedIn", "Studio", "Country"),
            ("sequelOf", "Game", "Game"),
        ]
        for name, domain, value_range in properties:
            node = self.ns[name]
            self.graph.add((node, RDF.type, RDF.Property))
            self.graph.add((node, RDFS.domain, self.ns[domain]))
            self.graph.add((node, RDFS.range, self.ns[value_range]))

        literals = [("releaseYear", "Game", XSD.integer), ("foundingYear", "Studio", XSD.integer)]
        for name, domain, datatype in literals:
            node = self.ns[name]
            self.graph.add((node, RDF.type, RDF.Property))
            self.graph.add((node, RDFS.domain, self.ns[domain]))
            self.graph.add((node, RDFS.range, datatype))

    def _named_node(self, kind, label, class_name):
        node = self.uri(kind, label)
        self.graph.add((node, RDF.type, self.ns[class_name]))
        self.graph.add((node, SCHEMA.name, Literal(label, lang="uk")))
        self.graph.add((node, RDFS.label, Literal(label, lang="uk")))
        return node

    def _add_studios(self):
        for studio in self.catalog.studios:
            node = self._named_node("studio", studio.name, "Studio")
            self.graph.add((node, DCTERMS.title, Literal(studio.name, lang="uk")))
            self.graph.add((node, self.ns.foundingYear,
                            Literal(studio.founded, datatype=XSD.integer)))

            country = self._named_node("country", studio.country, "Country")
            self.graph.add((node, self.ns.basedIn, country))

            person = self.uri("person", studio.founder)
            self.graph.add((person, RDF.type, self.ns.Person))
            self.graph.add((person, FOAF.name, Literal(studio.founder, lang="uk")))
            self.graph.add((person, RDFS.label, Literal(studio.founder, lang="uk")))
            self.graph.add((node, self.ns.foundedBy, person))

    def _add_games(self):
        for game in self.catalog.games:
            node = self._named_node("game", game.title, "Game")
            self.graph.add((node, DCTERMS.title, Literal(game.title, lang="uk")))
            self.graph.add((node, self.ns.releaseYear,
                            Literal(game.year, datatype=XSD.integer)))
            self.graph.add((node, SCHEMA.datePublished,
                            Literal(str(game.year), datatype=XSD.gYear)))

            studio = next(s for s in self.catalog.studios if s.key == game.studio)
            self.graph.add((node, self.ns.developedBy, self.uri("studio", studio.name)))

            publisher = self._named_node("publisher", game.publisher, "Publisher")
            self.graph.add((node, self.ns.publishedBy, publisher))

            for platform in game.platforms:
                target = self._named_node("platform", platform, "Platform")
                self.graph.add((node, self.ns.releasedOn, target))

            for genre in game.genres:
                target = self._named_node("genre", genre, "Genre")
                self.graph.add((node, self.ns.hasGenre, target))

            if game.sequel_of:
                earlier = next(g for g in self.catalog.games if g.key == game.sequel_of)
                self.graph.add((node, self.ns.sequelOf, self.uri("game", earlier.title)))

    def _merge_same_organisations(self):
        studio_names = {studio.name for studio in self.catalog.studios}
        for name in sorted(studio_names & set(self.catalog.publishers())):
            self.graph.add((self.uri("studio", name), OWL.sameAs, self.uri("publisher", name)))

    def build(self):
        self._declare_classes()
        self._declare_properties()
        self._add_studios()
        self._add_games()
        self._merge_same_organisations()
        return self

    def link_to(self, local_kind, local_label, external_uri):
        self.graph.add((self.uri(local_kind, local_label), OWL.sameAs, URIRef(external_uri)))

    def add_inception(self, external_uri, inception):
        self.graph.add((URIRef(external_uri), WDT.P571, Literal(inception, datatype=XSD.dateTime)))

    def save(self, path, fmt="turtle"):
        self.graph.serialize(path, format=fmt)
        return path

    def statistics(self):
        own_types = {t for t in self.graph.objects(None, RDF.type) if str(t).startswith(str(self.ns))}
        own_predicates = {p for p in self.graph.predicates() if str(p).startswith(str(self.ns))}
        instances = {s for s in self.graph.subjects(RDF.type, None)
                     if str(s).startswith(str(self.ns)) and s not in own_types}
        return {
            "трійок": len(self.graph),
            "типів сутностей": len(own_types),
            "екземплярів": len(instances),
            "типів зв'язків": len(own_predicates),
        }
