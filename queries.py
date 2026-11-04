PREFIXES = """
PREFIX gm:      <https://example.org/games/>
PREFIX schema:  <https://schema.org/>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>
"""


class NamedQuery:
    def __init__(self, title, purpose, body):
        self.title = title
        self.purpose = purpose
        self.body = PREFIXES + body

    def run(self, graph):
        return list(graph.query(self.body))


class QueryLibrary:
    def __init__(self):
        self.items = [
            NamedQuery(
                "Q1. Ігри студії GSC Game World за роком випуску",
                "базовий перехід між двома типами сутностей",
                """
SELECT ?title ?year WHERE {
  ?game a gm:Game ;
        schema:name ?title ;
        gm:releaseYear ?year ;
        gm:developedBy ?studio .
  ?studio schema:name "GSC Game World"@uk .
}
ORDER BY ?year
"""),
            NamedQuery(
                "Q2. Ігри, випущені після 2014 року",
                "FILTER за числовим значенням",
                """
SELECT ?title ?year WHERE {
  ?game a gm:Game ;
        schema:name ?title ;
        gm:releaseYear ?year .
  FILTER (?year > 2014)
}
ORDER BY DESC(?year) ?title
"""),
            NamedQuery(
                "Q3. Кількість ігор і рік заснування кожної студії",
                "агрегат COUNT із GROUP BY та переходом до країни",
                """
SELECT ?studio ?country ?founded (COUNT(?game) AS ?games) WHERE {
  ?game gm:developedBy ?node .
  ?node schema:name ?studio ;
        gm:foundingYear ?founded ;
        gm:basedIn ?place .
  ?place schema:name ?country .
}
GROUP BY ?studio ?country ?founded
ORDER BY DESC(?games) ?studio
"""),
            NamedQuery(
                "Q4. Країни за кількістю випущених ігор",
                "агрегат із переходом гра -> студія -> країна",
                """
SELECT ?country (COUNT(DISTINCT ?game) AS ?games) WHERE {
  ?game gm:developedBy ?studio .
  ?studio gm:basedIn ?place .
  ?place schema:name ?country .
}
GROUP BY ?country
HAVING (COUNT(DISTINCT ?game) >= 2)
ORDER BY DESC(?games) ?country
"""),
            NamedQuery(
                "Q5. Жанри, пов'язані з кожним засновником студії",
                "перехід через чотири зв'язки: особа -> студія -> гра -> жанр",
                """
SELECT ?founder ?genre (COUNT(DISTINCT ?game) AS ?games) WHERE {
  ?studio gm:foundedBy ?person .
  ?person foaf:name ?founder .
  ?game gm:developedBy ?studio ;
        gm:hasGenre ?node .
  ?node schema:name ?genre .
}
GROUP BY ?founder ?genre
ORDER BY ?founder DESC(?games)
"""),
            NamedQuery(
                "Q6. Ланцюжки продовжень",
                "рекурсивний шлях властивості gm:sequelOf",
                """
SELECT ?later ?earlier WHERE {
  ?b gm:sequelOf ?a .
  ?b schema:name ?later .
  ?a schema:name ?earlier .
}
ORDER BY ?earlier
"""),
        ]

    def run_all(self, graph, limit=25):
        for query in self.items:
            print("=" * 78)
            print(query.title)
            print(f"призначення: {query.purpose}")
            print("-" * 78)
            rows = query.run(graph)
            for index, row in enumerate(rows):
                if index >= limit:
                    print(f"  … ще {len(rows) - limit} рядків")
                    break
                print("  " + " | ".join(str(value) for value in row))
            print(f"  [рядків: {len(rows)}]\n")


class FaultyQuery(NamedQuery):
    pass


BROKEN = FaultyQuery(
    "Помилковий запит",
    "фільтр за schema:datePublished, записаним як xsd:gYear",
    """
SELECT ?title ?year WHERE {
  ?game a gm:Game ;
        schema:name ?title ;
        schema:datePublished ?year .
  FILTER (?year > "2014"^^xsd:gYear)
}
ORDER BY ?year
""")

FIXED = NamedQuery(
    "Виправлений запит",
    "фільтр за gm:releaseYear, записаним як xsd:integer",
    """
SELECT ?title ?year WHERE {
  ?game a gm:Game ;
        schema:name ?title ;
        gm:releaseYear ?year .
  FILTER (?year > 2014)
}
ORDER BY ?year
""")
