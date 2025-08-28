# Tools Directory

This directory contains external tools needed for diagram rendering.

## PlantUML

To enable PlantUML diagram rendering, download the PlantUML JAR file:

1. Download from: https://plantuml.com/download
2. Save as `plantuml.jar` in this directory
3. Ensure Java is installed on your system

The PlantUML renderer will automatically detect and use this JAR file for generating UML diagrams.

## Installation

```bash
# Download PlantUML JAR (if not already present)
wget https://github.com/plantuml/plantuml/releases/download/v1.2023.10/plantuml-1.2023.10.jar -O plantuml.jar

# Or download manually from: https://plantuml.com/download
```

## Requirements

- Java Runtime Environment (JRE) 8 or higher
- Python 3.7+ with required packages (see requirements.txt) 