"""
Demo script to generate a sample architectural diagram
"""
from diagram import Node, Edge, Diagram, generate_svg

def create_sample_diagram():
    """Create a sample microservices diagram"""
    # Define nodes
    nodes = [
        Node(id="api_gateway", label="API Gateway", type="gateway", color="#FF6B6B"),
        Node(id="user_service", label="User Service", type="service", color="#4ECDC4"),
        Node(id="order_service", label="Order Service", type="service", color="#4ECDC4"),
        Node(id="postgres_db", label="PostgreSQL", type="database", color="#45B7D1"),
        Node(id="redis_cache", label="Redis Cache", type="cache", color="#96CEB4"),
        Node(id="frontend", label="React Frontend", type="frontend", color="#FFEAA7")
    ]
    
    # Define edges (connections)
    edges = [
        Edge(from_node="frontend", to_node="api_gateway", label="HTTP requests"),
        Edge(from_node="api_gateway", to_node="user_service", label="routes"),
        Edge(from_node="api_gateway", to_node="order_service", label="routes"),
        Edge(from_node="user_service", to_node="postgres_db", label="user data"),
        Edge(from_node="order_service", to_node="postgres_db", label="order data"),
        Edge(from_node="user_service", to_node="redis_cache", label="session cache"),
        Edge(from_node="order_service", to_node="redis_cache", label="order cache")
    ]
    
    # Create diagram
    diagram = Diagram(
        title="E-commerce Microservices Architecture",
        nodes=nodes,
        edges=edges
    )
    
    return diagram

if __name__ == "__main__":
    print("Creating sample architectural diagram...")
    
    try:
        # Create diagram
        sample_diagram = create_sample_diagram()
        
        # Generate SVG
        svg_path = generate_svg(sample_diagram, "static/generated")
        
        print(f"✅ Successfully generated diagram: {svg_path}")
        print(f"📊 Diagram contains {len(sample_diagram.nodes)} nodes and {len(sample_diagram.edges)} edges")
        
        # Read and display first few lines of SVG
        with open(svg_path.replace("/", "\\"), 'r') as f:
            svg_content = f.read()
            print(f"📄 SVG file size: {len(svg_content)} characters")
            print("🔍 SVG preview (first 200 chars):")
            print(svg_content[:200] + "...")
            
        print("\n🎉 Demo completed successfully!")
        print(f"You can view the generated diagram by opening: {svg_path}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
