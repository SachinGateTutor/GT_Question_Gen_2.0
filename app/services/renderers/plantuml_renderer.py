import subprocess
import tempfile
import os
import shutil
import uuid
import traceback

def render(code: str, output_path: str):
    """Render PlantUML diagram using local JAR file"""
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate unique .puml filename
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".puml") as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    print(f"📝 PlantUML file written to: {tmp_path}")

    try:
        # Check if PlantUML JAR exists in tools directory
        jar_path = os.path.join(os.path.dirname(__file__), '../../tools/plantuml.jar')
        
        if not os.path.exists(jar_path):
            # Try alternative locations
            jar_path = os.path.join(os.path.dirname(__file__), '../../../tools/plantuml.jar')
            
        if not os.path.exists(jar_path):
            print("❌ PlantUML JAR not found. Please download plantuml.jar to the tools directory.")
            return None

        # Run PlantUML using the local JAR
        subprocess.run([
            "java", "-jar", jar_path,
            "-tpng", tmp_path,
            "-o", os.path.dirname(output_path)
        ], check=True, capture_output=True)

        # Construct expected output filename
        generated_path = os.path.join(os.path.dirname(output_path),
                                      os.path.basename(tmp_path).replace(".puml", ".png"))

        if not os.path.exists(generated_path):
            raise FileNotFoundError("❌ PlantUML rendering failed. No image generated.")

        shutil.move(generated_path, output_path)
        print(f"✅ PlantUML diagram saved to: {output_path}")
        return os.path.basename(output_path)

    except subprocess.CalledProcessError as e:
        print("❌ PlantUML failed:")
        print(e.stderr.decode(errors='ignore'))

        # Fallback: save a default error diagram
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".puml") as error_file:
            error_file.write("""
            @startuml
            skinparam backgroundColor #FFDDDD
            class Error {
                +message : "PlantUML syntax error"
                +hint : "Check syntax near relationships or brackets"
            }
            @enduml
            """)
            error_path = error_file.name

        print("🔁 Retrying with fallback error diagram...")

        try:
            subprocess.run([
                "java", "-jar", jar_path,
                "-tpng", error_path,
                "-o", os.path.dirname(output_path)
            ], check=True)

            fallback_output = os.path.join(os.path.dirname(output_path),
                                           os.path.basename(error_path).replace(".puml", ".png"))
            shutil.move(fallback_output, output_path)
            print(f"⚠️ Fallback image saved at: {output_path}")
            return os.path.basename(output_path)
        except Exception as fallback_error:
            print("❌ Failed to generate fallback image:", fallback_error)
            return None

    except Exception as e:
        print(f"❌ PlantUML rendering error: {e}")
        traceback.print_exc()
        return None

    finally:
        # Clean up temp files
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if 'error_path' in locals() and os.path.exists(error_path):
            os.unlink(error_path) 