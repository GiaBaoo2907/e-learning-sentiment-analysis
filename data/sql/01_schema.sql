/*
  E-learning sentiment project schema for SQL Server Express.
  Run this script in SSMS while connected to BUIGIABAO\SQLEXPRESS.
  It creates database ElearningSentiment, tables, indexes, and starter categories.
*/
IF DB_ID(N'ElearningSentiment') IS NULL
BEGIN
    CREATE DATABASE ElearningSentiment;
END
GO

USE ElearningSentiment;
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Users PRIMARY KEY,
        full_name NVARCHAR(120) NOT NULL,
        email NVARCHAR(255) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        role NVARCHAR(20) NOT NULL CONSTRAINT DF_Users_role DEFAULT N'student',
        is_active BIT NOT NULL CONSTRAINT DF_Users_active DEFAULT 1,
        created_at DATETIME2 NOT NULL,
        CONSTRAINT UQ_Users_email UNIQUE (email),
        CONSTRAINT CK_Users_role CHECK (role IN (N'student', N'admin'))
    );
END
GO

IF OBJECT_ID(N'dbo.PasswordResets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.PasswordResets (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_PasswordResets PRIMARY KEY,
        user_id INT NOT NULL,
        token_hash NVARCHAR(64) NOT NULL,
        expires_at DATETIME2 NOT NULL,
        used_at DATETIME2 NULL,
        CONSTRAINT UQ_PasswordResets_token UNIQUE (token_hash),
        CONSTRAINT FK_PasswordResets_Users FOREIGN KEY (user_id) REFERENCES dbo.Users(id)
    );
END
GO

IF OBJECT_ID(N'dbo.Categories', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Categories (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Categories PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        description NVARCHAR(500) NOT NULL CONSTRAINT DF_Categories_description DEFAULT N'',
        CONSTRAINT UQ_Categories_name UNIQUE (name)
    );
END
GO

IF OBJECT_ID(N'dbo.Courses', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Courses (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Courses PRIMARY KEY,
        category_id INT NOT NULL,
        title NVARCHAR(200) NOT NULL,
        instructor NVARCHAR(120) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        thumbnail_url NVARCHAR(1000) NULL,
        is_published BIT NOT NULL CONSTRAINT DF_Courses_published DEFAULT 0,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,
        CONSTRAINT FK_Courses_Categories FOREIGN KEY (category_id) REFERENCES dbo.Categories(id)
    );
END
GO

IF OBJECT_ID(N'dbo.Lessons', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Lessons (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Lessons PRIMARY KEY,
        course_id INT NOT NULL,
        title NVARCHAR(200) NOT NULL,
        description NVARCHAR(1000) NOT NULL CONSTRAINT DF_Lessons_description DEFAULT N'',
        video_url NVARCHAR(1000) NOT NULL,
        position INT NOT NULL,
        duration_seconds INT NOT NULL CONSTRAINT DF_Lessons_duration DEFAULT 0,
        CONSTRAINT FK_Lessons_Courses FOREIGN KEY (course_id) REFERENCES dbo.Courses(id),
        CONSTRAINT CK_Lessons_position CHECK (position > 0),
        CONSTRAINT CK_Lessons_duration CHECK (duration_seconds >= 0)
    );
END
GO

IF OBJECT_ID(N'dbo.Enrollments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Enrollments (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Enrollments PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        enrolled_at DATETIME2 NOT NULL,
        CONSTRAINT UQ_Enrollments_User_Course UNIQUE (user_id, course_id),
        CONSTRAINT FK_Enrollments_Users FOREIGN KEY (user_id) REFERENCES dbo.Users(id),
        CONSTRAINT FK_Enrollments_Courses FOREIGN KEY (course_id) REFERENCES dbo.Courses(id)
    );
END
GO

IF OBJECT_ID(N'dbo.LessonProgress', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.LessonProgress (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_LessonProgress PRIMARY KEY,
        user_id INT NOT NULL,
        lesson_id INT NOT NULL,
        is_completed BIT NOT NULL CONSTRAINT DF_LessonProgress_completed DEFAULT 0,
        updated_at DATETIME2 NOT NULL,
        CONSTRAINT UQ_LessonProgress_User_Lesson UNIQUE (user_id, lesson_id),
        CONSTRAINT FK_LessonProgress_Users FOREIGN KEY (user_id) REFERENCES dbo.Users(id),
        CONSTRAINT FK_LessonProgress_Lessons FOREIGN KEY (lesson_id) REFERENCES dbo.Lessons(id)
    );
END
GO

IF OBJECT_ID(N'dbo.Feedback', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Feedback (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_Feedback PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        lesson_id INT NULL,
        rating INT NOT NULL,
        text NVARCHAR(MAX) NOT NULL,
        sentiment INT NOT NULL,
        moderation_status NVARCHAR(20) NOT NULL CONSTRAINT DF_Feedback_status DEFAULT N'visible',
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,
        CONSTRAINT UQ_Feedback_User_Course_Lesson UNIQUE (user_id, course_id, lesson_id),
        CONSTRAINT FK_Feedback_Users FOREIGN KEY (user_id) REFERENCES dbo.Users(id),
        CONSTRAINT FK_Feedback_Courses FOREIGN KEY (course_id) REFERENCES dbo.Courses(id),
        CONSTRAINT FK_Feedback_Lessons FOREIGN KEY (lesson_id) REFERENCES dbo.Lessons(id),
        CONSTRAINT CK_Feedback_rating CHECK (rating BETWEEN 1 AND 5),
        CONSTRAINT CK_Feedback_sentiment CHECK (sentiment IN (0, 1, 2)),
        CONSTRAINT CK_Feedback_status CHECK (moderation_status IN (N'visible', N'hidden'))
    );
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Categories)
BEGIN
    INSERT INTO dbo.Categories(name, description) VALUES
        (N'Lập trình', N'Các khóa học lập trình và phát triển phần mềm'),
        (N'Khoa học dữ liệu', N'Phân tích dữ liệu, học máy và trí tuệ nhân tạo'),
        (N'Ngoại ngữ', N'Các khóa học ngôn ngữ'),
        (N'Kỹ năng học tập', N'Kỹ năng và phương pháp học tập trực tuyến');
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Courses_category_id' AND object_id = OBJECT_ID(N'dbo.Courses'))
    CREATE INDEX IX_Courses_category_id ON dbo.Courses(category_id);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Courses_is_published' AND object_id = OBJECT_ID(N'dbo.Courses'))
    CREATE INDEX IX_Courses_is_published ON dbo.Courses(is_published);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Lessons_course_id' AND object_id = OBJECT_ID(N'dbo.Lessons'))
    CREATE INDEX IX_Lessons_course_id ON dbo.Lessons(course_id, position);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Feedback_sentiment' AND object_id = OBJECT_ID(N'dbo.Feedback'))
    CREATE INDEX IX_Feedback_sentiment ON dbo.Feedback(sentiment);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Feedback_created_at' AND object_id = OBJECT_ID(N'dbo.Feedback'))
    CREATE INDEX IX_Feedback_created_at ON dbo.Feedback(created_at);
GO
