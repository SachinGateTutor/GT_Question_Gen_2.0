-- Export Data Script for GT Question Generator 2.0
-- Run this on your CURRENT system to export all generated data
-- Updated for SQL Server syntax and current schema

USE GTQuestionDB;
GO

-- Create export directory if it doesn't exist
-- Note: You may need to create C:\Exports\ directory manually

-- Export QuestionMaster data
SELECT 
    QuestionID,
    SubjectID,
    TopicID,
    QuestionTypeID,
    Marks,
    BloomLevelID,
    DifficultyLevelID,
    SectionID,
    IsEnable,
    IsDeleted,
    IsPublic,
    AddedDate,
    ApprovedDate
FROM QuestionMaster 
WHERE IsDeleted = 0;

-- Export MCQ_Questions data with all option image columns
SELECT 
    MCQID,
    QuestionID,
    QuestionText,
    OptionA,
    OptionB,
    OptionC,
    OptionD,
    CorrectOption,
    HasImage,
    ImgQuestion,
    ImgOptionA,
    ImgOptionB,
    ImgOptionC,
    ImgOptionD,
    CreatedDate
FROM MCQ_Questions;

-- Export QuestionExplanation data
SELECT 
    ExplanationID,
    QuestionID,
    ExplanationText,
    ImgExplanation,
    CreatedOn
FROM QuestionExplanation;

-- Export all reference data
SELECT * FROM CourseMaster;
SELECT * FROM StreamMaster;
SELECT * FROM SubjectMaster;
SELECT * FROM TopicMaster;
SELECT * FROM QuestionType;
SELECT * FROM BloomLevel;
SELECT * FROM DifficultyLevel;
SELECT * FROM SectionType;

-- Export complete question data with joins (for backup purposes)
SELECT 
    qm.QuestionID,
    qm.SubjectID,
    qm.TopicID,
    qm.QuestionTypeID,
    qm.Marks,
    qm.BloomLevelID,
    qm.DifficultyLevelID,
    qm.SectionID,
    qm.IsEnable,
    qm.IsDeleted,
    qm.IsPublic,
    qm.AddedDate,
    qm.ApprovedDate,
    c.CourseName,
    s.StreamName,
    sub.SubjectName,
    t.TopicName,
    qt.QuestionTypeName,
    bl.LevelName AS BloomLevelName,
    dl.LevelName AS DifficultyLevelName,
    st.SectionName,
    mcq.QuestionText,
    mcq.OptionA,
    mcq.OptionB,
    mcq.OptionC,
    mcq.OptionD,
    mcq.CorrectOption,
    mcq.HasImage,
    mcq.ImgQuestion,
    mcq.ImgOptionA,
    mcq.ImgOptionB,
    mcq.ImgOptionC,
    mcq.ImgOptionD,
    qe.ExplanationText,
    qe.ImgExplanation
FROM QuestionMaster qm
LEFT JOIN SubjectMaster sub ON qm.SubjectID = sub.SubjectID
LEFT JOIN StreamMaster s ON sub.StreamID = s.StreamID
LEFT JOIN CourseMaster c ON s.CourseID = c.CourseID
LEFT JOIN TopicMaster t ON qm.TopicID = t.TopicID
LEFT JOIN QuestionType qt ON qm.QuestionTypeID = qt.QuestionTypeID
LEFT JOIN BloomLevel bl ON qm.BloomLevelID = bl.BloomLevelID
LEFT JOIN DifficultyLevel dl ON qm.DifficultyLevelID = dl.DifficultyLevelID
LEFT JOIN SectionType st ON qm.SectionID = st.SectionID
LEFT JOIN MCQ_Questions mcq ON qm.QuestionID = mcq.QuestionID
LEFT JOIN QuestionExplanation qe ON qm.QuestionID = qe.QuestionID
WHERE qm.IsDeleted = 0;

PRINT 'Data export queries completed successfully!';
PRINT 'Copy the results from each SELECT statement to CSV files.';
PRINT 'You can also use SQL Server Management Studio to export results to CSV.';
GO 