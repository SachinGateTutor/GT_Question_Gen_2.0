#!/usr/bin/env python3
"""
Test script to demonstrate enhanced diagram generation with diverse shapes, colors, and visual styles.
This shows what's possible with the various diagram libraries.
"""

import os
import sys
import uuid
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import schemdraw
import schemdraw.elements as e
import schemdraw.logic as logic
import schemdraw.flow as flow
from io import BytesIO

def create_enhanced_schemdraw_diagram():
    """Create a rich, diverse schemdraw diagram with multiple elements"""
    print("🎨 Creating enhanced schemdraw diagram...")
    
    d = schemdraw.Drawing()
    
    # Add diverse electronic elements with colors and labels
    d += (r1 := e.Resistor().label('R1').color('red').up().label('10Ω'))
    d += (c1 := e.Capacitor().label('C1').color('blue').right().label('100μF'))
    d += (l1 := e.Inductor().label('L1').color('green').down().label('1mH'))
    d += (d1 := e.Diode().label('D1').color('orange').left().label('LED'))
    d += (v1 := e.SourceV().label('V1').color('purple').up().label('5V'))
    
    # Add logic elements
    d += (and1 := logic.And().label('AND').color('brown').at((3, 0)))
    d += (or1 := logic.Or().label('OR').color('teal').at((3, -2)))
    d += (not1 := logic.Not().label('NOT').color('magenta').at((3, -4)))
    
    # Add flow elements
    d += (start := flow.Start().label('START').color('darkgreen').at((0, 3)))
    d += (process := flow.Process().label('PROCESS').color('navy').at((0, 1)))
    d += (decision := flow.Decision().label('DECISION').color('crimson').at((0, -1)))
    d += (end := flow.End().label('END').color('darkred').at((0, -3)))
    
    # Add connections
    d += e.Line().at(start.S).to(process.N).color('red').width(2)
    d += e.Line().at(process.S).to(decision.N).color('blue').width(2)
    d += e.Line().at(decision.S).to(end.N).color('green').width(2)
    
    # Save to buffer
    buffer = BytesIO()
    d.save(buffer)
    buffer.seek(0)
    
    # Save to file
    filename = f"enhanced_schemdraw_{uuid.uuid4().hex[:8]}.png"
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f"✅ Enhanced schemdraw diagram saved as {filename}")
    return filename

def create_enhanced_matplotlib_diagram():
    """Create a rich, colorful matplotlib visualization"""
    print("📊 Creating enhanced matplotlib diagram...")
    
    plt.style.use('default')  # Use default style for compatibility
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # First subplot - colorful scatter plot
    x1 = np.random.randn(50)
    y1 = np.random.randn(50)
    colors1 = np.random.rand(50)
    sizes1 = 1000 * np.random.rand(50)
    
    scatter1 = ax1.scatter(x1, y1, c=colors1, s=sizes1, alpha=0.6, 
                           cmap='viridis', edgecolors='black', linewidth=0.5)
    ax1.set_title('Enhanced Scatter Plot', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X Values', fontsize=12)
    ax1.set_ylabel('Y Values', fontsize=12)
    ax1.grid(True, alpha=0.3)
    plt.colorbar(scatter1, ax=ax1)
    
    # Second subplot - bar chart with different colors
    categories = ['A', 'B', 'C', 'D', 'E']
    values = [23, 45, 56, 78, 32]
    colors2 = ['red', 'blue', 'green', 'orange', 'purple']
    
    bars = ax2.bar(categories, values, color=colors2, alpha=0.7, 
                   edgecolor='black', linewidth=1)
    ax2.set_title('Enhanced Bar Chart', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Categories', fontsize=12)
    ax2.set_ylabel('Values', fontsize=12)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)
    plt.close()
    
    # Save to file
    filename = f"enhanced_matplotlib_{uuid.uuid4().hex[:8]}.png"
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f"✅ Enhanced matplotlib diagram saved as {filename}")
    return filename

def create_enhanced_networkx_diagram():
    """Create a rich, diverse network graph"""
    print("🕸️ Creating enhanced networkx diagram...")
    
    G = nx.Graph()
    
    # Add nodes with different attributes
    nodes = [
        (1, {'color': 'red', 'size': 1000, 'label': 'Start'}),
        (2, {'color': 'blue', 'size': 800, 'label': 'Process'}),
        (3, {'color': 'green', 'size': 1200, 'label': 'Decision'}),
        (4, {'color': 'orange', 'size': 900, 'label': 'Action'}),
        (5, {'color': 'purple', 'size': 1100, 'label': 'End'}),
        (6, {'color': 'teal', 'size': 700, 'label': 'Branch'}),
        (7, {'color': 'crimson', 'size': 950, 'label': 'Merge'})
    ]
    
    G.add_nodes_from(nodes)
    
    # Add edges with different attributes
    edges = [
        (1, 2, {'color': 'red', 'width': 3}),
        (2, 3, {'color': 'blue', 'width': 2}),
        (3, 4, {'color': 'green', 'width': 4}),
        (3, 6, {'color': 'orange', 'width': 2}),
        (4, 5, {'color': 'purple', 'width': 3}),
        (6, 7, {'color': 'teal', 'width': 2}),
        (7, 5, {'color': 'crimson', 'width': 2})
    ]
    
    G.add_edges_from(edges)
    
    # Create layout
    pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Draw the graph
    plt.figure(figsize=(12, 8))
    
    # Draw nodes with different colors and sizes
    node_colors = [G.nodes[node]['color'] for node in G.nodes()]
    node_sizes = [G.nodes[node]['size'] for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                          alpha=0.8, edgecolors='black', linewidths=2)
    
    # Draw edges with different colors and widths
    edge_colors = [G[u][v]['color'] for u, v in G.edges()]
    edge_widths = [G[u][v]['width'] for u, v in G.edges()]
    
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, 
                          alpha=0.7, arrows=True, arrowsize=20)
    
    # Add labels
    labels = {node: G.nodes[node]['label'] for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=12, font_weight='bold')
    
    plt.title('Enhanced Network Graph', fontsize=16, fontweight='bold')
    plt.axis('off')
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)
    plt.close()
    
    # Save to file
    filename = f"enhanced_networkx_{uuid.uuid4().hex[:8]}.png"
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f"✅ Enhanced networkx diagram saved as {filename}")
    return filename

def create_enhanced_pillow_diagram():
    """Create a rich, colorful pillow diagram"""
    print("🎨 Creating enhanced pillow diagram...")
    
    # Create image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw diverse shapes with different colors
    # Rectangles
    draw.rectangle([50, 50, 200, 150], fill='lightblue', outline='darkblue', width=3)
    draw.rectangle([250, 50, 400, 150], fill='lightgreen', outline='darkgreen', width=3)
    draw.rectangle([450, 50, 600, 150], fill='lightcoral', outline='darkred', width=3)
    
    # Circles
    draw.ellipse([50, 200, 150, 300], fill='yellow', outline='orange', width=3)
    draw.ellipse([200, 200, 300, 300], fill='pink', outline='purple', width=3)
    draw.ellipse([350, 200, 450, 300], fill='lightcyan', outline='darkcyan', width=3)
    
    # Polygons
    points1 = [(500, 200), (550, 150), (600, 200), (550, 250)]
    draw.polygon(points1, fill='lightyellow', outline='gold', width=3)
    
    points2 = [(650, 200), (700, 150), (750, 200), (700, 250)]
    draw.polygon(points2, fill='lavender', outline='indigo', width=3)
    
    # Lines with different styles
    draw.line([50, 350, 200, 450], fill='red', width=5)
    draw.line([250, 350, 400, 450], fill='blue', width=3)
    draw.line([450, 350, 600, 450], fill='green', width=7)
    
    # Arrows
    draw.line([50, 500, 150, 500], fill='purple', width=4)
    draw.polygon([(150, 500), (140, 495), (140, 505)], fill='purple')
    
    draw.line([200, 500, 300, 500], fill='orange', width=4)
    draw.polygon([(300, 500), (290, 495), (290, 505)], fill='orange')
    
    # Add text with different fonts and colors
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_medium = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((50, 20), "Enhanced Pillow Diagram", fill='darkblue', font=font_large)
    draw.text((50, 170), "Rectangles", fill='darkblue', font=font_medium)
    draw.text((50, 320), "Circles", fill='darkgreen', font=font_medium)
    draw.text((500, 170), "Polygons", fill='darkred', font=font_medium)
    draw.text((50, 470), "Lines & Arrows", fill='darkpurple', font=font_medium)
    
    # Add annotations
    draw.text((220, 100), "Process", fill='darkgreen', font=font_small)
    draw.text((320, 250), "Data", fill='darkred', font=font_small)
    draw.text((570, 250), "Decision", fill='darkblue', font=font_small)
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Save to file
    filename = f"enhanced_pillow_{uuid.uuid4().hex[:8]}.png"
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f"✅ Enhanced pillow diagram saved as {filename}")
    return filename

def main():
    """Test all enhanced diagram generation methods"""
    print("🚀 Testing Enhanced Diagram Generation")
    print("=" * 50)
    
    try:
        # Test matplotlib
        matplotlib_file = create_enhanced_matplotlib_diagram()
        
        # Test networkx
        networkx_file = create_enhanced_networkx_diagram()
        
        # Test pillow
        pillow_file = create_enhanced_pillow_diagram()
        
        # Test schemdraw (skip if there are issues)
        try:
            schemdraw_file = create_enhanced_schemdraw_diagram()
        except Exception as e:
            print(f"⚠️ Skipping schemdraw test due to: {e}")
            schemdraw_file = None
        
        print("\n🎉 Enhanced diagrams created successfully!")
        print(f"📁 Files created:")
        if matplotlib_file:
            print(f"   - {matplotlib_file}")
        if networkx_file:
            print(f"   - {networkx_file}")
        if pillow_file:
            print(f"   - {pillow_file}")
        if schemdraw_file:
            print(f"   - {schemdraw_file}")
        
        print("\n✨ These diagrams demonstrate the rich diversity possible with:")
        print("   - Multiple colors and color schemes")
        print("   - Different shapes and geometric forms")
        print("   - Various layouts and arrangements")
        print("   - Different visual complexity levels")
        print("   - Rich annotations and labels")
        print("   - Diverse connection styles and patterns")
        
    except Exception as e:
        print(f"❌ Error creating enhanced diagrams: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 