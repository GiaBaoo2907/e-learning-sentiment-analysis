# Error analysis: LinearSVC (dev)

## Protocol

- Chỉ dùng dev để phân tích; test không được tải hoặc đánh giá.
- Text, topic, nhãn và feature được kiểm tra số dòng/thứ tự trước khi ghép.
- Model: `models\experiments\linear_svm_c_1_balanced.joblib`; processed data: `data\processed\dataset_preprocessed.csv`.
- Samples: 1,583; features: 12,854.

## Overall result

- Accuracy: 0.9078
- Macro-F1: 0.7703
- Errors: 146 / 1,583

## Confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | Negative | Neutral | Positive |
|---|---:|---:|---:|
| negative | 653 | 17 | 35 |
| neutral | 28 | 31 | 14 |
| positive | 37 | 15 | 753 |

## Error rate by topic

| Topic | Samples | Errors | Accuracy | Macro-F1 | Neutral support | Neutral recall |
|---|---:|---:|---:|---:|---:|---:|
| lecturer | 1151 | 87 | 0.9244 | 0.7268 | 32 | 0.2812 |
| training program | 267 | 32 | 0.8801 | 0.7064 | 14 | 0.3571 |
| facility | 70 | 7 | 0.9000 | 0.3158 | 1 | 0.0000 |
| other | 95 | 20 | 0.7895 | 0.7832 | 26 | 0.6538 |

## Most frequent error directions and examples

Examples are selected from dev errors for qualitative inspection; they are not automatic explanations.

### positive → negative (37 samples)

- Topic: training program; text: ngoài ra cung cấp một vài thông tin bổ sung về việc học công nghệ thông tin hiệu quả hơn .
- Topic: training program; text: thúc đẩy sinh viên tự học đạt điểm cao trong các kỳ thi .
- Topic: training program; text: dành ra những tiết thực hành nghe nói riêng tạo sự tự nhiên cho sinh viên khi giao tiếp bằng tiếng anh .

### negative → positive (35 samples)

- Topic: lecturer; text: đôi khi giảng dạy quá nhiệt tình mà quên mất cả thời gian ( hết giờ học giảng viên vẫn dạy thêm 10 - 15 phút ) .
- Topic: lecturer; text: không đi đúng giờ .
- Topic: lecturer; text: giảng viên nói tiếng anh không hay .

### neutral → negative (28 samples)

- Topic: other; text: em không có bất cứ một lời phê bình nào .
- Topic: lecturer; text: thầy cho tự tìm hiểu , và tự tìm hiểu khác với hiểu được vấn đề .
- Topic: training program; text: được 200 điểm là đươc 1 điểm quá trình .

### negative → neutral (17 samples)

- Topic: lecturer; text: cô rất nghiêm .
- Topic: lecturer; text: cô có tổ chức một hoạt động về anh văn nhưng em thấy chưa thực sự có hiệu quả ( đó là ý kiến cá nhân của em ) .
- Topic: other; text: đừng có một chỗ tiếng anh một chỗ tiếng việt .

### positive → neutral (15 samples)

- Topic: training program; text: đề cập về tính thực tế , liên quan của hệ thống kiến thức .
- Topic: training program; text: đồ án cuối kỳ trong vòng một tháng cuối , áp dụng được quy trình thực tế .
- Topic: lecturer; text: tận dụng hết thời gian .

## How to use this analysis

1. Review the largest confusion directions and topic-level metrics first.
2. Read example sentences and manually assign error causes (negation, mixed sentiment, short/ambiguous text, slang/emoji, or annotation ambiguity).
3. Count causes before changing preprocessing or model settings; make one change at a time and re-evaluate on dev.
4. Freeze model and configuration before the one-time final test evaluation.

Topic-conditioned results are diagnostic only; the classifier predicts sentiment, not topic.
Error sample table for manual annotation: `reports\error_analysis_svm_dev_samples.csv`.
