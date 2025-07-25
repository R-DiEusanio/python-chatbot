"""
Tests for dynamic diagram generation functionality
"""
import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch
from pydantic import ValidationError

from diagram import Node, Edge, Diagram, ask_llm_for_diagram_spec, generate_svg, is_diagram_request


class TestPydanticModels:
    """Test Pydantic model validation"""
    
    def test_node_creation(self):
        """Test Node model creation"""
        node = Node(id="test_id", label="Test Node", type="service")
        assert node.id == "test_id"
        assert node.label == "Test Node" 
        assert node.type == "service"
        assert node.color is None

    def test_node_with_color(self):
        """Test Node model with color"""
        node = Node(id="db", label="Database", type="database", color="#FF0000")
        assert node.color == "#FF0000"

    def test_edge_creation(self):
        """Test Edge model creation"""
        edge = Edge(from_node="api", to_node="db")
        assert edge.from_node == "api"
        assert edge.to_node == "db"
        assert edge.label is None

    def test_diagram_creation(self):
        """Test complete Diagram model"""
        nodes = [
            Node(id="api", label="API Gateway", type="gateway"),
            Node(id="db", label="Database", type="database")
        ]
        edges = [
            Edge(from_node="api", to_node="db", label="queries")
        ]
        diagram = Diagram(title="Test Architecture", nodes=nodes, edges=edges)
        
        assert diagram.title == "Test Architecture"
        assert len(diagram.nodes) == 2
        assert len(diagram.edges) == 1


class TestDiagramGeneration:
    """Test SVG generation functionality"""
    
    def test_generate_svg_creates_file(self):
        """Test that generate_svg creates a valid SVG file"""
        nodes = [
            Node(id="api", label="API", type="service"),
            Node(id="db", label="DB", type="database")
        ]
        edges = [Edge(from_node="api", to_node="db")]
        diagram = Diagram(title="Test", nodes=nodes, edges=edges)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            svg_path = generate_svg(diagram, temp_dir)
            
            # Check file exists
            full_path = svg_path.replace("/", os.sep)
            assert os.path.exists(full_path)
            
            # Check it's a valid SVG (basic check)
            with open(full_path, 'r') as f:
                content = f.read()
                assert content.startswith('<svg')
                assert 'Test' in content  # Title should be in SVG

    def test_generate_svg_empty_diagram(self):
        """Test SVG generation with empty diagram"""
        diagram = Diagram(title="Empty", nodes=[], edges=[])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            svg_path = generate_svg(diagram, temp_dir)
            full_path = svg_path.replace("/", os.sep)
            assert os.path.exists(full_path)


class TestDiagramDetection:
    """Test diagram request detection"""
    
    def test_is_diagram_request_positive(self):
        """Test positive diagram detection"""
        assert is_diagram_request("Create a diagramma architetturale") 
        assert is_diagram_request("Show me the sistema architecture")
        assert is_diagram_request("Draw a microservices diagram")
        assert is_diagram_request("Mappa concettuale del sistema")

    def test_is_diagram_request_negative(self):
        """Test negative diagram detection"""
        assert not is_diagram_request("What is Python?")
        assert not is_diagram_request("Explain machine learning")
        assert not is_diagram_request("How to write code")


class TestLLMIntegration:
    """Test LLM integration with mocking"""
    
    @patch('diagram.ChatOpenAI')
    def test_ask_llm_for_diagram_spec_success(self, mock_llm_class):
        """Test successful LLM diagram spec generation"""
        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps({
            "title": "Test Architecture",
            "nodes": [
                {"id": "api", "label": "API Gateway", "type": "gateway"},
                {"id": "db", "label": "Database", "type": "database"}
            ],
            "edges": [
                {"from_node": "api", "to_node": "db", "label": "queries"}
            ]
        })
        mock_llm.invoke.return_value = mock_response
        
        result = ask_llm_for_diagram_spec("Create API architecture", mock_llm)
        
        assert isinstance(result, Diagram)
        assert result.title == "Test Architecture"
        assert len(result.nodes) == 2
        assert len(result.edges) == 1

    @patch('diagram.ChatOpenAI')
    def test_ask_llm_for_diagram_spec_invalid_json(self, mock_llm_class):
        """Test LLM returning invalid JSON"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"
        mock_llm.invoke.return_value = mock_response
        
        with pytest.raises(json.JSONDecodeError):
            ask_llm_for_diagram_spec("Create architecture", mock_llm)

    @patch('diagram.ChatOpenAI') 
    def test_ask_llm_handles_markdown_code_blocks(self, mock_llm_class):
        """Test LLM response with markdown code blocks"""
        mock_llm = Mock()
        mock_response = Mock()
        json_content = {
            "title": "Test",
            "nodes": [{"id": "test", "label": "Test", "type": "service"}],
            "edges": []
        }
        mock_response.content = f"```json\n{json.dumps(json_content)}\n```"
        mock_llm.invoke.return_value = mock_response
        
        result = ask_llm_for_diagram_spec("Create test", mock_llm)
        
        assert isinstance(result, Diagram)
        assert result.title == "Test"


if __name__ == "__main__":
    pytest.main([__file__])
