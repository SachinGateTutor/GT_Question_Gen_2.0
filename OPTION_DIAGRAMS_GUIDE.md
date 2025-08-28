# 🖼️ Option Diagrams Feature Guide

## Overview

The AI MCQ Generator now supports **image-based ABCD options** with a user-controlled checkbox system. Users can choose whether to include diagrams in the question options (A, B, C, D) in addition to the main question diagram.

## ✨ New Features

### 1. User Interface Enhancements

#### Frontend Changes (`index.html`)
- **New Checkbox**: "🖼️ Include Diagrams in Options (A, B, C, D)"
- **Updated Label**: "📊 Include Question Diagram" (renamed for clarity)
- **Responsive Layout**: Option images display alongside text with proper spacing

#### Visual Design
```css
/* Option with image layout */
.option {
    display: flex;
    align-items: center;
    gap: 15px;
}

.option-image {
    max-width: 150px;
    max-height: 100px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
```

### 2. Backend Processing

#### OpenAI Service (`app/services/openai_service.py`)
- **Enhanced Prompting**: Generates 4 separate diagrams for options A, B, C, D
- **Code Parsing**: Extracts individual Python code blocks for each option
- **Library Selection**: Automatically chooses best library for option diagrams

#### Main API (`app/main.py`)
- **Multiple Diagram Rendering**: Renders up to 5 diagrams per question (1 main + 4 options)
- **Response Structure**: Includes `option_images` array in API response

### 3. Database Integration

The system utilizes existing database columns:
```sql
-- Existing columns that now get populated
ImgOptionA, ImgOptionB, ImgOptionC, ImgOptionD
HtmlOptionA, HtmlOptionB, HtmlOptionC, HtmlOptionD
```

## 🔧 How It Works

### 1. User Selection
```
☐ Include Question Diagram
☐ Include Diagrams in Options (A, B, C, D)  ← NEW
```

### 2. AI Processing
When option diagrams are requested:
1. **Library Selection**: AI chooses best library for the subject/topic
2. **Question Generation**: Creates question with 4 distinct option concepts
3. **Diagram Generation**: Creates 5 separate diagrams:
   - 1 main question diagram
   - 4 option-specific diagrams (A, B, C, D)

### 3. Response Format
```json
{
  "question_text": "What type of tree is shown?",
  "options": ["Binary Tree", "AVL Tree", "Red-Black Tree", "B-Tree"],
  "correct_answer": "A",
  "diagram_image_url": "/static/images/main_diagram.png",
  "option_images": [
    "/static/images/option_a.png",
    "/static/images/option_b.png", 
    "/static/images/option_c.png",
    "/static/images/option_d.png"
  ]
}
```

## 🎯 Use Cases

### Perfect For:
- **Data Structures**: Different tree types, graph structures
- **Electronics**: Circuit variations, component arrangements
- **Mathematics**: Different geometric shapes, function plots
- **Computer Networks**: Network topologies, routing diagrams
- **Software Engineering**: Different UML diagrams, flowcharts

### Example Scenarios:
1. **Binary Trees**: Each option shows a different tree structure
2. **Logic Gates**: Each option displays different gate combinations
3. **Network Topologies**: Each option shows different network layouts
4. **Geometric Shapes**: Each option shows different geometric configurations

## 🚀 Implementation Details

### Frontend Changes
```javascript
// New form field
requires_option_diagrams: formData.get('requiresOptionDiagrams') === 'on'

// Enhanced option display
function generateOptionsHTML(options, correctAnswer, optionImages = null) {
    // Displays text + image for each option
}
```

### Backend Changes
```python
# New parameter
requires_option_diagrams = data.get('requires_option_diagrams', False)

# Enhanced prompt generation
if requires_option_diagrams:
    prompt += option_diagram_instructions

# Multiple diagram rendering
for option in ['A', 'B', 'C', 'D']:
    option_code = option_diagram_codes.get(option)
    if option_code:
        option_image = render_diagram(option_code, library_used, output_folder)
```

## 📊 Performance Considerations

### Processing Time
- **Text-only questions**: ~10-15 seconds
- **With main diagram**: ~15-20 seconds  
- **With option diagrams**: ~25-35 seconds

### Storage Impact
- **Main diagram**: ~50-100KB per question
- **Option diagrams**: ~200-400KB per question (4 × 50-100KB)
- **Total per question**: ~250-500KB

## 🧪 Testing

### Test Script
```bash
python test_option_diagrams.py
```

### Manual Testing
1. Check "🖼️ Include Diagrams in Options"
2. Generate question
3. Verify 4 option images appear alongside text
4. Check review page displays option images correctly

## 🔄 Backward Compatibility

### Existing Features
- ✅ Text-only questions work unchanged
- ✅ Main question diagrams work unchanged
- ✅ Review page handles both old and new formats
- ✅ Database schema supports both formats

### Migration
- No database migration required
- Existing questions continue to work
- New questions can use option diagrams

## 🎨 Customization

### Image Sizing
```css
.option-image {
    max-width: 150px;  /* Adjust as needed */
    max-height: 100px; /* Adjust as needed */
}
```

### Layout Options
```css
/* Horizontal layout (current) */
.option { display: flex; align-items: center; }

/* Vertical layout (alternative) */
.option { display: block; }
.option-image { display: block; margin-top: 10px; }
```

## 🐛 Troubleshooting

### Common Issues

1. **No option images generated**
   - Check if checkbox is enabled
   - Verify OpenAI API key is valid
   - Check server logs for errors

2. **Images not displaying**
   - Verify image files exist in `/static/images/`
   - Check file permissions
   - Verify image URLs in browser dev tools

3. **Performance issues**
   - Consider reducing image quality
   - Implement caching for generated images
   - Use CDN for image delivery

### Debug Commands
```bash
# Check generated images
ls -la app/static/images/

# Test API directly
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"requires_option_diagrams": true, ...}'
```

## 🚀 Future Enhancements

### Potential Improvements
1. **Image Optimization**: Compress generated images
2. **Caching**: Cache frequently used diagrams
3. **CDN Integration**: Serve images from CDN
4. **Interactive Diagrams**: Clickable option images
5. **Custom Libraries**: User-selectable diagram libraries

### Advanced Features
1. **Diagram Templates**: Pre-defined diagram styles
2. **Batch Processing**: Generate multiple questions with option diagrams
3. **Export Options**: Export questions with embedded images
4. **Analytics**: Track which option diagrams are most effective

---

## 📝 Summary

The option diagrams feature transforms the MCQ generator from text-only to a rich visual experience. Users can now create questions where each answer choice is accompanied by a relevant diagram, making complex concepts easier to understand and more engaging for students.

**Key Benefits:**
- 🎯 **Enhanced Learning**: Visual aids for each option
- 🎨 **Rich Content**: Multiple diagrams per question
- 🔧 **User Control**: Optional feature via checkbox
- 📱 **Responsive**: Works on all device sizes
- 🔄 **Compatible**: Doesn't break existing functionality 