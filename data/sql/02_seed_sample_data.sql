/*
  Idempotent local demonstration data for ElearningSentiment.
  Run after 01_schema.sql. Demo accounts use the password Demo1234!.
  Change or remove these accounts before using a non-demo environment.
*/
USE ElearningSentiment;
GO
SET NOCOUNT ON;

DECLARE @now DATETIME2(7) = SYSUTCDATETIME();

IF NOT EXISTS (SELECT 1 FROM dbo.Categories WHERE name = N'Lập trình')
    INSERT INTO dbo.Categories(name, description)
    VALUES (N'Lập trình', N'Các khóa học lập trình và phát triển phần mềm');

/* Users: hashes use the same scrypt format as app/be/web_security.py. */
IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE email = N'admin@demo.example.com')
BEGIN
    INSERT INTO dbo.Users(full_name, email, password_hash, role, is_active, created_at)
    VALUES (N'Quản trị viên mẫu', N'admin@demo.example.com',
        N'scrypt$16384$8$1$ABEiM0RVZneImaq7zN3u_w$GcAok2YrU2Yy8SPYr26SyYo8mWcIE-_GdKiuBygvcUo',
        N'admin', 1, @now);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE email = N'student1@demo.example.com')
BEGIN
    INSERT INTO dbo.Users(full_name, email, password_hash, role, is_active, created_at)
    VALUES (N'Sinh viên mẫu 1', N'student1@demo.example.com',
        N'scrypt$16384$8$1$_-7dzLuqmYh3ZlVEMyIRAA$zc5d8ODFX5DuTAR1V-sAIlBSp3JCAYaXCRa2dCZdZ0U',
        N'student', 1, @now);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE email = N'student2@demo.example.com')
BEGIN
    INSERT INTO dbo.Users(full_name, email, password_hash, role, is_active, created_at)
    VALUES (N'Sinh viên mẫu 2', N'student2@demo.example.com',
        N'scrypt$16384$8$1$ABEiM0RVZneImaq7zN3u_w$GcAok2YrU2Yy8SPYr26SyYo8mWcIE-_GdKiuBygvcUo',
        N'student', 1, @now);
END;

DECLARE @adminId INT = (SELECT id FROM dbo.Users WHERE email = N'admin@demo.example.com');
DECLARE @student1Id INT = (SELECT id FROM dbo.Users WHERE email = N'student1@demo.example.com');
DECLARE @student2Id INT = (SELECT id FROM dbo.Users WHERE email = N'student2@demo.example.com');
DECLARE @categoryId INT = (SELECT id FROM dbo.Categories WHERE name = N'Lập trình');

/* Courses */
IF NOT EXISTS (SELECT 1 FROM dbo.Courses WHERE title = N'Python cho người mới bắt đầu')
BEGIN
    INSERT INTO dbo.Courses(category_id, title, instructor, description, thumbnail_url, is_published, created_at, updated_at)
    VALUES (@categoryId, N'Python cho người mới bắt đầu', N'Nguyễn Minh An',
        N'Làm quen với Python qua các ví dụ thực hành, biến, kiểu dữ liệu và hàm.',
        N'https://images.unsplash.com/photo-1516321318423-f06f85e504b3', 1, @now, @now);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Courses WHERE title = N'Phân tích dữ liệu cơ bản')
BEGIN
    INSERT INTO dbo.Courses(category_id, title, instructor, description, thumbnail_url, is_published, created_at, updated_at)
    VALUES (@categoryId, N'Phân tích dữ liệu cơ bản', N'Trần Thu Hà',
        N'Tìm hiểu quy trình làm sạch, khám phá và trực quan hóa dữ liệu.',
        N'https://images.unsplash.com/photo-1551288049-bebda4e38f71', 1, @now, @now);
END;

DECLARE @pythonCourseId INT = (SELECT id FROM dbo.Courses WHERE title = N'Python cho người mới bắt đầu');
DECLARE @dataCourseId INT = (SELECT id FROM dbo.Courses WHERE title = N'Phân tích dữ liệu cơ bản');

/* Lessons */
IF NOT EXISTS (SELECT 1 FROM dbo.Lessons WHERE course_id = @pythonCourseId AND position = 1)
    INSERT INTO dbo.Lessons(course_id, title, description, video_url, position, duration_seconds)
    VALUES (@pythonCourseId, N'Bài 1: Làm quen với Python', N'Cài đặt và chạy chương trình đầu tiên.',
        N'https://www.youtube-nocookie.com/embed/kqtD5dpn9C8', 1, 720);

IF NOT EXISTS (SELECT 1 FROM dbo.Lessons WHERE course_id = @pythonCourseId AND position = 2)
    INSERT INTO dbo.Lessons(course_id, title, description, video_url, position, duration_seconds)
    VALUES (@pythonCourseId, N'Bài 2: Biến và kiểu dữ liệu', N'Thực hành với biến và các kiểu dữ liệu cơ bản.',
        N'https://www.youtube-nocookie.com/embed/kqtD5dpn9C8', 2, 900);

IF NOT EXISTS (SELECT 1 FROM dbo.Lessons WHERE course_id = @dataCourseId AND position = 1)
    INSERT INTO dbo.Lessons(course_id, title, description, video_url, position, duration_seconds)
    VALUES (@dataCourseId, N'Bài 1: Quy trình phân tích dữ liệu', N'Các bước cơ bản của một dự án phân tích dữ liệu.',
        N'https://www.youtube-nocookie.com/embed/kqtD5dpn9C8', 1, 840);

DECLARE @pythonLesson1Id INT = (SELECT id FROM dbo.Lessons WHERE course_id = @pythonCourseId AND position = 1);
DECLARE @pythonLesson2Id INT = (SELECT id FROM dbo.Lessons WHERE course_id = @pythonCourseId AND position = 2);
DECLARE @dataLesson1Id INT = (SELECT id FROM dbo.Lessons WHERE course_id = @dataCourseId AND position = 1);

/* Enrollments */
IF NOT EXISTS (SELECT 1 FROM dbo.Enrollments WHERE user_id = @student1Id AND course_id = @pythonCourseId)
    INSERT INTO dbo.Enrollments(user_id, course_id, enrolled_at) VALUES (@student1Id, @pythonCourseId, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.Enrollments WHERE user_id = @student2Id AND course_id = @pythonCourseId)
    INSERT INTO dbo.Enrollments(user_id, course_id, enrolled_at) VALUES (@student2Id, @pythonCourseId, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.Enrollments WHERE user_id = @student2Id AND course_id = @dataCourseId)
    INSERT INTO dbo.Enrollments(user_id, course_id, enrolled_at) VALUES (@student2Id, @dataCourseId, @now);

/* Lesson progress */
IF NOT EXISTS (SELECT 1 FROM dbo.LessonProgress WHERE user_id = @student1Id AND lesson_id = @pythonLesson1Id)
    INSERT INTO dbo.LessonProgress(user_id, lesson_id, is_completed, updated_at) VALUES (@student1Id, @pythonLesson1Id, 1, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.LessonProgress WHERE user_id = @student1Id AND lesson_id = @pythonLesson2Id)
    INSERT INTO dbo.LessonProgress(user_id, lesson_id, is_completed, updated_at) VALUES (@student1Id, @pythonLesson2Id, 1, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.LessonProgress WHERE user_id = @student2Id AND lesson_id = @pythonLesson1Id)
    INSERT INTO dbo.LessonProgress(user_id, lesson_id, is_completed, updated_at) VALUES (@student2Id, @pythonLesson1Id, 1, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.LessonProgress WHERE user_id = @student2Id AND lesson_id = @pythonLesson2Id)
    INSERT INTO dbo.LessonProgress(user_id, lesson_id, is_completed, updated_at) VALUES (@student2Id, @pythonLesson2Id, 1, @now);
IF NOT EXISTS (SELECT 1 FROM dbo.LessonProgress WHERE user_id = @student2Id AND lesson_id = @dataLesson1Id)
    INSERT INTO dbo.LessonProgress(user_id, lesson_id, is_completed, updated_at) VALUES (@student2Id, @dataLesson1Id, 1, @now);

/* Feedback rows cover the three sentiment labels for the admin dashboard. */
IF NOT EXISTS (SELECT 1 FROM dbo.Feedback WHERE user_id = @student1Id AND course_id = @pythonCourseId AND lesson_id = @pythonLesson1Id)
    INSERT INTO dbo.Feedback(user_id, course_id, lesson_id, rating, text, sentiment, moderation_status, created_at, updated_at)
    VALUES (@student1Id, @pythonCourseId, @pythonLesson1Id, 5, N'Bài giảng dễ hiểu, ví dụ rất hay.', 2, N'visible', @now, @now);

IF NOT EXISTS (SELECT 1 FROM dbo.Feedback WHERE user_id = @student2Id AND course_id = @pythonCourseId AND lesson_id = @pythonLesson2Id)
    INSERT INTO dbo.Feedback(user_id, course_id, lesson_id, rating, text, sentiment, moderation_status, created_at, updated_at)
    VALUES (@student2Id, @pythonCourseId, @pythonLesson2Id, 2, N'Nội dung phần này khó theo dõi.', 0, N'visible', @now, @now);

IF NOT EXISTS (SELECT 1 FROM dbo.Feedback WHERE user_id = @student2Id AND course_id = @dataCourseId AND lesson_id = @dataLesson1Id)
    INSERT INTO dbo.Feedback(user_id, course_id, lesson_id, rating, text, sentiment, moderation_status, created_at, updated_at)
    VALUES (@student2Id, @dataCourseId, @dataLesson1Id, 3, N'Nội dung ở mức bình thường.', 1, N'visible', @now, @now);

/* An expired, already-used reset record demonstrates the table without creating a valid reset token. */
DECLARE @expiredTokenHash NVARCHAR(64) = LOWER(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CONVERT(VARBINARY(MAX), N'demo-expired-reset-token')), 2));
IF NOT EXISTS (SELECT 1 FROM dbo.PasswordResets WHERE token_hash = @expiredTokenHash)
    INSERT INTO dbo.PasswordResets(user_id, token_hash, expires_at, used_at)
    VALUES (@student1Id, @expiredTokenHash, DATEADD(DAY, -2, @now), DATEADD(DAY, -2, @now));

SELECT N'Sample data is ready.' AS result,
       (SELECT COUNT(*) FROM dbo.Users) AS users,
       (SELECT COUNT(*) FROM dbo.Courses) AS courses,
       (SELECT COUNT(*) FROM dbo.Lessons) AS lessons,
       (SELECT COUNT(*) FROM dbo.Feedback) AS feedback;
GO
