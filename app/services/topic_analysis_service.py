#!/usr/bin/env python3
"""
Topic Analysis Service for Random Question Generation
Handles topic classification, diagram requirements analysis, and question distribution planning
"""

import os
import openai
from typing import Dict, List, Any, Optional
from services.openai_service import get_openai_client

class TopicAnalysisService:
    def __init__(self):
        self.client = get_openai_client()
    
    def analyze_topic_complexity(self, topic_id: int, subject_id: int, stream_id: int, course_id: int) -> Dict[str, Any]:
        """Analyze topic to determine optimal question distribution"""
        try:
            # Get topic details from database (placeholder - will be implemented)
            topic_info = self._get_topic_details(topic_id)
            subject_info = self._get_subject_details(subject_id)
            stream_info = self._get_stream_details(stream_id)
            course_info = self._get_course_details(course_id)
            
            # AI analysis of topic complexity
            complexity_analysis = self._ai_analyze_topic_complexity(topic_info, subject_info, stream_info, course_info)
            
            # Determine diagram requirements
            diagram_requirements = self._determine_diagram_requirements(topic_info, subject_info)
            
            # Calculate optimal question count
            optimal_count = self._calculate_optimal_question_count(complexity_analysis)
            
            return {
                'topic_name': topic_info.get('name', 'Unknown Topic'),
                'subject_name': subject_info.get('name', 'Unknown Subject'),
                'stream_name': stream_info.get('name', 'Unknown Stream'),
                'course_name': course_info.get('name', 'Unknown Course'),
                'complexity_level': complexity_analysis['level'],
                'diagram_requirements': diagram_requirements,
                'optimal_question_count': optimal_count,
                'concept_coverage': complexity_analysis['concepts'],
                'difficulty_distribution': complexity_analysis['difficulty_mix'],
                'bloom_distribution': complexity_analysis['bloom_mix'],
                'topic_type': complexity_analysis['topic_type'],
                'focus_areas': complexity_analysis['focus_areas']
            }
            
        except Exception as e:
            print(f"Error in analyze_topic_complexity: {e}")
            return self._get_fallback_analysis()
    
    def _ai_analyze_topic_complexity(self, topic_info: Dict, subject_info: Dict, stream_info: Dict, course_info: Dict) -> Dict[str, Any]:
        """AI-powered analysis of topic complexity and characteristics"""
        
        prompt = f"""
Analyze the following topic for question generation:

Topic: {topic_info.get('name', 'Unknown')}
Subject: {subject_info.get('name', 'Unknown')}
Stream: {stream_info.get('name', 'Unknown')}
Course: {course_info.get('name', 'Unknown')}

Please provide a comprehensive analysis including:

1. **Complexity Level**: Basic, Intermediate, Advanced, or Expert
2. **Topic Type**: theoretical, computational, mathematical, business, or visual
3. **Key Concepts**: List 5-10 main concepts that should be covered
4. **Difficulty Distribution**: Percentage breakdown for Easy, Medium, Hard, Expert
5. **Bloom Level Distribution**: Percentage breakdown for Remember, Understand, Apply, Analyze, Evaluate, Create
6. **Focus Areas**: Primary areas of focus (understanding, analysis, application, etc.)
7. **Diagram Requirements**: Whether visual diagrams would enhance learning
8. **Alternative Enhancements**: What types of enhancements would be most valuable

Respond in JSON format:
{{
    "level": "Intermediate",
    "topic_type": "computational",
    "concepts": ["concept1", "concept2", "concept3"],
    "difficulty_mix": {{"Easy": 25, "Medium": 45, "Hard": 25, "Expert": 5}},
    "bloom_mix": {{"Remember": 20, "Understand": 30, "Apply": 25, "Analyze": 20, "Evaluate": 3, "Create": 2}},
    "focus_areas": ["implementation", "analysis", "optimization"],
    "requires_diagrams": false,
    "alternative_enhancements": ["code_snippets", "pseudocode", "detailed_explanations"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            # Parse JSON response
            import json
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return self._get_fallback_analysis()
    
    def _determine_diagram_requirements(self, topic_info: Dict, subject_info: Dict) -> Dict[str, Any]:
        """Determine if topic requires diagrams and what types"""
        
        topic_name = topic_info.get('name', '').lower()
        subject_name = subject_info.get('name', '').lower()
        
        # Visual topics that typically require diagrams
        visual_keywords = [
            'circuit', 'network', 'architecture', 'design', 'graph', 'chart',
            'flowchart', 'diagram', 'visual', 'drawing', 'sketch', 'layout',
            'microprocessor', 'electronics', 'electrical', 'mechanical',
            'data structure', 'algorithm visualization', 'system design'
        ]
        
        # Check if topic requires diagrams
        requires_diagrams = any(keyword in topic_name or keyword in subject_name for keyword in visual_keywords)
        
        if requires_diagrams:
            return {
                'requires_diagrams': True,
                'diagram_types': ['question_diagrams', 'option_diagrams', 'process_flows'],
                'alternative_enhancements': ['detailed_explanations', 'step_by_step_solutions']
            }
        else:
            return {
                'requires_diagrams': False,
                'diagram_types': [],
                'alternative_enhancements': ['detailed_explanations', 'examples', 'case_studies', 'scenarios']
            }
    
    def _calculate_optimal_question_count(self, complexity_analysis: Dict) -> int:
        """Calculate optimal number of questions based on complexity"""
        
        complexity_level = complexity_analysis.get('level', 'Intermediate')
        concept_count = len(complexity_analysis.get('concepts', []))
        
        # Base question count by complexity
        base_counts = {
            'Basic': 10,
            'Intermediate': 15,
            'Advanced': 20,
            'Expert': 25
        }
        
        base_count = base_counts.get(complexity_level, 15)
        
        # Adjust based on concept count
        if concept_count > 8:
            base_count += 5
        elif concept_count < 4:
            base_count -= 3
        
        # Ensure minimum and maximum bounds
        return max(8, min(30, base_count))
    
    def calculate_question_distribution(self, topic_analysis: Dict) -> List[Dict[str, Any]]:
        """Calculate optimal question distribution based on topic analysis"""
        
        total_questions = topic_analysis['optimal_question_count']
        requires_diagrams = topic_analysis['diagram_requirements']['requires_diagrams']
        topic_type = topic_analysis['topic_type']
        
        # Get distributions from analysis
        difficulty_dist = topic_analysis['difficulty_distribution']
        bloom_dist = topic_analysis['bloom_distribution']
        
        # Calculate actual question counts
        distribution = []
        
        for difficulty, difficulty_ratio in difficulty_dist.items():
            for bloom, bloom_ratio in bloom_dist.items():
                count = max(1, int(total_questions * (difficulty_ratio / 100) * (bloom_ratio / 100)))
                if count > 0:
                    # Determine enhancement type based on topic type
                    enhancement_type = self._get_enhancement_type_for_combination(
                        topic_type, difficulty, bloom, requires_diagrams
                    )
                    
                    distribution.append({
                        'difficulty': difficulty,
                        'bloom_level': bloom,
                        'count': count,
                        'enhancement_type': enhancement_type,
                        'requires_diagram': requires_diagrams and enhancement_type in ['question_diagrams', 'option_diagrams'],
                        'requires_option_diagrams': requires_diagrams and enhancement_type == 'option_diagrams',
                        'is_programming': enhancement_type == 'code_snippets'
                    })
        
        return distribution
    
    def _get_enhancement_type_for_combination(self, topic_type: str, difficulty: str, bloom: str, requires_diagrams: bool) -> str:
        """Get appropriate enhancement type for topic-difficulty-bloom combination"""
        
        if requires_diagrams:
            # For visual topics, use diagrams
            if bloom in ['Remember', 'Understand']:
                return 'question_diagrams'
            elif bloom in ['Apply', 'Analyze']:
                return 'option_diagrams'
            else:
                return 'question_diagrams'
        else:
            # For non-visual topics, use alternative enhancements
            enhancement_mapping = {
                'theoretical': {
                    'Easy': 'detailed_explanations',
                    'Medium': 'case_studies',
                    'Hard': 'scenarios',
                    'Expert': 'detailed_explanations'
                },
                'computational': {
                    'Easy': 'code_snippets',
                    'Medium': 'pseudocode',
                    'Hard': 'algorithms',
                    'Expert': 'code_snippets'
                },
                'mathematical': {
                    'Easy': 'mathematical_notation',
                    'Medium': 'formulas',
                    'Hard': 'step_by_step_solutions',
                    'Expert': 'proofs'
                },
                'business': {
                    'Easy': 'case_studies',
                    'Medium': 'scenarios',
                    'Hard': 'decision_matrices',
                    'Expert': 'analysis_frameworks'
                }
            }
            
            topic_enhancements = enhancement_mapping.get(topic_type, enhancement_mapping['theoretical'])
            return topic_enhancements.get(difficulty, 'detailed_explanations')
    
    def _get_topic_details(self, topic_id: int) -> Dict[str, Any]:
        """Get topic details from database"""
        try:
            from services.db_service import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TopicID, TopicName, TopicDescription 
                FROM Topics 
                WHERE TopicID = ?
            """, (topic_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if row[2] else ''
                }
            else:
                return {'name': f'Topic {topic_id}', 'description': 'Topic description'}
                
        except Exception as e:
            print(f"Error getting topic details: {e}")
            return {'name': f'Topic {topic_id}', 'description': 'Topic description'}
    
    def _get_subject_details(self, subject_id: int) -> Dict[str, Any]:
        """Get subject details from database"""
        try:
            from services.db_service import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT SubjectID, SubjectName, SubjectDescription 
                FROM Subjects 
                WHERE SubjectID = ?
            """, (subject_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if row[2] else ''
                }
            else:
                return {'name': f'Subject {subject_id}', 'description': 'Subject description'}
                
        except Exception as e:
            print(f"Error getting subject details: {e}")
            return {'name': f'Subject {subject_id}', 'description': 'Subject description'}
    
    def _get_stream_details(self, stream_id: int) -> Dict[str, Any]:
        """Get stream details from database"""
        try:
            from services.db_service import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT StreamID, StreamName, StreamDescription 
                FROM Streams 
                WHERE StreamID = ?
            """, (stream_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if row[2] else ''
                }
            else:
                return {'name': f'Stream {stream_id}', 'description': 'Stream description'}
                
        except Exception as e:
            print(f"Error getting stream details: {e}")
            return {'name': f'Stream {stream_id}', 'description': 'Stream description'}
    
    def _get_course_details(self, course_id: int) -> Dict[str, Any]:
        """Get course details from database"""
        try:
            from services.db_service import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT CourseID, CourseName, CourseDescription 
                FROM Courses 
                WHERE CourseID = ?
            """, (course_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] if row[2] else ''
                }
            else:
                return {'name': f'Course {course_id}', 'description': 'Course description'}
                
        except Exception as e:
            print(f"Error getting course details: {e}")
            return {'name': f'Course {course_id}', 'description': 'Course description'}
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis when AI analysis fails"""
        return {
            'level': 'Intermediate',
            'topic_type': 'theoretical',
            'concepts': ['concept1', 'concept2', 'concept3', 'concept4', 'concept5'],
            'difficulty_mix': {'Easy': 30, 'Medium': 40, 'Hard': 25, 'Expert': 5},
            'bloom_mix': {'Remember': 25, 'Understand': 30, 'Apply': 25, 'Analyze': 15, 'Evaluate': 3, 'Create': 2},
            'focus_areas': ['understanding', 'analysis', 'application'],
            'requires_diagrams': False,
            'alternative_enhancements': ['detailed_explanations', 'examples', 'case_studies']
        }

# Global instance
topic_analysis_service = TopicAnalysisService() 