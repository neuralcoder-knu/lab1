import html
import shutil
import subprocess

import matplotlib
from rdflib import Literal, URIRef
from rdflib.namespace import RDF, RDFS

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx


class GraphRenderer:
    PALETTE = {
        "Game": "#1f4e79",
        "Studio": "#8b0000",
        "Publisher": "#b8860b",
        "Platform": "#2e7d32",
        "Genre": "#6a1b9a",
        "Person": "#00695c",
        "Country": "#37474f",
    }

    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
        self.graph = knowledge_graph.graph
        self.ns = knowledge_graph.ns

    def _class_of(self, node):
        for kind in self.graph.objects(node, RDF.type):
            name = str(kind).replace(str(self.ns), "")
            if name in self.PALETTE:
                return name
        return None

    def _label_of(self, node):
        for value in self.graph.objects(node, RDFS.label):
            if isinstance(value, Literal):
                text = str(value)
                return text if len(text) <= 30 else text[:27] + "…"
        return str(node).rsplit("/", 1)[-1]

    def _as_networkx(self, skip=()):
        target = nx.Graph()
        for subject, predicate, obj in self.graph:
            if not isinstance(obj, URIRef) or predicate == RDF.type:
                continue
            left, right = self._class_of(subject), self._class_of(obj)
            if not left or not right or left in skip or right in skip:
                continue
            target.add_node(subject, kind=left)
            target.add_node(obj, kind=right)
            target.add_edge(subject, obj, relation=str(predicate).replace(str(self.ns), ""))
        return target

    def to_png(self, path="graph.png", skip=()):
        if not shutil.which("dot"):
            return self._to_png_matplotlib(path, skip)
        target = self._as_networkx(skip)
        lines = ["digraph G {", '  rankdir=LR; bgcolor="white";',
                 '  node [shape=box style="rounded,filled" fillcolor="#ffffff" '
                 'fontname="DejaVu Sans" fontsize=9];',
                 '  edge [fontname="DejaVu Sans" fontsize=7 color="#888888"];']
        ids = {node: f"n{index}" for index, node in enumerate(target)}
        for node, data in target.nodes(data=True):
            color = self.PALETTE[data["kind"]]
            lines.append(f'  {ids[node]} [label="{html.escape(self._label_of(node))}" '
                         f'color="{color}" fontcolor="{color}"];')
        for left, right, data in target.edges(data=True):
            lines.append(f'  {ids[left]} -> {ids[right]} '
                         f'[label="{html.escape(data["relation"])}"];')
        lines.append("}")
        dot_path = path.replace(".png", ".dot")
        with open(dot_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        subprocess.run(["dot", "-Tpng", "-Gdpi=140", dot_path, "-o", path], check=True)
        return path

    def _to_png_matplotlib(self, path, skip):
        target = self._as_networkx(skip)
        plt.figure(figsize=(18, 13))
        layout = nx.spring_layout(target, k=0.7, seed=11)
        colors = [self.PALETTE[target.nodes[n]["kind"]] for n in target]
        sizes = [220 + 110 * target.degree(n) for n in target]
        nx.draw_networkx_edges(target, layout, alpha=0.25)
        nx.draw_networkx_nodes(target, layout, node_color=colors, node_size=sizes, alpha=0.9)
        nx.draw_networkx_labels(target, layout,
                                labels={n: self._label_of(n) for n in target}, font_size=7)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path, dpi=130)
        plt.close()
        return path

    def to_html(self, path="graph.html"):
        from pyvis.network import Network
        target = self._as_networkx()
        net = Network(height="820px", width="100%", bgcolor="#ffffff",
                      font_color="#222222", directed=True, cdn_resources="remote")
        net.barnes_hut(gravity=-7000, spring_length=150)
        for node, data in target.nodes(data=True):
            net.add_node(str(node), label=self._label_of(node),
                         color=self.PALETTE[data["kind"]],
                         size=10 + 3 * target.degree(node),
                         title=f'{data["kind"]}: {self._label_of(node)}')
        for left, right, data in target.edges(data=True):
            net.add_edge(str(left), str(right), label=data["relation"], color="#cccccc")
        net.save_graph(path)
        return path
