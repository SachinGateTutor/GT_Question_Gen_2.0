// Configuration file for AI MCQ Generator
// Updated to use .NET backend for all endpoints

const config = {
    // .NET Backend API - for data fetching only
    NET_BACKEND_URL: 'http://192.168.0.102:5125',
    
    // .NET Backend endpoints - for data fetching
    NET_STATUS_ENDPOINT: 'http://192.168.0.102:5125/api/question-master/generation-status',
    NET_QUESTIONS_ENDPOINT: 'http://192.168.0.102:5125/api/question-master/',
    NET_HEALTH_ENDPOINT: 'http://192.168.0.102:5125/api/question-master/ai-service-status',
    
    // .NET Backend reference data endpoints
    NET_COURSES_ENDPOINT: 'http://192.168.0.102:5125/api/CoursesNew/get',
    NET_STREAMS_ENDPOINT: 'http://192.168.0.102:5125/api/Stream',
    NET_SUBJECTS_ENDPOINT: 'http://192.168.0.102:5125/api/SubjectNew',
    NET_TOPICS_ENDPOINT: 'http://192.168.0.102:5125/api/Topic/get',
    NET_QUESTION_TYPES_ENDPOINT: 'http://192.168.0.102:5125/api/Types/question',
    NET_DIFFICULTY_LEVELS_ENDPOINT: 'http://192.168.0.102:5125/api/DifficultyLevel',
    NET_BLOOM_LEVELS_ENDPOINT: 'http://192.168.0.102:5125/api/BloomLevel',
    
    // Python service - for question generation
    NET_GENERATE_ENDPOINT: 'http://192.168.0.101:5000/api/generate-question',
    
    // Legacy API_URL for backward compatibility (now points to Python service)
    API_URL: 'http://192.168.0.101:5000/api/generate-question',
    
    // Python service (fallback only)
    PYTHON_BASE_URL: 'http://192.168.0.101:5000',
    PYTHON_API_URL: 'http://192.168.0.101:5000/api/generate',
    
    // Flask server settings (for local development)
    FLASK_HOST: '0.0.0.0',   
    FLASK_PORT: 5000
};

// Instructions:
// 1. .NET backend now handles ALL endpoints
// 2. Reference data: /api/DifficultyLevel, /api/BloomLevel, etc.
// 3. Question generation: /api/question-master/generate-question
// 4. Python service kept as fallback only
// 5. Make sure .NET backend is running on 192.168.0.102:5125
