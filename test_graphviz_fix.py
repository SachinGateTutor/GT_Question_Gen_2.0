#!/usr/bin/env python3
"""
Test script to verify graphviz fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.diagram_service import render_graphviz_diagram

def test_graphviz_fix():
    """Test graphviz fix for the DBMS architecture diagram"""
    
    print("🧪 Testing Graphviz Fix")
    print("=" * 30)
    
    # Test case: DBMS Three Level Architecture
    code = """import graphviz
from io import BytesIO

# Create graphviz diagram
dot = graphviz.Digraph()
# Add nodes for Internal, Conceptual, and External levels
dot.node('Internal', 'Internal Level (Physical Level)')
dot.node('Conceptual', 'Conceptual Level (Logical Level)')
dot.node('External', 'External Level (View Level)')
# Add edges to connect the levels
dot.edge('Internal', 'Conceptual', label='Conceptual Schema')
dot.edge('Conceptual', 'External', label='External Schema')
# Save diagram to a buffer
buffer = BytesIO()
dot.render(buffer, format='png', cleanup=True)"""
    
    print("📊 Test: DBMS Three Level Architecture")
    result = render_graphviz_diagram(code, "test_output")
    print(f"✅ Result: {'Success' if result else 'Failed'}")
    
    if result:
        print(f"📁 Generated file: {result}")

if __name__ == "__main__":
    # Create test output directory
    os.makedirs("test_output", exist_ok=True)
    
    test_graphviz_fix()
    
    print("\n🎉 Testing completed!") 