#!/usr/bin/env python3
"""
Test script for the dynamic library selection system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.openai_service import determine_best_library, get_library_specific_prompt, get_library_rules

def test_library_selection():
    """Test the library selection for different subjects"""
    
    test_cases = [
        ("Digital Electronics", "Logic Gates", True),
        ("Mathematics", "Calculus", True),
        ("Computer Networks", "TCP/IP Protocol", True),
        ("Software Engineering", "UML Diagrams", True),
        ("Statistics", "Probability Distribution", True),
        ("Physics", "Circuit Analysis", True),
        ("Biology", "Cell Structure", True),
        ("Data Structures", "Binary Trees", True),
    ]
    
    print("🧪 Testing Dynamic Library Selection System")
    print("=" * 50)
    
    for subject, topic, requires_diagram in test_cases:
        print(f"\n📚 Subject: {subject}")
        print(f"📖 Topic: {topic}")
        
        library_name, reason = determine_best_library(subject, topic, requires_diagram)
        
        print(f"🎯 Selected Library: {library_name}")
        print(f"💡 Reason: {reason}")
        
        if library_name:
            print(f"📝 Sample Prompt:")
            print(get_library_specific_prompt(library_name)[:100] + "...")
            print(f"📋 Rules:")
            print(get_library_rules(library_name)[:100] + "...")
        
        print("-" * 30)

if __name__ == "__main__":
    test_library_selection() 