# 🗄️ Database Setup Guide - GT Question Generator 2.0

## Overview
This guide will help you set up the SQL Server database for the GT Question Generator 2.0 on a new system.

## 📋 Prerequisites

### System Requirements
- **SQL Server**: 2019+ (Express, Standard, or Enterprise)
- **SQL Server Management Studio (SSMS)**: For database management
- **ODBC Driver**: ODBC Driver 17 for SQL Server
- **Permissions**: Database creation and management rights

### Software Installation

#### Option 1: SQL Server Express (Free)
1. Download SQL Server Express from Microsoft
2. Run the installer with default settings
3. Enable TCP/IP protocol in SQL Server Configuration Manager
4. Install SQL Server Management Studio (SSMS)

#### Option 2: SQL Server Standard/Enterprise
1. Install SQL Server with your license
2. Configure network access
3. Install SSMS for management

## 🔧 Database Setup Steps

### Step 1: Install SQL Server

#### Windows Installation
```bash
# Download SQL Server Express
# https://www.microsoft.com/en-us/sql-server/sql-server-downloads

# Or use Chocolatey (if available)
choco install sql-server-express
choco install sql-server-management-studio
```

#### Linux Installation (Docker)
```bash
# Pull SQL Server image
docker pull mcr.microsoft.com/mssql/server:2019-latest

# Run SQL Server container
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" \
  -p 1433:1433 --name sqlserver --hostname sqlserver \
  -d mcr.microsoft.com/mssql/server:2019-latest
```

### Step 2: Configure SQL Server

#### Enable TCP/IP Protocol
1. Open SQL Server Configuration Manager
2. Navigate to SQL Server Network Configuration
3. Enable TCP/IP protocol
4. Restart SQL Server service

#### Create Database User (Optional)
```sql
-- Create a new login
CREATE LOGIN gtuser WITH PASSWORD = 'YourStrong@Passw0rd';

-- Create database user
USE GTQuestionDB;
CREATE USER gtuser FOR LOGIN gtuser;

-- Grant permissions
EXEC sp_addrolemember 'db_owner', 'gtuser';
```

### Step 3: Run Database Setup Script

#### Method 1: Using SQL Server Management Studio
1. Open SSMS
2. Connect to your SQL Server instance
3. Open the `database_setup.sql` file
4. Click "Execute" to run the script

#### Method 2: Using Command Line
```bash
# Windows
sqlcmd -S localhost -i database_setup.sql

# Linux
sqlcmd -S localhost -U sa -P YourStrong@Passw0rd -i database_setup.sql
```

#### Method 3: Using PowerShell
```powershell
# Run the setup script
Invoke-Sqlcmd -InputFile "database_setup.sql" -ServerInstance "localhost"
```

### Step 4: Verify Database Setup

#### Check Database Creation
```sql
-- Verify database exists
SELECT name FROM sys.databases WHERE name = 'GTQuestionDB';

-- Check tables
USE GTQuestionDB;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';
```

#### Verify Sample Data
```sql
-- Check courses
SELECT * FROM CourseMaster;

-- Check streams
SELECT * FROM StreamMaster;

-- Check subjects
SELECT * FROM SubjectMaster;

-- Check topics
SELECT * FROM TopicMaster;
```

## 🔗 Application Configuration

### Update Database Connection

#### Method 1: Environment Variables
Create a `.env` file in your project root:
```env
DB_SERVER=localhost
DB_NAME=GTQuestionDB
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
```

#### Method 2: Update db_service.py
Edit `app/services/db_service.py`:
```python
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'  # Your server name
        'DATABASE=GTQuestionDB;'  # Your database name
        'UID=sa;'  # Your username
        'PWD=YourStrong@Passw0rd;'  # Your password
    )
    return conn
```

### Test Database Connection
```python
# Test connection
python test_db_connection.py
```

## 📊 Database Schema

### Core Tables
1. **CourseMaster** - Course definitions
2. **StreamMaster** - Stream definitions (linked to courses)
3. **SubjectMaster** - Subject definitions (linked to streams)
4. **TopicMaster** - Topic definitions (linked to subjects)
5. **QuestionMaster** - Question metadata
6. **MCQ_Questions** - MCQ-specific data
7. **QuestionExplanation** - Explanations and diagrams

### Reference Tables
1. **QuestionType** - Question types (MCQ, True/False, etc.)
2. **BloomLevel** - Bloom's taxonomy levels
3. **DifficultyLevel** - Difficulty levels (Easy, Medium, Hard)
4. **SectionType** - Section types (Section A, B, C, D)

### Sample Data Included
- **Courses**: B. Tech, M. Tech, BA, BSc
- **Streams**: Computer Science, Mechanical, Civil, Electrical, IT
- **Subjects**: Computer Science, AI, ML, Data Structures, etc.
- **Topics**: Binary Trees, Logic Gates, Neural Networks, etc.
- **Question Types**: MCQ, True/False, Fill in the Blanks, etc.
- **Bloom Levels**: Remember, Understand, Apply, Analyze, Evaluate, Create
- **Difficulty Levels**: Easy, Medium, Hard, Expert

## 🔍 Troubleshooting

### Common Issues

#### 1. Connection Failed
```bash
# Check SQL Server service
services.msc  # Windows
systemctl status mssql-server  # Linux

# Test connection
sqlcmd -S localhost -U sa -P YourStrong@Passw0rd
```

#### 2. ODBC Driver Not Found
```bash
# Install ODBC Driver 17
# Windows: Download from Microsoft
# Linux: Follow Microsoft's installation guide
```

#### 3. Permission Denied
```sql
-- Grant necessary permissions
USE GTQuestionDB;
GRANT ALL PRIVILEGES ON DATABASE::GTQuestionDB TO [your_user];
```

#### 4. Port Not Accessible
```bash
# Check if port 1433 is open
netstat -an | findstr 1433  # Windows
netstat -an | grep 1433      # Linux

# Configure firewall
# Windows: Allow SQL Server in Windows Firewall
# Linux: sudo ufw allow 1433
```

### Performance Optimization

#### Create Indexes
```sql
-- The setup script creates basic indexes
-- For better performance, consider additional indexes based on usage patterns
CREATE INDEX IX_QuestionMaster_AddedDate ON QuestionMaster(AddedDate);
CREATE INDEX IX_MCQ_Questions_CorrectOption ON MCQ_Questions(CorrectOption);
```

#### Configure Memory
```sql
-- Set maximum memory for SQL Server (adjust based on your system)
EXEC sp_configure 'max server memory (MB)', 2048;
RECONFIGURE;
```

## 🔒 Security Considerations

### Best Practices
1. **Use Strong Passwords** - Change default passwords
2. **Limit Permissions** - Use least privilege principle
3. **Enable Encryption** - Use SSL/TLS for connections
4. **Regular Backups** - Set up automated backup schedule
5. **Update Regularly** - Keep SQL Server patched

### Connection Security
```python
# Use encrypted connections
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=GTQuestionDB;'
    'UID=sa;'
    'PWD=YourStrong@Passw0rd;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)
```

## 📈 Monitoring and Maintenance

### Database Maintenance
```sql
-- Check database size
SELECT 
    name,
    size * 8 / 1024 AS SizeMB
FROM sys.master_files
WHERE database_id = DB_ID('GTQuestionDB');

-- Check table sizes
SELECT 
    t.name AS TableName,
    p.rows AS RowCounts,
    SUM(a.total_pages) * 8 AS TotalSpaceKB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.is_ms_shipped = 0
GROUP BY t.name, p.rows
ORDER BY t.name;
```

### Backup Strategy
```sql
-- Create full backup
BACKUP DATABASE GTQuestionDB 
TO DISK = 'C:\Backups\GTQuestionDB.bak'
WITH FORMAT, INIT, COMPRESSION;

-- Create maintenance plan for regular backups
-- Use SQL Server Agent for automated backups
```

## 🚀 Quick Setup Commands

### Windows (PowerShell)
```powershell
# Install SQL Server Express
choco install sql-server-express -y

# Install SSMS
choco install sql-server-management-studio -y

# Run database setup
sqlcmd -S localhost -i database_setup.sql
```

### Linux (Bash)
```bash
# Install SQL Server
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev

# Run database setup
sqlcmd -S localhost -U sa -P YourStrong@Passw0rd -i database_setup.sql
```

### Docker
```bash
# Run SQL Server container
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" \
  -p 1433:1433 --name sqlserver \
  -v $(pwd):/database \
  -d mcr.microsoft.com/mssql/server:2019-latest

# Run setup script
docker exec -i sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P YourStrong@Passw0rd \
  -i /database/database_setup.sql
```

## ✅ Verification Checklist

- [ ] SQL Server installed and running
- [ ] Database GTQuestionDB created
- [ ] All tables created successfully
- [ ] Sample data inserted
- [ ] Indexes created
- [ ] Application can connect to database
- [ ] Test questions can be generated
- [ ] Questions can be stored and retrieved
- [ ] Review interface works correctly

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify SQL Server service is running
3. Test connection using sqlcmd
4. Check error logs in SQL Server Management Studio
5. Ensure proper permissions are set

---

**Last Updated**: July 2025  
**Version**: 2.0  
**Database**: SQL Server 2019+ 