"""
Simple test to verify diagram generation works
"""
import sys
import os
sys.path.append('.')

from diagram import Node, Edge, Diagram, generate_svg, is_diagram_request

def test_basic_functionality():
    """Test basic diagram generation without LLM"""
    print("Testing basic diagram functionality...")
    
    # Test 1: Diagram detection
    print("1. Testing diagram request detection...")
    assert is_diagram_request("Create a diagramma architetturale")
    assert is_diagram_request("architectural diagram")
    assert not is_diagram_request("What is Python?")
    print("   ✅ Diagram detection works")
    
    # Test 2: Model creation
    print("2. Testing Pydantic models...")
    nodes = [
        Node(id="api_gateway", label="API Gateway", type="gateway", color="#FF6B6B"),
        Node(id="service_a", label="Service A", type="service", color="#4ECDC4"),
        Node(id="service_b", label="Service B", type="service", color="#4ECDC4"),
        Node(id="postgres", label="Postgres DB", type="database", color="#45B7D1"),
        Node(id="redis", label="Redis Cache", type="cache", color="#96CEB4")
    ]
    
    edges = [
        Edge(from_node="api_gateway", to_node="service_a", label="routes"),
        Edge(from_node="api_gateway", to_node="service_b", label="routes"),
        Edge(from_node="service_a", to_node="postgres", label="queries"),
        Edge(from_node="service_b", to_node="postgres", label="queries"),
        Edge(from_node="service_a", to_node="redis", label="cache"),
        Edge(from_node="service_b", to_node="redis", label="cache")
    ]
    
    diagram = Diagram(
        title="Microservices Architecture",
        nodes=nodes,
        edges=edges
    )
    
    print(f"   ✅ Created diagram with {len(diagram.nodes)} nodes and {len(diagram.edges)} edges")
    
    # Test 3: SVG generation
    print("3. Testing SVG generation...")
    svg_path = generate_svg(diagram, "static/generated")
    
    if os.path.exists(svg_path.replace("/", os.sep)):
        print(f"   ✅ SVG generated successfully: {svg_path}")
        
        # Check SVG content
        with open(svg_path.replace("/", os.sep), 'r') as f:
            content = f.read()
            if '<svg' in content and 'Microservices Architecture' in content:
                print("   ✅ SVG content is valid")
                return True
            else:
                print("   ❌ SVG content is invalid")
                return False
    else:
        print(f"   ❌ SVG file not created: {svg_path}")
        return False

if __name__ == "__main__":
    print("Testing Dynamic Diagram Generation")
    print("=" * 40)
    
    try:
        success = test_basic_functionality()
        if success:
            print("\n🎉 Basic functionality test passed!")
        else:
            print("\n❌ Basic functionality test failed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
