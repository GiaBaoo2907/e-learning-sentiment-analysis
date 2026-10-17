# Error analysis: LogisticRegression (dev)

## Protocol

- Chỉ dùng dev để phân tích; test không được tải hoặc đánh giá.
- Text, topic, nhãn và feature được kiểm tra số dòng/thứ tự trước khi ghép.
- Model: `models\experiments\logistic_regression_c_10_balanced.joblib`; processed data: `data\processed\dataset_preprocessed.csv`.
- Samples: 1,583; features: 12,854.

## Overall result

- Accuracy: 0.8977
- Macro-F1: 0.7647
- Errors: 162 / 1,583

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 642 | 32 | 31 |
| neutral | 24 | 38 | 11 |
| positive | 38 | 26 | 741 |

## Error rate by topic

| Topic | Samples | Errors | Accuracy | Macro-F1 | Neutral support | Neutral recall |
|---|---:|---:|---:|---:|---:|---:|
| lecturer | 1151 | 95 | 0.9175 | 0.7351 | 32 | 0.4062 |
| training program | 267 | 36 | 0.8652 | 0.7160 | 14 | 0.5714 |
| facility | 70 | 7 | 0.9000 | 0.3158 | 1 | 0.0000 |
| other | 95 | 24 | 0.7474 | 0.7434 | 26 | 0.6538 |

## Most frequent error directions and examples

Examples are selected from dev errors for qualitative inspection; they are not automatic explanations.

### positive → negative (38 samples)

- Topic: training program; text: ngoài ra cung cấp một vài thông tin bổ sung về việc học công nghệ thông tin hiệu quả hơn .
- Topic: training program; text: dành ra những tiết thực hành nghe nói riêng tạo sự tự nhiên cho sinh viên khi giao tiếp bằng tiếng anh .
- Topic: lecturer; text: thầy ít có giảng về bài tập , chỉ cho sinh viên tự tìm hiểu .

### negative → neutral (32 samples)

- Topic: lecturer; text: cô rất nghiêm .
- Topic: lecturer; text: không check mail mỗi khi hỏi bài .
- Topic: lecturer; text: không dễ tính .

### negative → positive (31 samples)

- Topic: lecturer; text: đôi khi giảng dạy quá nhiệt tình mà quên mất cả thời gian ( hết giờ học giảng viên vẫn dạy thêm 10 - 15 phút ) .
- Topic: lecturer; text: không đi đúng giờ .
- Topic: lecturer; text: giảng viên nói tiếng anh không hay .

### positive → neutral (26 samples)

- Topic: training program; text: đề cập về tính thực tế , liên quan của hệ thống kiến thức .
- Topic: training program; text: đồ án cuối kỳ trong vòng một tháng cuối , áp dụng được quy trình thực tế .
- Topic: training program; text: thúc đẩy sinh viên tự học đạt điểm cao trong các kỳ thi .

### neutral → negative (24 samples)

- Topic: other; text: em không có bất cứ một lời phê bình nào .
- Topic: other; text: tạm được .
- Topic: training program; text: được 200 điểm là đươc 1 điểm quá trình .

## How to use this analysis

1. Review the largest confusion directions and topic-level metrics first.
2. Read example sentences and manually assign error causes (negation, mixed sentiment, short/ambiguous text, slang/emoji, or annotation ambiguity).
3. Count causes before changing preprocessing or model settings; make one change at a time and re-evaluate on dev.
4. Freeze model and configuration before the one-time final test evaluation.

Topic-conditioned results are diagnostic only; the classifier predicts sentiment, not topic.
Error sample table for manual annotation: `reports\error_analysis_logistic_regression_dev_samples.csv`.
