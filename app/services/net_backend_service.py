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


def coerce_stream_id(value: Any) -> Optional[int]:
    """Treat missing or non-positive stream IDs (including JWT 0) as unset."""
    if value is None or value == '':
        return None
    try:
        stream_id = int(value)
    except (TypeError, ValueError):
        return None
    return stream_id if stream_id > 0 else None


def _log_safe(value: object, max_len: int = 800) -> str:
    """Narrow-console-safe log text (e.g. Windows cp1252) when API bodies contain Unicode."""
    s = "" if value is None else str(value)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s.encode("ascii", errors="backslashreplace").decode("ascii")


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
    
    def store_question(self, question_data: Dict[str, Any], auth_token: str = None, user_id: str = None, user_type_id: int = None) -> Dict[str, Any]:
        """Store generated question in .NET backend database using two-step process"""
        try:
            logger.info(f"Starting two-step question storage process...")
            
            # Prepare headers with token if provided
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

            # Convert correct_answer before Question Master create so misu can be sent
            correct_option = self._convert_answer_to_option_letter(
                question_data.get('correct_answer', ''),
                question_data.get('options', [])
            )
            if not correct_option:
                return {
                    'success': False,
                    'error': "Could not determine correct answer option (A/B/C/D) from AI response.",
                    'error_type': 'answer_mapping_failed'
                }
            misu = {'A': 1, 'B': 2, 'C': 3, 'D': 4}.get(str(correct_option).strip().upper())
            
            # Step 1: Create Question Master record
            raw_group_id = question_data.get('group_id')
            if raw_group_id is None:
                raw_group_id = question_data.get('groupId')
            try:
                effective_group_id = int(raw_group_id) if raw_group_id is not None else 0
            except (TypeError, ValueError):
                logger.warning(f"Invalid group_id '{raw_group_id}', using fallback groupID 0")
                effective_group_id = 0

            request_stream_id = coerce_stream_id(question_data.get('stream_id'))
            if request_stream_id is None:
                request_stream_id = coerce_stream_id(
                    question_data.get('streamID') or question_data.get('streamId')
                )

            if user_type_id is None:
                user_type_id = self._extract_user_type_id_from_token(auth_token)
            try:
                user_type_id = int(user_type_id) if user_type_id is not None else None
            except (TypeError, ValueError):
                user_type_id = None
            # user_type_id 0 => counter 1; any other/missing value => counter 0
            counter = 1 if user_type_id == 0 else 0

            question_master_payload = {
                'subjectID': question_data.get('subject_id'),
                'topicID': question_data.get('topic_id'),
                'topicTypeID': question_data.get('section_id', 0),  # Same as sectionID
                'questionTypeID': question_data.get('question_type_id', 1),
                'marks': question_data.get('marks', 1),
                'bloomLevelID': question_data.get('bloom_level_id', 1),
                'difficultyLevelID': question_data.get('difficulty_level_id', 1),
                'sectionID': question_data.get('section_id', 0),
                'groupID': effective_group_id,
                'isPublic': True,
                'addedBy': 0,
                'isAIGenerated': True,
                'diagramCode': question_data.get('diagram_code') or None,
                'createdDate': datetime.now().isoformat() + 'Z',
                'questionsGeneratedBy': user_id or '',  # User ID from JWT token
                'SourceSystem': 'PragyaAI',
                'sourceQuestionID': 0,  # 0 for new questions
                'misu': misu,
                'counter': counter,
            }
            if request_stream_id is not None:
                question_master_payload['streamID'] = request_stream_id
            
            # Handle generationID as optional/nullable - only include if provided
            generation_id = question_data.get('generation_id')
            if generation_id is not None:
                try:
                    # Convert to 32-bit integer (ensure it fits in int32 range: -2,147,483,648 to 2,147,483,647)
                    generation_id_int = int(generation_id)
                    # Clamp to 32-bit signed integer range if needed
                    max_int32 = 2147483647
                    min_int32 = -2147483648
                    if generation_id_int > max_int32:
                        generation_id_int = max_int32
                    elif generation_id_int < min_int32:
                        generation_id_int = min_int32
                    question_master_payload['generationID'] = generation_id_int
                except (ValueError, TypeError):
                    # If conversion fails, skip generationID (nullable field)
                    logger.warning(f"Could not convert generation_id to integer: {generation_id}, skipping generationID field")
            
            # Remove None values
            question_master_payload = {k: v for k, v in question_master_payload.items() if v is not None}
            
            logger.info(f"Creating Question Master record with payload: {question_master_payload}")
            
            # Create Question Master record with auth token
            # Send payload directly (no dto wrapper needed based on Postman tests)
            question_master_response = self.session.post(
                f"{self.base_url}/api/question-master",
                json=question_master_payload,
                headers=headers,
                timeout=30
            )
            
            if question_master_response.status_code not in [200, 201]:
                error_text = question_master_response.text
                logger.error(f"Failed to create Question Master record: {question_master_response.status_code} - {_log_safe(error_text)}")
                
                # Check for CHECK constraint violations
                if "CHECK constraint" in error_text or "CK_QM_QType" in error_text:
                    logger.error(f"Database CHECK constraint violation detected. Payload sent: {question_master_payload}")
                    logger.error(f"This indicates that one of the values (likely questionTypeID={question_master_payload.get('questionTypeID')}) is not allowed by the database constraint.")
                    logger.error(f"Please verify the valid values for QuestionTypeID in the database or update the CHECK constraint.")
                
                return {
                    'success': False,
                    'error': f"Question Master creation failed: {question_master_response.status_code} - {error_text}",
                    'error_type': 'database_constraint' if "CHECK constraint" in error_text else 'api_error'
                }
            
            # Parse JSON response to extract questionId, jkuh, and streamId
            try:
                response_json = question_master_response.json()
                
                # Log full response for debugging
                logger.info(f"Full Question Master API response: {response_json}")
                
                # Handle both camelCase and PascalCase field names
                question_id = (response_json.get('questionId') or 
                             response_json.get('QuestionId') or
                             response_json.get('question_id'))
                jkuh = (response_json.get('jkuh') or 
                       response_json.get('Jkuh') or
                       response_json.get('JKUH'))
                response_stream_id = coerce_stream_id(
                    response_json.get('streamId') or
                    response_json.get('StreamId') or
                    response_json.get('stream_id')
                )

                # Always route later calls with the REQUEST stream, not the .NET read-back.
                # Until the backend is fixed, response streamId/jkuh can come from the default shard (173).
                routing_stream_id = request_stream_id
                if (
                    request_stream_id is not None
                    and response_stream_id is not None
                    and response_stream_id != request_stream_id
                ):
                    logger.warning(
                        f"Question Master response streamId={response_stream_id} does not match "
                        f"request streamID={request_stream_id}. Using request streamID for MCQ/explanation. "
                        f"questionId={question_id}, jkuh={jkuh}"
                    )
                elif routing_stream_id is None and response_stream_id is not None:
                    routing_stream_id = response_stream_id

                logger.info(
                    f"Question Master record created successfully - questionId: {question_id}, "
                    f"jkuh: {jkuh}, requestStreamId: {request_stream_id}, "
                    f"responseStreamId: {response_stream_id}, routingStreamId: {routing_stream_id}"
                )
                
                if not jkuh:
                    logger.error(f"Missing jkuh in response: {response_json}")
                    return {
                        'success': False,
                        'error': f"Missing jkuh in response: {response_json}"
                    }
            except (ValueError, KeyError) as e:
                logger.error(f"Invalid question response format: {_log_safe(question_master_response.text)} - Error: {e}")
                return {
                    'success': False,
                    'error': f"Invalid question response format: {question_master_response.text}"
                }
            
            # Step 2: Insert MCQ content using jkuh (not question_id)
            # Check if question has images
            diagram_image_url = question_data.get('diagram_image_url')
            has_question_image = bool(diagram_image_url)
            has_option_images = bool(question_data.get('option_images') and any(question_data.get('option_images', [])))
            has_images = has_question_image or has_option_images
            
            # Get option images if available
            option_images = question_data.get('option_images', [])
            
            # Log image information
            if has_question_image:
                logger.info(f"Question has diagram image: {diagram_image_url}")
            if has_option_images:
                logger.info(f"Question has option images: {option_images}")
            logger.info(f"Question has images: {has_images}")
            
            explanation_text = question_data.get('explanation')
            if isinstance(explanation_text, str):
                explanation_text = explanation_text.strip() or None
            else:
                explanation_text = None
            
            mcq_payload = {
                'jkuh': jkuh,  # Use jkuh field name as required by MCQ API
                'questionText': question_data.get('question_text', ''),
                'optionA': question_data.get('options', [''])[0] if len(question_data.get('options', [])) > 0 else '',
                'optionB': question_data.get('options', [''])[1] if len(question_data.get('options', [])) > 1 else '',
                'optionC': question_data.get('options', [''])[2] if len(question_data.get('options', [])) > 2 else '',
                'optionD': question_data.get('options', [''])[3] if len(question_data.get('options', [])) > 3 else '',
                'correctOption': correct_option,
                'hasImage': has_images,
                'imgQuestion': question_data.get('diagram_image_url') if has_question_image else None,
                'imgOptionA': option_images[0] if len(option_images) > 0 and option_images[0] else None,
                'imgOptionB': option_images[1] if len(option_images) > 1 and option_images[1] else None,
                'imgOptionC': option_images[2] if len(option_images) > 2 and option_images[2] else None,
                'imgOptionD': option_images[3] if len(option_images) > 3 and option_images[3] else None,
                'htmlQuestion': None,
                'htmlOptionA': None,
                'htmlOptionB': None,
                'htmlOptionC': None,
                'htmlOptionD': None,
                'htmlExplanation': explanation_text
            }
            if routing_stream_id is not None:
                mcq_payload['streamID'] = routing_stream_id
            
            logger.info(f"Inserting MCQ content with payload: {mcq_payload}")
            
            # Insert MCQ content with auth token
            mcq_response = self.session.post(
                f"{self.base_url}/api/mcq/add",
                json=mcq_payload,
                headers=headers,
                timeout=30
            )
            
            if mcq_response.status_code not in [200, 201]:
                logger.error(f"Failed to insert MCQ content: {mcq_response.status_code} - {_log_safe(mcq_response.text)}")
                return {
                    'success': False,
                    'error': f"MCQ insertion failed: {mcq_response.status_code} - {mcq_response.text}"
                }

            # Explanation is stored on the MCQ row via htmlExplanation; skip QuestionExplanation API.
            explanation_stored = bool(explanation_text)
            
            logger.info(f"Question stored successfully in .NET backend via two-step process")
            return {
                'success': True,
                'question_id': question_id,  # questionId from response
                'jkuh': jkuh,  # jkuh - the important ID for MCQ table
                'stream_id': routing_stream_id,  # request streamID used for shard routing
                'response': {
                    'question_master_id': question_id,
                    'jkuh': jkuh,
                    'stream_id': routing_stream_id,
                    'response_stream_id': response_stream_id,
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
    
    def _extract_user_type_id_from_token(self, token: str) -> Optional[int]:
        """Read user_type_id from a JWT payload without verifying the signature."""
        if not token:
            return None
        try:
            import base64
            if token.startswith('Bearer '):
                token = token[7:]
            parts = token.split('.')
            if len(parts) != 3:
                return None
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            for key in ('user_type_id', 'userTypeId', 'UserTypeID', 'UserTypeId', 'usertypeid'):
                if key in decoded and decoded[key] is not None:
                    return int(decoded[key])
        except (TypeError, ValueError, json.JSONDecodeError, Exception):
            logger.warning("Could not extract user_type_id from auth token")
        return None

    def _convert_answer_to_option_letter(self, correct_answer: str, options: list) -> Optional[str]:
        """Convert the correct answer text to option letter (A, B, C, D)"""
        if not correct_answer or not options:
            logger.warning(f"Missing correct_answer or options. correct_answer: {correct_answer}, options: {options}")
            return None
        
        # Clean the answer text (remove LaTeX, extra spaces, etc.)
        clean_answer = correct_answer.strip().upper()
        
        # First check: If the answer is already a valid option letter (A, B, C, D)
        if clean_answer in ['A', 'B', 'C', 'D']:
            logger.info(f"Answer is already a letter: {clean_answer}")
            return clean_answer
        
        # Second check: If answer starts with a letter followed by period or space (e.g., "A.", "B ", "C:")
        if len(clean_answer) >= 1 and clean_answer[0] in ['A', 'B', 'C', 'D']:
            letter = clean_answer[0]
            logger.info(f"Extracted letter from answer: {letter} (from '{correct_answer}')")
            return letter
        
        # Third check: Find which option matches the correct answer text (exact match)
        for i, option in enumerate(options):
            if option and option.strip() == clean_answer:
                letter = chr(65 + i)  # Convert 0,1,2,3 to A,B,C,D
                logger.info(f"Found exact match for answer text at index {i}: {letter}")
                return letter
        
        # Fourth check: Try partial matching (answer text is contained in option)
        for i, option in enumerate(options):
            if option and clean_answer in option.strip():
                letter = chr(65 + i)  # Convert 0,1,2,3 to A,B,C,D
                logger.info(f"Found partial match for answer text at index {i}: {letter}")
                return letter
        
        # Fifth check: Try reverse partial matching (option text is contained in answer)
        for i, option in enumerate(options):
            if option and option.strip() in clean_answer:
                letter = chr(65 + i)  # Convert 0,1,2,3 to A,B,C,D
                logger.info(f"Found reverse partial match for answer text at index {i}: {letter}")
                return letter
        
        # If still no match, fail fast to avoid storing incorrect answer metadata
        logger.error(f"CRITICAL: Could not match correct answer '{correct_answer}' to any option. Options: {options}.")
        return None
    
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
    
    def get_subject_by_id(self, subject_id: int, auth_token: str = None, stream_id: Optional[int] = None, is_aptitude: bool = False, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get subject information by ID from .NET backend unified endpoint"""
        try:
            if is_aptitude:
                if group_id is None:
                    return {
                        'success': False,
                        'error': 'group_id is required for aptitude subject lookup',
                        'subject_name': None
                    }
                return self.get_aptitude_subject_by_id(subject_id, group_id, auth_token=auth_token)

            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            params = {}
            routing_stream_id = coerce_stream_id(stream_id)
            if routing_stream_id is not None:
                params['streamid'] = routing_stream_id
                params['streamId'] = routing_stream_id
            
            response = self.session.get(
                f"{self.base_url}/api/SubjectUnified/{subject_id}",
                headers=headers,
                params=params if params else None,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle both array and single object responses
                if isinstance(response_data, list):
                    # If array, find the subject with matching ID
                    subject_data = None
                    for item in response_data:
                        item_id = (item.get('subjectId') or 
                                 item.get('SubjectID') or
                                 item.get('subject_id'))
                        if item_id == subject_id:
                            subject_data = item
                            break
                    
                    if not subject_data:
                        logger.warning(f"Subject {subject_id} not found in array response")
                        return {
                            'success': False,
                            'error': 'Subject not found in response array',
                            'subject_name': None
                        }
                else:
                    # Single object response
                    subject_data = response_data
                
                # Handle both camelCase and PascalCase field names
                subject_name = (subject_data.get('subjectName') or 
                              subject_data.get('SubjectName') or
                              subject_data.get('subject_name'))
                subject_id_from_response = (subject_data.get('subjectId') or 
                                          subject_data.get('SubjectID') or
                                          subject_data.get('subject_id'))
                
                if subject_name:
                    logger.info(f"Retrieved subject name: {_log_safe(subject_name)} for subject_id: {subject_id}")
                    return {
                        'success': True,
                        'subject_id': subject_id_from_response or subject_id,
                        'subject_name': subject_name,
                        'data': subject_data
                    }
                else:
                    logger.warning(f"Subject {subject_id} response missing subjectName field")
                    return {
                        'success': False,
                        'error': 'Missing subjectName in response',
                        'subject_name': None
                    }
            else:
                logger.warning(f"Failed to get subject {subject_id}: {response.status_code} - {_log_safe(response.text)}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'subject_name': None
                }
                
        except Exception as e:
            logger.error(f"Error getting subject {subject_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'subject_name': None
            }

    def get_aptitude_subject_by_id(self, subject_id: int, group_id: int, auth_token: str = None) -> Dict[str, Any]:
        """Get aptitude subject by ID from aptitude subjects list endpoint"""
        try:
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

            response = self.session.get(
                f"{self.base_url}/api/SubjectUnified/aptitude/subjects",
                headers=headers,
                params={'groupId': int(group_id)},
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"Failed aptitude subjects lookup for group {group_id}: {response.status_code} - {_log_safe(response.text)}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'subject_name': None
                }

            response_data = response.json()
            subjects = response_data.get('subjects', []) if isinstance(response_data, dict) else []
            if not isinstance(subjects, list):
                return {
                    'success': False,
                    'error': 'Invalid aptitude subjects response format',
                    'subject_name': None
                }

            subject_data = None
            for item in subjects:
                item_id = item.get('subjectId') or item.get('SubjectID') or item.get('subject_id')
                if item_id == subject_id:
                    subject_data = item
                    break

            if not subject_data:
                return {
                    'success': False,
                    'error': 'Subject not found in aptitude subjects',
                    'subject_name': None
                }

            subject_name = subject_data.get('subjectName') or subject_data.get('SubjectName') or subject_data.get('subject_name')
            if not subject_name:
                return {
                    'success': False,
                    'error': 'Missing subjectName in aptitude subject response',
                    'subject_name': None
                }

            return {
                'success': True,
                'subject_id': subject_id,
                'subject_name': subject_name,
                'data': subject_data
            }

        except Exception as e:
            logger.error(f"Error getting aptitude subject {subject_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'subject_name': None
            }

    def get_aptitude_topic_by_id(self, topic_id: int, subject_id: int, group_id: int, auth_token: str = None) -> Dict[str, Any]:
        """Get aptitude topic by ID from aptitude topics list endpoint"""
        try:
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

            response = self.session.get(
                f"{self.base_url}/api/SubjectUnified/aptitude/topics",
                headers=headers,
                params={
                    'subjectId': int(subject_id),
                    'groupId': int(group_id)
                },
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"Failed aptitude topics lookup for subject {subject_id}, group {group_id}: {response.status_code} - {_log_safe(response.text)}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'topic_name': None
                }

            response_data = response.json()
            topics = response_data.get('topics', []) if isinstance(response_data, dict) else []
            if not isinstance(topics, list):
                return {
                    'success': False,
                    'error': 'Invalid aptitude topics response format',
                    'topic_name': None
                }

            topic_data = None
            for item in topics:
                item_id = item.get('topicId') or item.get('TopicID') or item.get('topic_id')
                if item_id == topic_id:
                    topic_data = item
                    break

            if not topic_data:
                return {
                    'success': False,
                    'error': 'Topic not found in aptitude topics',
                    'topic_name': None
                }

            topic_name = topic_data.get('topicName') or topic_data.get('TopicName') or topic_data.get('topic_name')
            if not topic_name:
                return {
                    'success': False,
                    'error': 'Missing topicName in aptitude topic response',
                    'topic_name': None
                }

            return {
                'success': True,
                'topic_id': topic_id,
                'topic_name': topic_name,
                'data': topic_data
            }

        except Exception as e:
            logger.error(f"Error getting aptitude topic {topic_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'topic_name': None
            }
    
    def get_topic_by_id(self, topic_id: int, subject_id: int, auth_token: str = None, is_aptitude: bool = False, group_id: Optional[int] = None, stream_id: Optional[int] = None) -> Dict[str, Any]:
        """Get topic information by ID from .NET backend unified endpoint"""
        try:
            if is_aptitude:
                if group_id is None:
                    return {
                        'success': False,
                        'error': 'group_id is required for aptitude topic lookup',
                        'topic_name': None
                    }
                return self.get_aptitude_topic_by_id(topic_id, subject_id, group_id, auth_token=auth_token)

            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'

            params = {}
            routing_stream_id = coerce_stream_id(stream_id)
            if routing_stream_id is not None:
                params['streamid'] = routing_stream_id
                params['streamId'] = routing_stream_id
            
            response = self.session.get(
                f"{self.base_url}/api/TopicUnified/topic/{topic_id}/subject/{subject_id}",
                headers=headers,
                params=params if params else None,
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle both array and single object responses
                if isinstance(response_data, list):
                    # If array, find the topic with matching ID
                    topic_data = None
                    for item in response_data:
                        item_id = (item.get('topicId') or 
                                 item.get('TopicID') or
                                 item.get('topic_id'))
                        if item_id == topic_id:
                            topic_data = item
                            break
                    
                    if not topic_data:
                        logger.warning(f"Topic {topic_id} not found in array response")
                        return {
                            'success': False,
                            'error': 'Topic not found in response array',
                            'topic_name': None
                        }
                else:
                    # Single object response
                    topic_data = response_data
                
                # Handle both camelCase and PascalCase field names
                topic_name = (topic_data.get('topicName') or 
                             topic_data.get('TopicName') or
                             topic_data.get('topic_name'))
                topic_id_from_response = (topic_data.get('topicId') or 
                                          topic_data.get('TopicID') or
                                          topic_data.get('topic_id'))
                
                if topic_name:
                    logger.info(f"Retrieved topic name: {_log_safe(topic_name)} for topic_id: {topic_id}")
                    return {
                        'success': True,
                        'topic_id': topic_id_from_response or topic_id,
                        'topic_name': topic_name,
                        'data': topic_data
                    }
                else:
                    logger.warning(f"Topic {topic_id} response missing topicName field")
                    return {
                        'success': False,
                        'error': 'Missing topicName in response',
                        'topic_name': None
                    }
            else:
                logger.warning(f"Failed to get topic {topic_id}: {response.status_code} - {_log_safe(response.text)}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'topic_name': None
                }
                
        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'topic_name': None
            }

# Global instance
net_backend_service = NetBackendService() 