# Programming Questions Feature Guide

## Overview

The GT Question Generator now supports generating programming questions with code snippets! This feature allows you to create multiple-choice questions that include realistic code examples in various programming languages.

## Features

### 🎯 Supported Programming Languages
- **Java Programming** - Questions with Java code snippets
- **C++ Programming** - Questions with C++ code snippets  
- **Python Programming** - Questions with Python code snippets
- **Data Structures with Programs** - Questions about data structures with implementation code
- **Algorithms Implementation** - Questions about algorithms with code examples
- **Object-Oriented Programming** - OOP concepts with code examples
- **Database Programming** - SQL and database programming questions

### 💻 Code Features
- **Syntax Highlighting** - Code is displayed with proper syntax highlighting using Prism.js
- **Language Detection** - Automatically detects programming language from code blocks
- **Multiple Output Formats** - Questions can ask about:
  - Program output
  - Error identification
  - Time complexity analysis
  - Data structure identification
  - Code purpose analysis
  - Algorithm behavior

## How to Use

### 1. Database Setup
First, add programming topics to your database:

```sql
-- Run the add_programming_topics.sql script
sqlcmd -S localhost -d MCQGen -i add_programming_topics.sql
```

### 2. Frontend Usage

1. **Select Programming Topic**: Choose a programming-related topic from the dropdown
2. **Enable Programming Question**: Check the "💻 Programming Question (with code snippets)" checkbox
3. **Generate Question**: Click "Generate Question" to create a programming question

### 3. Backend API

The API now supports the `is_programming_question` parameter:

```json
{
  "course_id": 1,
  "stream_id": 1,
  "subject_id": 1,
  "topic_id": 1,
  "question_type_id": 1,
  "difficulty_level_id": 1,
  "bloom_level_id": 1,
  "question_type": "MCQ",
  "requires_diagram": false,
  "requires_option_diagrams": false,
  "is_programming_question": true,
  "custom_prompt": "Generate a Java question about loops",
  "num_questions": 1
}
```

## Question Types Generated

### 1. Output Analysis Questions
```
What will be the output of the following code?
```
Code snippet showing loops, conditionals, functions, etc.

### 2. Error Identification Questions
```
Identify the error in the given code snippet
```
Code with intentional errors for students to identify

### 3. Time Complexity Questions
```
What is the time complexity of the following algorithm?
```
Algorithm implementation with complexity analysis

### 4. Data Structure Questions
```
Identify the data structure used in the code
```
Code implementing various data structures

### 5. Code Purpose Questions
```
What is the purpose of the following code?
```
Code snippets with clear functionality

## Example Questions

### Java Programming Example
**Question**: What will be the output of the following code?

```java
public class Main {
    public static void main(String[] args) {
        int x = 5;
        System.out.println(x++);
        System.out.println(x);
    }
}
```

**Options**:
- A) 5, 5
- B) 5, 6  
- C) 6, 6
- D) 6, 5

**Answer**: B
**Explanation**: The post-increment operator (x++) returns the current value (5) and then increments x to 6.

### C++ Programming Example
**Question**: What will happen when this code is executed?

```cpp
#include <iostream>
using namespace std;
int main() {
    int i;
    for (i = 0; i < 5; i++);
    {
        cout << i;
    }
    return 0;
}
```

**Options**:
- A) Prints 0,1,2,3,4
- B) Prints 5
- C) Prints nothing
- D) Compilation error

**Answer**: B
**Explanation**: The semicolon after the for loop makes it an empty loop that runs 5 times, then i=5 is printed.

## Technical Implementation

### Backend Changes

1. **Enhanced OpenAI Service** (`app/services/openai_service.py`):
   - Added `generate_programming_question_prompt()` function
   - Enhanced parsing to handle code snippets
   - Added programming topic detection

2. **Database Schema**:
   - Added programming subjects and topics
   - Supports code snippet storage

### Frontend Changes

1. **Syntax Highlighting**:
   - Added Prism.js for code syntax highlighting
   - Supports multiple programming languages
   - Dark theme for code blocks

2. **Code Display**:
   - Automatic code snippet extraction
   - Language detection and labeling
   - Proper formatting and styling

3. **User Interface**:
   - Added "Programming Question" checkbox
   - Enhanced question display with code blocks
   - Improved styling for programming questions

## Testing

Run the test script to verify the feature:

```bash
python test_programming_questions.py
```

This will test:
- Programming question generation
- Code snippet inclusion
- Regular question generation (without code)
- API response validation

## Customization

### Adding New Programming Languages

1. **Update the prompt function** in `openai_service.py`:
```python
elif 'javascript' in topic.lower():
    language = 'JavaScript'
    code_example = '''
function test() {
    let x = 5;
    console.log(x++);
    console.log(x);
}
'''
```

2. **Add language support** to Prism.js in the frontend

### Custom Prompts

You can provide specific instructions for programming questions:

```
"Generate a Python question about recursion with a factorial function"
"Create a Java question about inheritance with a class hierarchy"
"Make a C++ question about pointers and memory management"
```

## Best Practices

1. **Question Quality**:
   - Ensure code is syntactically correct
   - Make output predictable and calculable
   - Include realistic distractors in options

2. **Code Complexity**:
   - Start with simple concepts for basic questions
   - Increase complexity for advanced topics
   - Balance readability with educational value

3. **Language-Specific Features**:
   - Use language-specific syntax and conventions
   - Include common programming patterns
   - Test edge cases and common mistakes

## Troubleshooting

### Common Issues

1. **No Code Snippet Generated**:
   - Check if `is_programming_question` is set to `true`
   - Verify the topic is programming-related
   - Check OpenAI API response for errors

2. **Syntax Highlighting Not Working**:
   - Ensure Prism.js is loaded
   - Check browser console for JavaScript errors
   - Verify language detection is working

3. **Database Connection Issues**:
   - Run the SQL script to add programming topics
   - Check database connection settings
   - Verify topic IDs are correct

### Debug Mode

Enable debug logging in the backend:
```python
# In openai_service.py
print(f"🔍 Debug: Programming topic detected: {is_programming_topic}")
print(f"🔍 Debug: Generated prompt: {prompt[:200]}...")
```

## Future Enhancements

1. **Additional Languages**: Support for JavaScript, C#, Go, Rust
2. **Interactive Code**: Code execution and output verification
3. **Code Complexity Analysis**: Automatic difficulty assessment
4. **Programming Patterns**: Questions about design patterns and best practices
5. **Debugging Questions**: Questions that require finding and fixing bugs

## Support

For issues or questions about the programming questions feature:
1. Check the logs for error messages
2. Run the test script to verify functionality
3. Review the API documentation
4. Check the database for programming topics

---

**Note**: This feature requires an active OpenAI API key and proper database setup. Make sure all dependencies are installed and the server is running correctly. 