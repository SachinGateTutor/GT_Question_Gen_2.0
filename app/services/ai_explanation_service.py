#!/usr/bin/env python3
"""
AI Explanation Service
Handles AI-powered question explanations using OpenAI
"""

import openai
import json
from typing import Dict, Any, Optional
from .openai_service import get_openai_client
from datetime import datetime

class AIExplanationService:
    def __init__(self):
        self.client = get_openai_client()
    
    def generate_question_explanation(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive AI explanation for a question
        
        Args:
            question_data: Dictionary containing question information
            
        Returns:
            Dictionary with formatted explanation sections
        """
        try:
            # Build the prompt based on question data
            prompt = self._build_explanation_prompt(question_data)
            
            # Generate AI response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are PragyaAI, an expert tutor specializing in computer science and engineering education. Provide clear, step-by-step explanations that help students understand concepts deeply."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse and format the response
            raw_response = response.choices[0].message.content
            return self._format_ai_explanation(raw_response, question_data)
            
        except Exception as e:
            print(f"Error generating AI explanation: {e}")
            return self._get_fallback_explanation(question_data)
    
    def _build_explanation_prompt(self, question_data: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for AI explanation"""
        
        question_text = question_data.get('question_text', '')
        options = question_data.get('options', [])
        correct_answer = question_data.get('correct_answer', '')
        topic = question_data.get('topic', '')
        subject = question_data.get('subject', '')
        difficulty = question_data.get('difficulty_level', 'Medium')
        question_type = question_data.get('question_type', 'MCQ')
        bloom_level = question_data.get('bloom_level', 'Understand')
        
        # Build options text
        options_text = ""
        if options:
            option_labels = ['A', 'B', 'C', 'D']
            for i, option in enumerate(options[:4]):
                options_text += f"{option_labels[i]}) {option}\n"
        
        prompt = f"""
        You are PragyaAI, an expert tutor. Please provide a comprehensive explanation for this question:

        **Question Details:**
        - Subject: {subject}
        - Topic: {topic}
        - Question Type: {question_type}
        - Difficulty Level: {difficulty}
        - Bloom Level: {bloom_level}

        **Question:**
        {question_text}

        **Options:**
        {options_text}

        **Correct Answer:** {correct_answer}

        Please provide your explanation in the following JSON format:
        {{
            "step_by_step_solution": "Detailed step-by-step solution process",
            "why_correct": "Why the correct answer is right",
            "why_incorrect": "Why other options are wrong",
            "key_concepts": "Important concepts to remember",
            "learning_tips": "Study tips and strategies",
            "similar_problems": "How to approach similar problems",
            "difficulty_analysis": "What makes this question {difficulty} level"
        }}

        Make your explanation:
        1. Clear and easy to understand
        2. Include practical examples if relevant
        3. Focus on the learning objectives
        4. Provide actionable study tips
        5. Explain the reasoning process
        """
        
        return prompt
    
    def _format_ai_explanation(self, raw_response: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the AI response into structured sections"""
        
        try:
            # Try to parse JSON response
            if raw_response.strip().startswith('{'):
                explanation_data = json.loads(raw_response)
            else:
                # If not JSON, create structured format from text
                explanation_data = self._parse_text_response(raw_response)
            
            return {
                "success": True,
                "explanation": explanation_data,
                "question_id": question_data.get('question_id'),
                "generated_at": str(datetime.now()),
                "ai_model": "PragyaAI (GPT-4)"
            }
            
        except json.JSONDecodeError:
            # Fallback to text parsing
            return {
                "success": True,
                "explanation": self._parse_text_response(raw_response),
                "question_id": question_data.get('question_id'),
                "generated_at": str(datetime.now()),
                "ai_model": "PragyaAI (GPT-4)"
            }
    
    def _parse_text_response(self, text: str) -> Dict[str, str]:
        """Parse text response into structured format"""
        
        sections = {
            "step_by_step_solution": "",
            "why_correct": "",
            "why_incorrect": "",
            "key_concepts": "",
            "learning_tips": "",
            "similar_problems": "",
            "difficulty_analysis": ""
        }
        
        # Simple parsing logic
        lines = text.split('\n')
        current_section = "step_by_step_solution"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to identify sections
            if any(keyword in line.lower() for keyword in ['step', 'solution', 'solve']):
                current_section = "step_by_step_solution"
            elif any(keyword in line.lower() for keyword in ['correct', 'right', 'answer']):
                current_section = "why_correct"
            elif any(keyword in line.lower() for keyword in ['incorrect', 'wrong', 'eliminate']):
                current_section = "why_incorrect"
            elif any(keyword in line.lower() for keyword in ['concept', 'remember', 'important']):
                current_section = "key_concepts"
            elif any(keyword in line.lower() for keyword in ['tip', 'strategy', 'study']):
                current_section = "learning_tips"
            elif any(keyword in line.lower() for keyword in ['similar', 'approach', 'method']):
                current_section = "similar_problems"
            elif any(keyword in line.lower() for keyword in ['difficulty', 'level', 'challenge']):
                current_section = "difficulty_analysis"
            
            sections[current_section] += line + "\n"
        
        return sections
    
    def _get_fallback_explanation(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide a fallback explanation when AI fails"""
        
        return {
            "success": False,
            "explanation": {
                "step_by_step_solution": "AI explanation is currently unavailable. Please try again later.",
                "why_correct": "Unable to generate explanation at this time.",
                "why_incorrect": "Please contact support if you need assistance.",
                "key_concepts": "Key concepts related to this topic.",
                "learning_tips": "Review the topic thoroughly and practice similar problems.",
                "similar_problems": "Look for similar questions in your study materials.",
                "difficulty_analysis": f"This is a {question_data.get('difficulty_level', 'Medium')} level question."
            },
            "question_id": question_data.get('question_id'),
            "generated_at": str(datetime.now()),
            "ai_model": "PragyaAI (Fallback)",
            "error": "AI service temporarily unavailable"
        }
    
    def analyze_question_difficulty(self, question_text: str) -> str:
        """Analyze question difficulty based on content"""
        
        try:
            prompt = f"""
            Analyze the difficulty level of this question:
            
            Question: {question_text}
            
            Respond with only: Easy, Medium, or Hard
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            difficulty = response.choices[0].message.content.strip()
            return difficulty if difficulty in ['Easy', 'Medium', 'Hard'] else 'Medium'
            
        except Exception as e:
            print(f"Error analyzing difficulty: {e}")
            return 'Medium'
    
    def provide_step_by_step_solution(self, question: str, options: list, correct_answer: str) -> str:
        """Generate step-by-step solution for a question"""
        
        try:
            prompt = f"""
            Provide a step-by-step solution for this question:
            
            Question: {question}
            Options: {options}
            Correct Answer: {correct_answer}
            
            Give a clear, logical step-by-step approach to solve this problem.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating step-by-step solution: {e}")
            return "Step-by-step solution is currently unavailable."
    
    def generate_learning_tips(self, question_type: str, topic: str) -> str:
        """Generate learning tips based on question type and topic"""
        
        try:
            prompt = f"""
            Generate learning tips for {question_type} questions on the topic: {topic}
            
            Provide practical study tips and strategies.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating learning tips: {e}")
            return "Focus on understanding the core concepts and practice regularly."

# Global instance
ai_explanation_service = AIExplanationService() 