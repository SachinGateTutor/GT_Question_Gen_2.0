-- Add Programming Topics to Database
USE GTQuestionDB;
GO

-- Add Programming as a new subject under Computer Science stream
-- First, get the Computer Science stream ID
DECLARE @CSStreamID INT = (SELECT StreamID FROM StreamMaster WHERE StreamName = 'Computer Science');

-- Add Programming subject if it doesn't exist
IF NOT EXISTS (SELECT * FROM SubjectMaster WHERE SubjectName = 'Programming' AND StreamID = @CSStreamID)
BEGIN
    INSERT INTO SubjectMaster (SubjectName, StreamID, IsActive) 
    VALUES ('Programming', @CSStreamID, 1);
    PRINT 'Programming subject added successfully.';
END
ELSE
BEGIN
    PRINT 'Programming subject already exists.';
END

-- Get the Programming subject ID
DECLARE @ProgrammingSubjectID INT = (SELECT SubjectID FROM SubjectMaster WHERE SubjectName = 'Programming' AND StreamID = @CSStreamID);

-- Add programming topics
IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Java Programming' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Java Programming', @ProgrammingSubjectID, 1, 1);
    PRINT 'Java Programming topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'C++ Programming' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('C++ Programming', @ProgrammingSubjectID, 1, 1);
    PRINT 'C++ Programming topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Python Programming' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Python Programming', @ProgrammingSubjectID, 1, 1);
    PRINT 'Python Programming topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Data Structures with Programs' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Data Structures with Programs', @ProgrammingSubjectID, 1, 1);
    PRINT 'Data Structures with Programs topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Algorithms Implementation' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Algorithms Implementation', @ProgrammingSubjectID, 1, 1);
    PRINT 'Algorithms Implementation topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Object-Oriented Programming' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Object-Oriented Programming', @ProgrammingSubjectID, 1, 1);
    PRINT 'Object-Oriented Programming topic added successfully.';
END

IF NOT EXISTS (SELECT * FROM TopicMaster WHERE TopicName = 'Database Programming' AND SubjectID = @ProgrammingSubjectID)
BEGIN
    INSERT INTO TopicMaster (TopicName, SubjectID, BloomLevelID, IsActive) 
    VALUES ('Database Programming', @ProgrammingSubjectID, 1, 1);
    PRINT 'Database Programming topic added successfully.';
END

PRINT 'Programming topics setup completed.'; 