import requests
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetBackendService:
    """Service to communicate with .NET backend API"""
    
    def __init__(self, base_url: str = None):
        # Get base URL from environment variable or use default
        self.base_url = base_url or os.getenv('NET_BACKEND_URL', 'http://192.168.0.102:5125')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check if .NET backend is available"""
        try:
            # Try multiple possible health endpoints
            health_endpoints = [
                "/api/health",
                "/health",
                "/api/question-master/ai-service-status",
                "/swagger/index.html"  # Fallback to check if service is running
            ]
            
            for endpoint in health_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        return {
                            'success': True,
                            'status_code': response.status_code,
                            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                            'endpoint_used': endpoint
                        }
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        return {
                            'success': False,
                            'status_code': response.status_code,
                            'error': f"HTTP {response.status_code}",
                            'endpoint_tried': endpoint
                        }
                except requests.exceptions.RequestException:
                    continue  # Try next endpoint
            
            # If all endpoints failed, return error
            return {
                'success': False,
                'status_code': None,
                'error': 'No health endpoint found',
                'endpoints_tried': health_endpoints
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'success': False,
                'status_code': None,
                'error': str(e)
            }
    
    def store_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store generated question in .NET backend database using two-step process"""
        try:
            logger.info(f"Starting two-step question storage process...")
            
            # Step 1: Create Question Master record
            question_master_payload = {
                'subjectID': question_data.get('subject_id'),
                'topicID': question_data.get('topic_id'),
                'topicTypeID': question_data.get('section_id', 0),  # Same as sectionID
                'questionTypeID': question_data.get('question_type_id', 1),
                'marks': question_data.get('marks', 1),
                'bloomLevelID': question_data.get('bloom_level_id', 1),
                'difficultyLevelID': question_data.get('difficulty_level_id', 1),
                'sectionID': question_data.get('section_id', 0),
                'groupID': 264,  # Hardcoded as specified
                'isPublic': True,
                'addedBy': 0,
                'isAIGenerated': True,
                'diagramCode': question_data.get('diagram_code') or None,
                'createdDate': datetime.now().isoformat() + 'Z'
            }
            
            # Remove None values
            question_master_payload = {k: v for k, v in question_master_payload.items() if v is not None}
            
            logger.info(f"Creating Question Master record with payload: {question_master_payload}")
            
            # Create Question Master record
            question_master_response = self.session.post(
                f"{self.base_url}/api/question-master",
                json=question_master_payload,
                timeout=30
            )
            
            if question_master_response.status_code not in [200, 201]:
                logger.error(f"Failed to create Question Master record: {question_master_response.status_code} - {question_master_response.text}")
                return {
                    'success': False,
                    'error': f"Question Master creation failed: {question_master_response.status_code} - {question_master_response.text}"
                }
            
            # Extract questionID from response (response body is just the number)
            try:
                question_id = int(question_master_response.text.strip())
                logger.info(f"Question Master record created successfully with ID: {question_id}")
            except ValueError:
                logger.error(f"Invalid question ID response: {question_master_response.text}")
                return {
                    'success': False,
                    'error': f"Invalid question ID response: {question_master_response.text}"
                }
            
            # Step 2: Insert MCQ content using the questionID
            # Convert correct_answer from text to letter (A, B, C, D)
            correct_option = self._convert_answer_to_option_letter(
                question_data.get('correct_answer', ''),
                question_data.get('options', [])
            )
            
            mcq_payload = {
                'questionID': question_id,
                'questionText': question_data.get('question_text', ''),
                'optionA': question_data.get('options', [''])[0] if len(question_data.get('options', [])) > 0 else '',
                'optionB': question_data.get('options', [''])[1] if len(question_data.get('options', [])) > 1 else '',
                'optionC': question_data.get('options', [''])[2] if len(question_data.get('options', [])) > 2 else '',
                'optionD': question_data.get('options', [''])[3] if len(question_data.get('options', [])) > 3 else '',
                'correctOption': correct_option,
                'hasImage': False,
                'imgQuestion': None,
                'imgOptionA': None,
                'imgOptionB': None,
                'imgOptionC': None,
                'imgOptionD': None,
                'htmlQuestion': None,
                'htmlOptionA': None,
                'htmlOptionB': None,
                'htmlOptionC': None,
                'htmlOptionD': None
            }
            
            logger.info(f"Inserting MCQ content with payload: {mcq_payload}")
            
            # Insert MCQ content
            mcq_response = self.session.post(
                f"{self.base_url}/api/mcq/add",
                json=mcq_payload,
                timeout=30
            )
            
            if mcq_response.status_code not in [200, 201]:
                logger.error(f"Failed to insert MCQ content: {mcq_response.status_code} - {mcq_response.text}")
                return {
                    'success': False,
                    'error': f"MCQ insertion failed: {mcq_response.status_code} - {mcq_response.text}"
                }
            
            # Step 3: Store explanation if available
            explanation_stored = False
            if question_data.get('explanation'):
                try:
                    explanation_result = self._store_explanation(question_id, question_data.get('explanation'))
                    if explanation_result:
                        explanation_stored = True
                        logger.info(f"Explanation stored successfully for question {question_id}")
                    else:
                        logger.warning(f"Failed to store explanation for question {question_id}")
                except Exception as e:
                    logger.warning(f"Error storing explanation: {e}")
            
            logger.info(f"Question stored successfully in .NET backend via two-step process")
            return {
                'success': True,
                'question_id': question_id,
                'response': {
                    'question_master_id': question_id,
                    'mcq_inserted': True,
                    'explanation_stored': explanation_stored
                },
                'endpoint_used': 'Two-step: /api/question-master + /api/mcq/add'
            }
                
        except Exception as e:
            logger.error(f"Error storing question in .NET backend: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_explanation(self, question_id: int, explanation_text: str) -> bool:
        """Store explanation for a question in .NET backend using the correct API endpoint"""
        try:
            # Use the correct API endpoint for explanations
            endpoint = "/api/QuestionExplanation/add-or-update"
            
            explanation_payload = {
                'questionID': question_id,
                'explanationText': explanation_text,
                'htmlExplanation': None,  # We don't have HTML explanation
                'imgExplanation': None,   # We don't have image explanation
                'legacySourceType': 'AI_Generated',  # Mark as AI generated
                'explanationType': 'Standard',        # Standard explanation type
                'userID': 0  # System generated
            }
            
            logger.info(f"Storing explanation for question {question_id} via {endpoint}")
            
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=explanation_payload,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Explanation stored successfully for question {question_id}")
                return True
            else:
                logger.error(f"Explanation storage failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing explanation: {str(e)}")
            return False
    
    def _convert_answer_to_option_letter(self, correct_answer: str, options: list) -> str:
        """Convert the correct answer text to option letter (A, B, C, D)"""
        if not correct_answer or not options:
            return 'A'  # Default fallback
        
        # Clean the answer text (remove LaTeX, extra spaces, etc.)
        clean_answer = correct_answer.strip()
        
        # Find which option matches the correct answer
        for i, option in enumerate(options):
            if option and option.strip() == clean_answer:
                return chr(65 + i)  # Convert 0,1,2,3 to A,B,C,D
        
        # If no exact match, try partial matching
        for i, option in enumerate(options):
            if option and clean_answer in option.strip():
                return chr(65 + i)
        
        # If still no match, return first option as fallback
        logger.warning(f"Could not match correct answer '{correct_answer}' to any option, defaulting to 'A'")
        return 'A'
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get generation status from .NET backend"""
        try:
            # Try multiple possible status endpoints
            status_endpoints = [
                f"/api/question-master/generation-status/{generation_id}",
                f"/api/generation-status/{generation_id}",
                f"/api/question-master/status/{generation_id}"
            ]
            
            for endpoint in status_endpoints:
                try:
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=15  # Increased timeout
                    )
                    
                    if response.status_code == 200:
                        return {
                            'success': True,
                            'status_data': response.json(),
                            'endpoint_used': endpoint
                        }
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        logger.warning(f"Status check failed via {endpoint}: {response.status_code}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Status request failed for {endpoint}: {e}")
                    continue
            
            # If all endpoints failed, return error
            return {
                'success': False,
                'error': 'No working status endpoint found',
                'endpoints_tried': status_endpoints
            }
                
        except Exception as e:
            logger.error(f"Error getting generation status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
net_backend_service = NetBackendService() 