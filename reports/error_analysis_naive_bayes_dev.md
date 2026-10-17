# Error analysis: MultinomialNB (dev)

## Protocol

- Chỉ dùng dev để phân tích; test không được tải hoặc đánh giá.
- Text, topic, nhãn và feature được kiểm tra số dòng/thứ tự trước khi ghép.
- Model: `models\experiments\naive_bayes_alpha_0_1.joblib`; processed data: `data\processed\dataset_preprocessed.csv`.
- Samples: 1,583; features: 12,854.

## Overall result

- Accuracy: 0.8907
- Macro-F1: 0.6870
- Errors: 173 / 1,583

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 670 | 5 | 30 |
| neutral | 42 | 11 | 20 |
| positive | 74 | 2 | 729 |

## Error rate by topic

| Topic | Samples | Errors | Accuracy | Macro-F1 | Neutral support | Neutral recall |
|---|---:|---:|---:|---:|---:|---:|
| lecturer | 1151 | 108 | 0.9062 | 0.6272 | 32 | 0.0312 |
| training program | 267 | 34 | 0.8727 | 0.6059 | 14 | 0.0714 |
| facility | 70 | 2 | 0.9714 | 0.3285 | 1 | 0.0000 |
| other | 95 | 29 | 0.6947 | 0.6586 | 26 | 0.3462 |

## Most frequent error directions and examples

Examples are selected from dev errors for qualitative inspection; they are not automatic explanations.

### positive → negative (74 samples)

- Topic: training program; text: ngoài ra cung cấp một vài thông tin bổ sung về việc học công nghệ thông tin hiệu quả hơn .
- Topic: lecturer; text: giảng viên giảng nhiều bài tập và tăng cường ôn tập ngữ pháp và luyện nói .
- Topic: training program; text: đồ án cuối kỳ trong vòng một tháng cuối , áp dụng được quy trình thực tế .

### neutral → negative (42 samples)

- Topic: other; text: em không có bất cứ một lời phê bình nào .
- Topic: lecturer; text: thầy cho tự tìm hiểu , và tự tìm hiểu khác với hiểu được vấn đề .
- Topic: other; text: tạm được .

### negative → positive (30 samples)

- Topic: lecturer; text: mong thầy dạy tận tâm hơn !
- Topic: lecturer; text: không đi đúng giờ .
- Topic: lecturer; text: cô rất nghiêm .

### neutral → positive (20 samples)

- Topic: lecturer; text: truyền đạt kiến thức .
- Topic: lecturer; text: sự nhiệt tình .
- Topic: lecturer; text: cẩn thận .

### negative → neutral (5 samples)

- Topic: lecturer; text: cô có tổ chức một hoạt động về anh văn nhưng em thấy chưa thực sự có hiệu quả ( đó là ý kiến cá nhân của em ) .
- Topic: lecturer; text: em mong muốn được nghe thầy kể nhiều câu chuyện về sự nghiệp và cuộc đời , gian nan từng trải của thầy trong các bài học nhiều hơn nữa , có lẻ sinh viên sẽ học được nhiều điều hơn .
- Topic: lecturer; text: thầy chơi đểu em nhé , gọi em 2 lần làm em 1 con dấu nợ đấy !

## How to use this analysis

1. Review the largest confusion directions and topic-level metrics first.
2. Read example sentences and manually assign error causes (negation, mixed sentiment, short/ambiguous text, slang/emoji, or annotation ambiguity).
3. Count causes before changing preprocessing or model settings; make one change at a time and re-evaluate on dev.
4. Freeze model and configuration before the one-time final test evaluation.

Topic-conditioned results are diagnostic only; the classifier predicts sentiment, not topic.
Error sample table for manual annotation: `reports\error_analysis_naive_bayes_dev_samples.csv`.
