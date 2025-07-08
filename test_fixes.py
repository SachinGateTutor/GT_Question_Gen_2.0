#!/usr/bin/env python3
"""
Test script to verify fixes for common AI mistakes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.diagram_service import render_seaborn_diagram, render_matplotlib_diagram

def test_seaborn_fixes():
    """Test seaborn fixes for common AI mistakes"""
    
    print("🧪 Testing Seaborn Fixes")
    print("=" * 40)
    
    # Test case 1: Missing pandas import
    code1 = """import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# Create a bar plot to visualize the probability
data = {'Outcome': ['Less than 4', '4 or more'],
        'Probability': [0.5, 0.5]}
df = pd.DataFrame(data)
sns.barplot(data=df, x='Outcome', y='Probability')
plt.title('Probability Test')
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()"""
    
    print("📊 Test 1: Missing pandas import")
    result1 = render_seaborn_diagram(code1, "test_output")
    print(f"✅ Result: {'Success' if result1 else 'Failed'}")
    
    # Test case 2: Invalid venn2 function
    code2 = """import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

# Create Venn diagram using seaborn
data = {'A': 40, 'B': 30, 'AB': 20}
sns.venn2(subsets=(data['A'], data['B'], data['AB']), set_labels=('A', 'B'))
plt.title('Venn Diagram Test')
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()"""
    
    print("📊 Test 2: Invalid venn2 function")
    result2 = render_seaborn_diagram(code2, "test_output")
    print(f"✅ Result: {'Success' if result2 else 'Failed'}")

def test_matplotlib_fixes():
    """Test matplotlib fixes for common AI mistakes"""
    
    print("\n🧪 Testing Matplotlib Fixes")
    print("=" * 40)
    
    # Test case: Missing numpy import
    code = """import matplotlib.pyplot as plt
from io import BytesIO

# Create matplotlib figure
fig, ax = plt.subplots(figsize=(8, 6))
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)
plt.title('Sine Wave')
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()"""
    
    print("📊 Test: Missing numpy import")
    result = render_matplotlib_diagram(code, "test_output")
    print(f"✅ Result: {'Success' if result else 'Failed'}")

if __name__ == "__main__":
    # Create test output directory
    os.makedirs("test_output", exist_ok=True)
    
    test_seaborn_fixes()
    test_matplotlib_fixes()
    
    print("\n🎉 Testing completed!") 