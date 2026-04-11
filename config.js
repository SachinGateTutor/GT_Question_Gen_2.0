// Configuration file for GT Question Generator 2.0
// Hybrid Architecture: Python Flask + .NET Backend
// Updated for network access

const config = {
    // .NET Backend API - for data fetching and storage
    NET_BACKEND_URL: 'http://192.168.0.101:5125',
    
    // .NET Backend endpoints - for data fetching
    NET_STATUS_ENDPOINT: 'http://192.168.0.101:5125/api/question-master/generation-status',
    NET_QUESTIONS_ENDPOINT: 'http://192.168.0.101:5125/api/QuestionRetrieval/filter',
    NET_AI_QUESTIONS_ENDPOINT: 'http://192.168.0.101:5125/api/QuestionRetrieval/filter?IsAIGenerated=true',
    NET_QUESTION_BY_ID_ENDPOINT: 'http://192.168.0.101:5125/api/QuestionRetrieval',
    NET_HEALTH_ENDPOINT: 'http://192.168.0.101:5125/api/question-master/ai-service-status',
    
    // .NET Backend reference data endpoints
    NET_COURSES_ENDPOINT: 'http://192.168.0.101:5125/api/CoursesNew/get',
    NET_STREAMS_ENDPOINT: 'http://192.168.0.101:5125/api/Stream',
    NET_SUBJECTS_ENDPOINT: 'http://192.168.0.101:5125/api/SubjectNew',
    NET_TOPICS_ENDPOINT: 'http://192.168.0.101:5125/api/Topic/get',
    NET_QUESTION_TYPES_ENDPOINT: 'http://192.168.0.101:5125/api/Types/question',
    NET_DIFFICULTY_LEVELS_ENDPOINT: 'http://192.168.0.101:5125/api/DifficultyLevel',
    NET_BLOOM_LEVELS_ENDPOINT: 'http://192.168.0.101:5125/api/BloomLevel',
    
    // Python service - for AI question generation and diagram rendering
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

// Instructions for Hybrid Architecture:
// 1. .NET Backend (port 5125): Handles data management, storage, and retrieval
// 2. Python Flask (port 5000): Handles AI processing, diagram generation
// 3. Both services must be running for full functionality
// 4. Frontend served by Python Flask on port 5000
// 5. Make sure firewall allows connections on ports 5000 and 5125
