"""
Dynamic diagram generation module for creating architectural diagrams
"""
import os
import json
import uuid
import math
from typing import List, Optional
from pydantic import BaseModel, ValidationError
import svgwrite
from langchain_openai import ChatOpenAI


class Node(BaseModel):
    """Represents a node in the architectural diagram"""
    id: str
    label: str
    type: str  # e.g., "service", "database", "gateway", "cache"
    color: Optional[str] = None


class Edge(BaseModel):
    """Represents a connection between two nodes"""
    from_node: str
    to_node: str
    label: Optional[str] = None


class Diagram(BaseModel):
    """Complete diagram specification with nodes and edges"""
    title: str
    nodes: List[Node]
    edges: List[Edge]


def ask_llm_for_diagram_spec(query: str, llm: ChatOpenAI) -> Diagram:
    """
    Ask the LLM to generate a strict JSON specification for an architectural diagram
    
    Args:
        query: User's diagram request
        llm: ChatOpenAI instance
        
    Returns:
        Diagram: Parsed diagram specification
        
    Raises:
        ValidationError: If the LLM response doesn't match the expected schema
        json.JSONDecodeError: If the LLM response isn't valid JSON
    """
    prompt = f"""
You are an expert architect. Create a JSON specification for an architectural diagram based on this request: "{query}"

Return ONLY a valid JSON object with this exact schema:
{{
  "title": "Diagram Title",
  "nodes": [
    {{
      "id": "unique_id",
      "label": "Display Name", 
      "type": "service|database|gateway|cache|frontend|backend",
      "color": "#hex_color (optional)"
    }}
  ],
  "edges": [
    {{
      "from_node": "source_node_id",
      "to_node": "target_node_id", 
      "label": "Connection Description (optional)"
    }}
  ]
}}

Rules:
- Use clear, descriptive node IDs (no spaces, use underscores)
- Include all components mentioned in the request
- Add logical connections between components
- Use appropriate node types
- Return ONLY the JSON, no other text

Request: {query}
"""
    
    response = llm.invoke(prompt)
    response_text = response.content.strip()
    
    # Remove any markdown code blocks if present
    if response_text.startswith("```"):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    if response_text.startswith("```json"):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    
    # Parse JSON and validate with Pydantic
    diagram_data = json.loads(response_text)
    return Diagram(**diagram_data)


def generate_svg(diagram: Diagram, output_dir: str = "static/generated") -> str:
    """
    Generate an SVG file from a diagram specification using automatic layout
    
    Args:
        diagram: Diagram specification with nodes and edges
        output_dir: Directory to save the generated SVG
        
    Returns:
        str: Relative path to the generated SVG file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    filename = f"diagram_{uuid.uuid4().hex[:8]}.svg"
    filepath = os.path.join(output_dir, filename)
    
    # SVG dimensions and layout parameters
    width, height = 800, 600
    margin = 50
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(filepath, size=(width, height))
    
    # Add title
    dwg.add(dwg.text(diagram.title, 
                    insert=(width // 2, 30), 
                    text_anchor="middle",
                    font_size="20",
                    font_weight="bold",
                    fill="black"))
    
    # Calculate grid layout for nodes
    num_nodes = len(diagram.nodes)
    if num_nodes == 0:
        dwg.save()
        return f"{output_dir}/{filename}".replace("\\", "/")
    
    # Determine grid dimensions (roughly square)
    cols = math.ceil(math.sqrt(num_nodes))
    rows = math.ceil(num_nodes / cols)
    
    # Calculate spacing
    usable_width = width - 2 * margin
    usable_height = height - 2 * margin - 60  # Account for title
    cell_width = usable_width / cols
    cell_height = usable_height / rows
    
    # Node styling based on type
    type_colors = {
        "gateway": "#FF6B6B",
        "service": "#4ECDC4", 
        "database": "#45B7D1",
        "cache": "#96CEB4",
        "frontend": "#FFEAA7",
        "backend": "#DDA0DD"
    }
    
    # Position nodes and store coordinates
    node_positions = {}
    for i, node in enumerate(diagram.nodes):
        row = i // cols
        col = i % cols
        
        # Center the node in its grid cell
        x = margin + col * cell_width + cell_width // 2
        y = margin + 60 + row * cell_height + cell_height // 2
        
        node_positions[node.id] = (x, y)
        
        # Choose color
        color = node.color or type_colors.get(node.type, "#E0E0E0")
        
        # Draw node as rectangle with rounded corners
        node_width = min(120, cell_width - 20)
        node_height = 60
        
        rect = dwg.rect(
            insert=(x - node_width//2, y - node_height//2),
            size=(node_width, node_height),
            rx=10, ry=10,
            fill=color,
            stroke="black",
            stroke_width=2
        )
        dwg.add(rect)
        
        # Add node label
        dwg.add(dwg.text(node.label,
                        insert=(x, y + 5),
                        text_anchor="middle",
                        font_size="12",
                        font_weight="bold",
                        fill="black"))
    
    # Add arrowhead marker definition
    marker = dwg.defs.add(dwg.marker(
        insert=(10, 5), size=(10, 10),
        orient="auto", markerUnits="strokeWidth"
    ))
    marker['id'] = 'arrowhead'
    marker.add(dwg.path(d="M 0,0 L 0,10 L 10,5 z", fill="black"))
    
    # Draw edges
    for edge in diagram.edges:
        if edge.from_node in node_positions and edge.to_node in node_positions:
            x1, y1 = node_positions[edge.from_node]
            x2, y2 = node_positions[edge.to_node]
            
            # Draw arrow
            line = dwg.line(start=(x1, y1), end=(x2, y2),
                           stroke="black", stroke_width=2,
                           marker_end="url(#arrowhead)")
            dwg.add(line)
            
            # Add edge label if provided
            if edge.label:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                dwg.add(dwg.text(edge.label,
                                insert=(mid_x, mid_y - 10),
                                text_anchor="middle",
                                font_size="10",
                                fill="blue"))
    
    # Save the SVG
    dwg.save()
    
    # Return relative path (use forward slashes for web compatibility)
    return f"{output_dir}/{filename}".replace("\\", "/")


def is_diagram_request(query: str) -> bool:
    """
    Check if a user query is requesting a diagram
    
    Args:
        query: User's query string
        
    Returns:
        bool: True if the query appears to be requesting a diagram
    """
    diagram_keywords = [
        "mappa concettuale", "diagramma", "diagramma a blocchi",
        "schema architetturale", "diagramma architetturale",
        "architettura", "architectural diagram", "architecture diagram",
        "create diagram", "draw diagram", "show architecture",
        "microservices", "system design"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in diagram_keywords)
