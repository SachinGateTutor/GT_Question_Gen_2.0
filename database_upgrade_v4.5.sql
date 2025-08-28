-- GT Question Generator 2.0 - Database Upgrade Script for v4.5_ML
-- This script upgrades existing databases to include new features
-- Run this script if you're upgrading from an earlier version

USE GTQuestionDB;
GO

PRINT 'Starting database upgrade to v4.5_ML...';
GO

-- Add DiagramCode column to existing MCQ_Questions table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[MCQ_Questions]') AND name = 'DiagramCode')
BEGIN
    ALTER TABLE MCQ_Questions ADD DiagramCode NVARCHAR(MAX);
    PRINT '✅ DiagramCode column added successfully to MCQ_Questions table.';
END
ELSE
BEGIN
    PRINT '✅ DiagramCode column already exists in MCQ_Questions table.';
END
GO

-- Recreate the view to include the new column
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_QuestionsWithDetails')
BEGIN
    DROP VIEW vw_QuestionsWithDetails;
    PRINT '🔄 Existing view dropped for recreation.';
END
GO

-- Create updated view with DiagramCode column
CREATE VIEW vw_QuestionsWithDetails AS
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
    mcq.DiagramCode,
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
GO

PRINT '✅ Updated view vw_QuestionsWithDetails created successfully.';
GO

-- Verify the upgrade
PRINT '🔍 Verifying upgrade...';

-- Check if DiagramCode column exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[MCQ_Questions]') AND name = 'DiagramCode')
BEGIN
    PRINT '✅ DiagramCode column verification: PASSED';
END
ELSE
BEGIN
    PRINT '❌ DiagramCode column verification: FAILED';
END

-- Check if view exists
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_QuestionsWithDetails')
BEGIN
    PRINT '✅ View vw_QuestionsWithDetails verification: PASSED';
END
ELSE
BEGIN
    PRINT '❌ View vw_QuestionsWithDetails verification: FAILED';
END

-- Check if view includes DiagramCode column
IF EXISTS (SELECT * FROM sys.columns c 
           INNER JOIN sys.views v ON c.object_id = v.object_id 
           WHERE v.name = 'vw_QuestionsWithDetails' AND c.name = 'DiagramCode')
BEGIN
    PRINT '✅ View DiagramCode column verification: PASSED';
END
ELSE
BEGIN
    PRINT '❌ View DiagramCode column verification: FAILED';
END

PRINT '';
PRINT '🚀 Database upgrade to v4.5_ML completed successfully!';
PRINT '📋 New Features Added:';
PRINT '   - DiagramCode storage for Python diagram generation code';
PRINT '   - Enhanced view with diagram code support';
PRINT '   - Support for advanced question generation with diagrams';
PRINT '';
PRINT '✅ Your database is now ready for GT Question Generator v4.5_ML!';
GO 