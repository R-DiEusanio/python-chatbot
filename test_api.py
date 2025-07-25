"""
Simple test script to verify diagram generation functionality
"""
import requests
import json

def test_diagram_generation():
    """Test the diagram generation endpoint"""
    url = "http://localhost:5000/ask"
    
    # Test diagram request
    diagram_payload = {
        "query": "Create an architectural diagram for a microservices web system with API Gateway, Service A, Service B, Postgres DB, and Redis cache"
    }
    
    print("Testing diagram generation...")
    try:
        response = requests.post(url, json=diagram_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if "svg_url" in result:
                print(f"✅ Diagram generated successfully: {result['svg_url']}")
                if "error" in result:
                    print(f"⚠️  Warning: {result['error']}")
                return True
            else:
                print("❌ No svg_url in response")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_normal_query():
    """Test normal Q&A functionality"""
    url = "http://localhost:5000/ask"
    
    normal_payload = {
        "query": "What is Python programming language?"
    }
    
    print("\nTesting normal Q&A...")
    try:
        response = requests.post(url, json=normal_payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "answer" in result:
                print(f"✅ Normal Q&A works: {result['answer'][:100]}...")
                return True
            else:
                print("❌ No answer in response")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Python Chatbot Dynamic Diagram Generation")
    print("=" * 50)
    
    diagram_success = test_diagram_generation()
    qa_success = test_normal_query()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Diagram Generation: {'✅ PASS' if diagram_success else '❌ FAIL'}")
    print(f"Normal Q&A: {'✅ PASS' if qa_success else '❌ FAIL'}")
    
    if diagram_success and qa_success:
        print("\n🎉 All tests passed! The feature is working correctly.")
    else:
        print("\n🚨 Some tests failed. Check the logs above for details.")
