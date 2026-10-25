# Nghiên cứu Logistic Regression cho phân tích cảm xúc

## Câu hỏi nghiên cứu

Trên cùng train/dev split và TF-IDF unigram + bigram, Logistic Regression có thể cung cấp baseline tuyến tính cạnh tranh với NB/SVM và cải thiện khả năng nhận diện lớp neutral không?

## Lý thuyết

Logistic Regression là mô hình phân loại tuyến tính. Với vector đặc trưng TF-IDF `x`, mô hình tính điểm tuyến tính cho từng lớp. Trong bài toán nhiều lớp, `solver="lbfgs"` tối ưu Logistic Regression đa lớp với softmax để chuyển các điểm thành xác suất; dự đoán là lớp có xác suất lớn nhất. Các xác suất có thể dùng để xem độ chắc chắn tương đối của dự đoán, nhưng chưa được hiệu chuẩn chỉ vì mô hình trả ra xác suất.

Tham số `C` là nghịch đảo độ mạnh regularization: `C` nhỏ áp dụng regularization mạnh hơn và thường giảm độ phức tạp hiệu dụng; `C` lớn regularize yếu hơn và có thể fit train sát hơn. Chọn `C` bằng kết quả dev, không bằng train hoặc test.

`class_weight="balanced"` điều chỉnh trọng số lớp dựa trên tần suất nhãn trong train, làm tăng mức phạt lỗi với lớp hiếm. Vì neutral chỉ chiếm phần nhỏ dữ liệu, đây là baseline đáng thử nhưng cần so sánh với `class_weight=None` trên dev. Accuracy đơn lẻ có thể che khuất hiệu quả lớp thiểu số; ưu tiên Macro-F1 và xem riêng precision/recall/F1 neutral.

## Workflow

1. Dùng artifacts TF-IDF đã tạo, với vectorizer fit trên train và cùng ma trận train/dev như NB/SVM.
2. Fit baseline `LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs", max_iter=2000)` trên train.
3. Đánh giá trên dev bằng Accuracy, Macro-F1, precision/recall/F1 từng lớp và confusion matrix. Lưu báo cáo và model để tái lập.
4. Trong tuning tuần 6–7, thử trước `C ∈ {0.1, 1, 10}` với `class_weight="balanced"`. Sau đó cố định C tốt nhất và so sánh `balanced` với `None`; mỗi lượt chỉ đổi một yếu tố.
5. Ghi lại mọi cấu hình, Macro-F1, neutral recall/F1 và cảnh báo hội tụ nếu có. Chọn theo mục tiêu đã thống nhất; không chọn cấu hình bằng test.
6. So sánh ba model trên dev trong bước kế hoạch tương ứng. Chỉ chạy đánh giá test sau khi khóa model, cấu hình và preprocessing.

## Tái lập

Chạy baseline:

```powershell
$env:PYTHONPATH="app/ml/src"
python -m sentiment_analysis.cli --task train-logistic-regression
```

Thử các cấu hình riêng. Mặc định model/report bị ghi đè, nên dùng đường dẫn riêng nếu cần lưu tất cả kết quả:

```powershell
python -m sentiment_analysis.cli --task train-logistic-regression --c 0.1 --model-path data/models/lr_c_0_1.joblib --model-report app/ml/reports/lr_c_0_1.md
python -m sentiment_analysis.cli --task train-logistic-regression --c 10 --model-path data/models/lr_c_10.joblib --model-report app/ml/reports/lr_c_10.md
python -m sentiment_analysis.cli --task train-logistic-regression --class-weight none --model-path data/models/lr_unweighted.joblib --model-report app/ml/reports/lr_unweighted.md
```

Các lệnh chỉ nạp train/dev artifacts; test không được tải hoặc đánh giá.

## Kết quả tuning dev

| C | Class weight | Accuracy | Macro-F1 | Neutral recall | Neutral F1 |
|---:|---|---:|---:|---:|---:|
| 0.1 | balanced | 0.8414 | 0.7075 | 0.6027 | 0.3607 |
| 1.0 | balanced | 0.8907 | 0.7573 | 0.5616 | 0.4339 |
| 10 | balanced | 0.8977 | 0.7647 | 0.5205 | 0.4497 |
| 0.1 | none | 0.8838 | 0.6029 | 0.0000 | 0.0000 |
| 1.0 | none | 0.9116 | 0.6922 | 0.1233 | 0.2169 |
| 10 | none | 0.9103 | 0.7395 | 0.2466 | 0.3636 |

Trên grid nhỏ này, cấu hình `C=10`, `class_weight="balanced"` có Macro-F1 và neutral F1 cao nhất trong các cấu hình Logistic Regression. Cấu hình `C=1`, balanced có neutral recall cao nhất; lựa chọn cuối cần dựa trên mục tiêu metric đã xác định trước. Bỏ class weighting tăng accuracy nhưng làm Macro-F1 và nhận diện neutral giảm rõ rệt.

Các phép thử preprocessing cùng tham số đã chọn đạt Macro-F1 0.7647 với `text_segmented` uni+bi-gram, 0.7318 với `text_no_stopword` uni+bi-gram và 0.7379 với `text_segmented` unigram. Giữ `text_segmented` uni+bi-gram làm representation hiện tại. Chưa có kết luận test; kết quả đầy đủ của ba model nằm trong `app/ml/reports/week6_7_experiments.md`.