-- Export Data Script for GT Question Generator
-- Run this on your CURRENT system to export all generated data

USE MCQGen;
GO

-- Export QuestionMaster data
SELECT * FROM QuestionMaster 
WHERE IsDeleted = 0 
INTO OUTFILE 'C:\Exports\QuestionMaster.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';

-- Export MCQ_Questions data
SELECT * FROM MCQ_Questions 
INTO OUTFILE 'C:\Exports\MCQ_Questions.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';

-- Export QuestionExplanation data
SELECT * FROM QuestionExplanation 
INTO OUTFILE 'C:\Exports\QuestionExplanation.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';

-- Export all reference data
SELECT * FROM CourseMaster INTO OUTFILE 'C:\Exports\CourseMaster.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM StreamMaster INTO OUTFILE 'C:\Exports\StreamMaster.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM SubjectMaster INTO OUTFILE 'C:\Exports\SubjectMaster.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM TopicMaster INTO OUTFILE 'C:\Exports\TopicMaster.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM QuestionType INTO OUTFILE 'C:\Exports\QuestionType.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM BloomLevel INTO OUTFILE 'C:\Exports\BloomLevel.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM DifficultyLevel INTO OUTFILE 'C:\Exports\DifficultyLevel.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';
SELECT * FROM SectionType INTO OUTFILE 'C:\Exports\SectionType.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n';

PRINT 'Data export completed successfully!';
PRINT 'Check C:\Exports\ folder for CSV files.';
GO 