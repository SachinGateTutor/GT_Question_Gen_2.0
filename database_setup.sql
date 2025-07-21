-- GT Question Generator 2.0 - Database Setup Script
-- This script creates the complete database schema for the application

-- Create the database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'GTQuestionDB')
BEGIN
    CREATE DATABASE GTQuestionDB;
    PRINT 'Database GTQuestionDB created successfully.';
END
ELSE
BEGIN
    PRINT 'Database GTQuestionDB already exists.';
END
GO

USE GTQuestionDB;
GO

-- Create CourseMaster table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CourseMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE CourseMaster (
        CourseID INT IDENTITY(1,1) PRIMARY KEY,
        CourseName NVARCHAR(100) NOT NULL,
        IsActive BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'CourseMaster table created successfully.';
END
GO

-- Create StreamMaster table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[StreamMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE StreamMaster (
        StreamID INT IDENTITY(1,1) PRIMARY KEY,
        StreamName NVARCHAR(100) NOT NULL,
        CourseID INT FOREIGN KEY REFERENCES CourseMaster(CourseID),
        IsActive BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'StreamMaster table created successfully.';
END
GO

-- Create SubjectMaster table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SubjectMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE SubjectMaster (
        SubjectID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectName NVARCHAR(100) NOT NULL,
        StreamID INT FOREIGN KEY REFERENCES StreamMaster(StreamID),
        IsActive BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'SubjectMaster table created successfully.';
END
GO

-- Create TopicMaster table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[TopicMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE TopicMaster (
        TopicID INT IDENTITY(1,1) PRIMARY KEY,
        TopicName NVARCHAR(100) NOT NULL,
        SubjectID INT FOREIGN KEY REFERENCES SubjectMaster(SubjectID),
        BloomLevelID INT,
        IsActive BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'TopicMaster table created successfully.';
END
GO

-- Create QuestionType table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[QuestionType]') AND type in (N'U'))
BEGIN
    CREATE TABLE QuestionType (
        QuestionTypeID INT IDENTITY(1,1) PRIMARY KEY,
        QuestionTypeName NVARCHAR(50) NOT NULL,
        IsActive BIT DEFAULT 1
    );
    PRINT 'QuestionType table created successfully.';
END
GO

-- Create BloomLevel table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[BloomLevel]') AND type in (N'U'))
BEGIN
    CREATE TABLE BloomLevel (
        BloomLevelID INT IDENTITY(1,1) PRIMARY KEY,
        LevelName NVARCHAR(50) NOT NULL,
        Description NVARCHAR(200),
        IsActive BIT DEFAULT 1
    );
    PRINT 'BloomLevel table created successfully.';
END
GO

-- Create DifficultyLevel table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DifficultyLevel]') AND type in (N'U'))
BEGIN
    CREATE TABLE DifficultyLevel (
        DifficultyLevelID INT IDENTITY(1,1) PRIMARY KEY,
        LevelName NVARCHAR(50) NOT NULL,
        Description NVARCHAR(200),
        IsActive BIT DEFAULT 1
    );
    PRINT 'DifficultyLevel table created successfully.';
END
GO

-- Create SectionType table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SectionType]') AND type in (N'U'))
BEGIN
    CREATE TABLE SectionType (
        SectionID INT IDENTITY(1,1) PRIMARY KEY,
        SectionName NVARCHAR(50) NOT NULL,
        IsActive BIT DEFAULT 1
    );
    PRINT 'SectionType table created successfully.';
END
GO

-- Create QuestionMaster table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[QuestionMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE QuestionMaster (
        QuestionID INT IDENTITY(1,1) PRIMARY KEY,
        SubjectID INT FOREIGN KEY REFERENCES SubjectMaster(SubjectID),
        TopicID INT FOREIGN KEY REFERENCES TopicMaster(TopicID),
        QuestionTypeID INT FOREIGN KEY REFERENCES QuestionType(QuestionTypeID),
        Marks INT DEFAULT 1,
        BloomLevelID INT FOREIGN KEY REFERENCES BloomLevel(BloomLevelID),
        DifficultyLevelID INT FOREIGN KEY REFERENCES DifficultyLevel(DifficultyLevelID),
        SectionID INT FOREIGN KEY REFERENCES SectionType(SectionID),
        IsEnable BIT DEFAULT 0,
        IsDeleted BIT DEFAULT 0,
        IsPublic BIT DEFAULT 0,
        AddedDate DATETIME DEFAULT GETDATE(),
        ApprovedDate DATETIME NULL
    );
    PRINT 'QuestionMaster table created successfully.';
END
GO

-- Create MCQ_Questions table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[MCQ_Questions]') AND type in (N'U'))
BEGIN
    CREATE TABLE MCQ_Questions (
        MCQID INT IDENTITY(1,1) PRIMARY KEY,
        QuestionID INT FOREIGN KEY REFERENCES QuestionMaster(QuestionID),
        QuestionText NVARCHAR(MAX) NOT NULL,
        OptionA NVARCHAR(500),
        OptionB NVARCHAR(500),
        OptionC NVARCHAR(500),
        OptionD NVARCHAR(500),
        CorrectOption CHAR(1) CHECK (CorrectOption IN ('A', 'B', 'C', 'D')),
        HasImage BIT DEFAULT 0,
        ImgQuestion NVARCHAR(500),
        ImgOptionA NVARCHAR(500),
        ImgOptionB NVARCHAR(500),
        ImgOptionC NVARCHAR(500),
        ImgOptionD NVARCHAR(500),
        CreatedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'MCQ_Questions table created successfully.';
END
GO

-- Create QuestionExplanation table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[QuestionExplanation]') AND type in (N'U'))
BEGIN
    CREATE TABLE QuestionExplanation (
        ExplanationID INT IDENTITY(1,1) PRIMARY KEY,
        QuestionID INT FOREIGN KEY REFERENCES QuestionMaster(QuestionID),
        ExplanationText NVARCHAR(MAX),
        ImgExplanation NVARCHAR(500),
        CreatedOn DATETIME DEFAULT GETDATE()
    );
    PRINT 'QuestionExplanation table created successfully.';
END
GO

-- Insert sample data for CourseMaster
IF NOT EXISTS (SELECT * FROM CourseMaster WHERE CourseName = 'B. Tech')
BEGIN
    INSERT INTO CourseMaster (CourseName) VALUES ('B. Tech');
    INSERT INTO CourseMaster (CourseName) VALUES ('M. Tech');
    INSERT INTO CourseMaster (CourseName) VALUES ('BA');
    INSERT INTO CourseMaster (CourseName) VALUES ('BSc');
    PRINT 'Sample courses inserted successfully.';
END
GO

-- Insert sample data for StreamMaster
IF NOT EXISTS (SELECT * FROM StreamMaster WHERE StreamName = 'Computer Science')
BEGIN
    DECLARE @BtechCourseID INT = (SELECT CourseID FROM CourseMaster WHERE CourseName = 'B. Tech');
    DECLARE @MtechCourseID INT = (SELECT CourseID FROM CourseMaster WHERE CourseName = 'M. Tech');
    
    INSERT INTO StreamMaster (StreamName, CourseID) VALUES 
    ('Computer Science', @BtechCourseID),
    ('Mechanical Engineering', @BtechCourseID),
    ('Civil Engineering', @BtechCourseID),
    ('Electrical Engineering', @BtechCourseID),
    ('Information Technology', @BtechCourseID),
    ('Computer Science', @MtechCourseID),
    ('Data Science', @MtechCourseID);
    PRINT 'Sample streams inserted successfully.';
END
GO

-- Insert sample data for SubjectMaster
IF NOT EXISTS (SELECT * FROM SubjectMaster WHERE SubjectName = 'Computer Science')
BEGIN
    DECLARE @CSStreamID INT = (SELECT StreamID FROM StreamMaster WHERE StreamName = 'Computer Science' AND CourseID = (SELECT CourseID FROM CourseMaster WHERE CourseName = 'B. Tech'));
    
    INSERT INTO SubjectMaster (SubjectName, StreamID) VALUES 
    ('Computer Science', @CSStreamID),
    ('Artificial Intelligence', @CSStreamID),
    ('Machine Learning', @CSStreamID),
    ('Data Structures', @CSStreamID),
    ('Database Management', @CSStreamID),
    ('Computer Networks', @CSStreamID),
    ('Operating Systems', @CSStreamID),
    ('Software Engineering', @CSStreamID);
    PRINT 'Sample subjects inserted successfully.';
END
GO

-- Insert sample data for TopicMaster
IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Binary Trees')
BEGIN
    DECLARE @DSSubjectID INT = (SELECT SubjectID FROM SubjectMaster WHERE SubjectName = 'Data Structures');
    DECLARE @CSSubjectID INT = (SELECT SubjectID FROM SubjectMaster WHERE SubjectName = 'Computer Science');
    DECLARE @AISubjectID INT = (SELECT SubjectID FROM SubjectMaster WHERE SubjectName = 'Artificial Intelligence');
    
    INSERT INTO TopicMaster (TopicName, SubjectID) VALUES 
    ('Binary Trees', @DSSubjectID),
    ('Linked Lists', @DSSubjectID),
    ('Stacks and Queues', @DSSubjectID),
    ('Sorting Algorithms', @DSSubjectID),
    ('Searching Algorithms', @DSSubjectID),
    ('Graph Theory', @DSSubjectID),
    ('Dynamic Programming', @DSSubjectID),
    ('Logic Gates', @CSSubjectID),
    ('Microprocessor Architecture', @CSSubjectID),
    ('Digital Electronics', @CSSubjectID),
    ('Computer Organization', @CSSubjectID),
    ('Neural Networks', @AISubjectID),
    ('Expert Systems', @AISubjectID),
    ('Natural Language Processing', @AISubjectID),
    ('Computer Vision', @AISubjectID);
    PRINT 'Sample topics inserted successfully.';
END
GO

-- Insert sample data for QuestionType
IF NOT EXISTS (SELECT * FROM QuestionType WHERE QuestionTypeName = 'MCQ')
BEGIN
    INSERT INTO QuestionType (QuestionTypeName) VALUES 
    ('MCQ'),
    ('True/False'),
    ('Fill in the Blanks'),
    ('Short Answer'),
    ('Long Answer'),
    ('CDQ');
    PRINT 'Question types inserted successfully.';
END
GO

-- Insert sample data for BloomLevel
IF NOT EXISTS (SELECT * FROM BloomLevel WHERE LevelName = 'Remember')
BEGIN
    INSERT INTO BloomLevel (LevelName, Description) VALUES 
    ('Remember', 'Recall facts and basic concepts'),
    ('Understand', 'Explain ideas and concepts'),
    ('Apply', 'Use information in new situations'),
    ('Analyze', 'Draw connections among ideas'),
    ('Evaluate', 'Justify a stand or decision'),
    ('Create', 'Produce new or original work');
    PRINT 'Bloom levels inserted successfully.';
END
GO

-- Insert sample data for DifficultyLevel
IF NOT EXISTS (SELECT * FROM DifficultyLevel WHERE LevelName = 'Easy')
BEGIN
    INSERT INTO DifficultyLevel (LevelName, Description) VALUES 
    ('Easy', 'Basic level questions'),
    ('Medium', 'Intermediate level questions'),
    ('Hard', 'Advanced level questions'),
    ('Expert', 'Expert level questions');
    PRINT 'Difficulty levels inserted successfully.';
END
GO

-- Insert sample data for SectionType
IF NOT EXISTS (SELECT * FROM SectionType WHERE SectionName = 'Section A')
BEGIN
    INSERT INTO SectionType (SectionName) VALUES 
    ('Section A'),
    ('Section B'),
    ('Section C'),
    ('Section D');
    PRINT 'Section types inserted successfully.';
END
GO

-- Create indexes for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_QuestionMaster_SubjectID')
BEGIN
    CREATE INDEX IX_QuestionMaster_SubjectID ON QuestionMaster(SubjectID);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_QuestionMaster_TopicID')
BEGIN
    CREATE INDEX IX_QuestionMaster_TopicID ON QuestionMaster(TopicID);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_QuestionMaster_IsEnable')
BEGIN
    CREATE INDEX IX_QuestionMaster_IsEnable ON QuestionMaster(IsEnable);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_MCQ_Questions_QuestionID')
BEGIN
    CREATE INDEX IX_MCQ_Questions_QuestionID ON MCQ_Questions(QuestionID);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SubjectMaster_StreamID')
BEGIN
    CREATE INDEX IX_SubjectMaster_StreamID ON SubjectMaster(StreamID);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TopicMaster_SubjectID')
BEGIN
    CREATE INDEX IX_TopicMaster_SubjectID ON TopicMaster(SubjectID);
END

PRINT 'Database indexes created successfully.';
GO

-- Create a view for easy question retrieval
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_QuestionsWithDetails')
BEGIN
    DROP VIEW vw_QuestionsWithDetails;
END
GO

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

PRINT 'View vw_QuestionsWithDetails created successfully.';
GO

PRINT 'Database setup completed successfully!';
PRINT 'You can now connect to the database using the connection string in your application.';
GO 