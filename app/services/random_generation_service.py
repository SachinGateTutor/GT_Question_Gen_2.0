import threading
import uuid
import os
import sys
from datetime import datetime
from .openai_service import generate_mcq_and_diagram
from .diagram_service_new import render_diagram
from .net_backend_service import NetBackendService

class RandomGenerationService:
    def __init__(self):
        self.active_generations = {}
        self.net_backend = NetBackendService()
    
    def analyze_topic(self, topic_info, question_type):
        """Analyze topic and return AI recommendations for question distribution"""
        from .openai_service import ai_analyze_topic
        return ai_analyze_topic(topic_info, question_type)
    
    def generate_questions_background(self, generation_id, request_data, question_plan):
        """Generate questions in background thread"""
        try:
            # Initialize progress tracking
            self.active_generations[generation_id] = {
                'status': 'active',
                'progress': {
                    'current': 0,
                    'total': question_plan['total_questions'],
                    'diagram_current': 0,
                    'diagram_total': question_plan['diagram_questions'],
                    'option_diagram_current': 0,
                    'option_diagram_total': question_plan['option_diagram_questions'],
                    'text_only_current': 0,
                    'text_only_total': question_plan['text_only_questions'],
                    'code_current': 0,
                    'code_total': question_plan['code_questions']
                },
                'generated_questions': [],
                'start_time': datetime.now()
            }
            
            # Generate questions based on plan
            question_types = []
            
            # Add diagram questions
            for _ in range(question_plan['diagram_questions']):
                question_types.append('diagram')
            
            # Add option diagram questions
            for _ in range(question_plan['option_diagram_questions']):
                question_types.append('option_diagram')
            
            # Add text-only questions
            for _ in range(question_plan['text_only_questions']):
                question_types.append('text_only')
            
            # Add code questions
            for _ in range(question_plan['code_questions']):
                question_types.append('code')
            
            # Generate each question
            for i, question_type in enumerate(question_types):
                if self.active_generations[generation_id]['status'] == 'stopped':
                    break
                
                try:
                    # Generate single question
                    question_data = self.generate_single_question(request_data, question_type)
                    
                    # Store in .NET backend
                    if question_data:
                        try:
                            # Store question in .NET backend
                            storage_result = self.net_backend.store_question(question_data)
                            if storage_result.get('success'):
                                print(f" Question stored successfully with ID: {storage_result.get('question_id')}")
                                question_data['question_id'] = storage_result.get('question_id')
                                self.active_generations[generation_id]['generated_questions'].append(question_data)
                            else:
                                print(f" Failed to store question: {storage_result.get('error', 'Unknown error')}")
                        except Exception as e:
                            print(f" Error storing question in .NET backend: {e}")
                    
                    # Update progress
                    self.active_generations[generation_id]['progress']['current'] += 1
                    if question_type == 'diagram':
                        self.active_generations[generation_id]['progress']['diagram_current'] += 1
                    elif question_type == 'option_diagram':
                        self.active_generations[generation_id]['progress']['option_diagram_current'] += 1
                    elif question_type == 'text_only':
                        self.active_generations[generation_id]['progress']['text_only_current'] += 1
                    elif question_type == 'code':
                        self.active_generations[generation_id]['progress']['code_current'] += 1
                        
                except Exception as e:
                    print(f"Error generating question {i+1}: {e}")
                    continue
            
            # Mark as completed
            self.active_generations[generation_id]['status'] = 'completed'
            self.active_generations[generation_id]['end_time'] = datetime.now()
            
        except Exception as e:
            print(f"Background generation error: {e}")
            self.active_generations[generation_id]['status'] = 'error'
            self.active_generations[generation_id]['error'] = str(e)
    
    def generate_single_question(self, request_data, question_type):
        """Generate a single question based on type with proper diagram handling"""
        try:
            # Prepare request data
            enhanced_request = request_data.copy()
            
            # Get topic name from database using topic_id
            topic_id = enhanced_request.get('topic_id')
            if topic_id:
                try:
                    from .db_service import get_topic_name_by_id
                    topic_name = get_topic_name_by_id(topic_id)
                    if topic_name:
                        enhanced_request['topic'] = topic_name
                        print(f" Debug: Retrieved topic name: {topic_name} for topic_id: {topic_id}")
                    else:
                        print(f" Warning: Could not find topic name for topic_id: {topic_id}")
                except Exception as e:
                    print(f" Warning: Error retrieving topic name: {e}")
            
            # Get subject name from database using subject_id
            subject_id = enhanced_request.get('subject_id')
            if subject_id:
                try:
                    from .db_service import get_subject_name_by_id
                    subject_name = get_subject_name_by_id(subject_id)
                    if subject_name:
                        enhanced_request['subject'] = subject_name
                        print(f" Debug: Retrieved subject name: {subject_name} for subject_id: {subject_id}")
                    else:
                        print(f" Warning: Could not find subject name for subject_id: {subject_id}")
                except Exception as e:
                    print(f" Warning: Error retrieving subject name: {e}")
            
            # Get stream name from database using stream_id
            stream_id = enhanced_request.get('stream_id')
            if stream_id:
                try:
                    from .db_service import get_stream_name_by_id
                    stream_name = get_stream_name_by_id(stream_id)
                    if stream_name:
                        enhanced_request['stream'] = stream_name
                        print(f" Debug: Retrieved stream name: {stream_name} for stream_id: {stream_id}")
                    else:
                        print(f" Warning: Could not find stream name for stream_id: {stream_id}")
                except Exception as e:
                    print(f" Warning: Error retrieving stream name: {e}")
            
            # Modify request based on question type
            if question_type == 'diagram':
                enhanced_request['requires_diagram'] = True
                enhanced_request['requires_option_diagrams'] = False
            elif question_type == 'option_diagram':
                enhanced_request['requires_diagram'] = False
                enhanced_request['requires_option_diagrams'] = True
            elif question_type == 'code':
                enhanced_request['is_programming_question'] = True
            else:  # text_only
                enhanced_request['requires_diagram'] = False
                enhanced_request['requires_option_diagrams'] = False
                enhanced_request['is_programming_question'] = False
            
            # Generate question using existing service
            generated_data = generate_mcq_and_diagram(enhanced_request)
            
            # Handle diagram rendering if needed
            if generated_data.get('diagram_code'):
                try:
                    # Set the output folder for diagram images
                    output_folder = os.path.join(os.path.dirname(__file__), 'static', 'images')
                    diagram_result = render_diagram(generated_data['diagram_code'], generated_data['library_used'], output_folder)
                    
                    # Handle the result - it could be a string (filename) or dict
                    if isinstance(diagram_result, str):
                        # It's a filename, create the full path
                        generated_data['diagram_image_url'] = f"/static/images/{diagram_result}"
                    elif isinstance(diagram_result, dict) and diagram_result.get('image_url'):
                        generated_data['diagram_image_url'] = diagram_result['image_url']
                    else:
                        generated_data['diagram_image_url'] = None
                        
                except Exception as e:
                    print(f"Diagram rendering error: {e}")
                    generated_data['diagram_image_url'] = None
            
            # Handle option diagrams if needed
            if generated_data.get('option_diagram_codes'):
                option_images = []
                for option, code in generated_data['option_diagram_codes'].items():
                    if code:
                        try:
                            output_folder = os.path.join(os.path.dirname(__file__), 'static', 'images')
                            diagram_result = render_diagram(code, generated_data['library_used'], output_folder)
                            
                            if isinstance(diagram_result, str):
                                option_images.append(f"/static/images/{diagram_result}")
                            elif isinstance(diagram_result, dict) and diagram_result.get('image_url'):
                                option_images.append(diagram_result['image_url'])
                            else:
                                option_images.append(None)
                                
                        except Exception as e:
                            print(f"Option diagram rendering error: {e}")
                            option_images.append(None)
                    else:
                        option_images.append(None)
                generated_data['option_images'] = option_images
            
            # Merge with original request data for database storage
            final_data = {**request_data, **generated_data}
            
            # Convert string IDs to integers for database storage
            if 'subject_id' in final_data and isinstance(final_data['subject_id'], str):
                final_data['subject_id'] = int(final_data['subject_id'])
            if 'topic_id' in final_data and isinstance(final_data['topic_id'], str):
                final_data['topic_id'] = int(final_data['topic_id'])
            if 'question_type_id' in final_data and isinstance(final_data['question_type_id'], str):
                final_data['question_type_id'] = int(final_data['question_type_id'])
            if 'course_id' in final_data and isinstance(final_data['course_id'], str):
                final_data['course_id'] = int(final_data['course_id'])
            if 'stream_id' in final_data and isinstance(final_data['stream_id'], str):
                final_data['stream_id'] = int(final_data['stream_id'])
            
            return final_data
            
        except Exception as e:
            print(f"Error in generate_single_question: {e}")
            return None
    
    def get_generation_progress(self, generation_id):
        """Get progress for a specific generation"""
        if generation_id in self.active_generations:
            return self.active_generations[generation_id]
        return None
    
    def stop_generation(self, generation_id):
        """Stop an ongoing generation"""
        if generation_id in self.active_generations:
            self.active_generations[generation_id]['status'] = 'stopped'
            return True
        return False
    
    def cleanup_generation(self, generation_id):
        """Clean up completed generations"""
        if generation_id in self.active_generations:
            del self.active_generations[generation_id]

# Global instance
random_generation_service = RandomGenerationService() 