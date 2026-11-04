import pathlib

from catalog import default_catalog
from graph import KnowledgeGraph
from linker import WikidataLinker
from queries import BROKEN, FIXED, QueryLibrary
from render import GraphRenderer

TURTLE = "games.ttl"
JSONLD = "games.jsonld"

EXTERNAL = [
    ("studio", "GSC Game World", WikidataLinker.STUDIO_CLASS),
    ("studio", "CD Projekt Red", WikidataLinker.STUDIO_CLASS),
    ("game", "The Witcher 3: Wild Hunt", WikidataLinker.GAME_CLASS),
]

MANUAL_EDIT = """
<https://example.org/games/game/cyberpunk-2077>
    schema:gamePlatform "GeForce Now"@uk ;
    schema:inLanguage "uk" .
"""

COMBINED = """
PREFIX gm:     <https://example.org/games/>
PREFIX schema: <https://schema.org/>
PREFIX owl:    <http://www.w3.org/2002/07/owl#>
PREFIX wdt:    <http://www.wikidata.org/prop/direct/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?studio ?inception (COUNT(?game) AS ?games) WHERE {
  ?node a gm:Studio ;
        schema:name ?studio ;
        owl:sameAs ?external .
  ?external wdt:P571 ?inception .
  ?game gm:developedBy ?node .
}
GROUP BY ?studio ?inception
ORDER BY ?inception
"""


class Lab:
    def __init__(self):
        self.catalog = default_catalog()
        self.kg = KnowledgeGraph(self.catalog)

    def report_catalog(self):
        print("КАТАЛОГ")
        for key, value in self.catalog.summary().items():
            print(f"  {key}: {value}")
        print()

    def report_graph(self):
        print("ГРАФ")
        for key, value in self.kg.statistics().items():
            print(f"  {key}: {value}")
        print()

    def serialise(self):
        self.kg.save(TURTLE, "turtle")
        self.kg.save(JSONLD, "json-ld")
        print(f"серіалізовано: {TURTLE}, {JSONLD}\n")

    def apply_manual_edit(self):
        before = len(self.kg.graph)
        with open(TURTLE, "a", encoding="utf-8") as handle:
            handle.write(MANUAL_EDIT)
        reread = KnowledgeGraph(self.catalog)
        reread.graph.parse(TURTLE, format="turtle")
        print("РУЧНА ПРАВКА")
        print(f"  до правки: {before} трійок")
        print(f"  після повторного читання: {len(reread.graph)} трійок\n")

    def show_entity(self, kind, label):
        node = self.kg.uri(kind, label)
        print(f"ТРІЙКИ СУТНОСТІ {label}")
        for predicate, obj in sorted(self.kg.graph.predicate_objects(node), key=str):
            short = str(predicate).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            print(f"  {short:18s} -> {str(obj).replace(str(self.kg.ns), 'gm:')[:70]}")
        print()

    def show_sample(self, limit=12):
        print(f"ПЕРШІ {limit} ТРІЙОК")
        for index, (subject, predicate, obj) in enumerate(self.kg.graph):
            if index >= limit:
                break
            left = str(subject).replace(str(self.kg.ns), "gm:")
            middle = str(predicate).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            print(f"  {left[:44]:46s} {middle:16s} {str(obj)[:44]}")
        print()

    def visualise(self):
        renderer = GraphRenderer(self.kg)
        renderer.to_png("graph_full.png")
        renderer.to_png("graph_core.png", skip=("Platform", "Genre"))
        renderer.to_html("graph.html")
        print("візуалізація: graph_full.png, graph_core.png, graph.html\n")

    def run_queries(self):
        QueryLibrary().run_all(self.kg.graph)

    def show_error_example(self):
        print("=" * 78)
        print("ПОМИЛКОВИЙ І ВИПРАВЛЕНИЙ ПРИКЛАД")
        print("-" * 78)
        for query in (BROKEN, FIXED):
            rows = query.run(self.kg.graph)
            print(f"  {query.title}: {query.purpose}")
            print(f"  рядків: {len(rows)}")
            for row in rows[:3]:
                print("     " + " | ".join(str(value) for value in row))
            print()

    def link_external(self):
        print("ЗВ'ЯЗОК ІЗ WIKIDATA")
        try:
            linked = WikidataLinker().attach(self.kg, EXTERNAL)
        except Exception as error:
            print(f"  Wikidata недоступна: {type(error).__name__}")
            return
        if not linked:
            return
        self.kg.save("games_linked.ttl", "turtle")
        print("\nОБ'ЄДНАНИЙ ЗАПИТ")
        for row in self.kg.graph.query(COMBINED):
            print("  " + " | ".join(str(value) for value in row))
        print()


if __name__ == "__main__":
    lab = Lab()
    lab.report_catalog()
    lab.kg.build()
    lab.report_graph()
    lab.serialise()
    lab.apply_manual_edit()
    lab.show_sample()
    lab.show_entity("game", "S.T.A.L.K.E.R.: Shadow of Chernobyl")
    lab.visualise()
    lab.run_queries()
    lab.show_error_example()
    lab.link_external()
    print("готово:", ", ".join(sorted(p.name for p in pathlib.Path(".").glob("games*.ttl"))))
