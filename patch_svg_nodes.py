import xml.etree.ElementTree as ET

# Mappa dei gruppi principali e relative coordinate iniziali (x, y)
group_layout = {
    "frontend_security": {"prefix": "fs", "x": 320, "y": 350},
    "api_security": {"prefix": "as", "x": 740, "y": 350},
    "backend_security": {"prefix": "bs", "x": 100, "y": 350},
    "database_security": {"prefix": "ds", "x": 990, "y": 160},
    "devsecops": {"prefix": "dv", "x": 500, "y": 160},
}

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ns = {"svg": SVG_NS}

tree = ET.parse("static/mappa2_patched.svg")
root = tree.getroot()

# Trova o crea contenitore <text>
text_container = root.find(".//svg:text", ns)
if text_container is None:
    text_container = ET.SubElement(root, f"{{{SVG_NS}}}text")

# Posiziona i nodi figli
for group_key, conf in group_layout.items():
    prefix = conf["prefix"]
    x = conf["x"]
    y = conf["y"]
    for i in range(1, 6):  # max 5 figli per gruppo
        key = f"{prefix}{i}"
        tspan = root.find(f".//svg:tspan[@id='{key}']", ns)
        if tspan is not None:
            tspan.set("x", str(x))
            tspan.set("y", str(y))
            y += 25  # spazio tra i nodi

# Salva file modificato
tree.write("static/mappa2_patched.svg", encoding="utf-8", xml_declaration=True)
print("✅ Layout SVG aggiornato con posizionamento nodi figli.")
