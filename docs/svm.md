# Nghiên cứu Linear SVM cho phân tích cảm xúc

## Câu hỏi nghiên cứu

Với cùng dữ liệu TF-IDF unigram + bigram và cùng train/dev split, Linear SVM có cải thiện Macro-F1 và khả năng nhận diện lớp neutral so với Multinomial Naive Bayes không?

## Lý thuyết

Support Vector Machine (SVM) phân loại bằng cách tìm biên quyết định tách các lớp sao cho khoảng cách từ biên đến những điểm gần nhất (support vectors) được tối đa hóa. Với TF-IDF nhiều chiều và thưa, LinearSVC là lựa chọn tuyến tính hiệu quả; mô hình học một vector trọng số cho mỗi lớp và dự đoán lớp có điểm quyết định cao nhất.

Tham số `C` điều khiển đánh đổi giữa biên rộng và lỗi trên train. `C` lớn phạt lỗi phân loại mạnh hơn, có thể fit train sát hơn; `C` nhỏ regularize mạnh hơn. Không nên chọn `C` bằng kết quả train: so sánh các giá trị trên dev, giữ nguyên các split và đặc trưng.

Dữ liệu mất cân bằng đáng kể: neutral chiếm khoảng 4,32%, trong khi NB baseline không dự đoán được mẫu neutral nào. `class_weight="balanced"` đặt trọng số nghịch với tần suất lớp trong train, tăng mức phạt khi phân loại sai lớp hiếm. Đây là một lựa chọn cấu hình cần đánh giá trên dev, không đảm bảo tự động cải thiện mọi metric.

Khác với Naive Bayes, LinearSVC không tạo xác suất lớp trực tiếp. Mặc định đánh giá bằng nhãn dự đoán và không cần calibration xác suất cho câu hỏi nghiên cứu này.

## Workflow thí nghiệm

1. Dùng artifacts TF-IDF hiện có trong `data/processed/vectorized/`. Vectorizer đã fit trên train; không fit lại trên dev hoặc test.
2. Fit LinearSVC trên `X_train.npz` và `y_train.npy`. Baseline: `C=1.0`, `class_weight="balanced"`, `random_state=42`.
3. Dự đoán `X_dev.npz`; báo cáo Accuracy, Macro-F1, precision/recall/F1 từng lớp và confusion matrix. Ưu tiên Macro-F1 và theo dõi riêng recall/F1 của neutral.
4. Nếu cần tuning, thử một lưới nhỏ có định trước, chẳng hạn `C ∈ {0.1, 1, 10}`; giữ class weight và toàn bộ dữ liệu cố định để so sánh có kiểm soát. Ghi lại cả cấu hình không cân bằng lớp nếu muốn kiểm tra tác dụng của class weight (`--class-weight none`).
5. Chọn cấu hình dựa trên Macro-F1 dev và lỗi từng lớp; ghi kết quả vào báo cáo trước khi đánh giá test. Không dùng test để tuning hoặc chọn cấu hình.
6. Sau khi khóa cấu hình, thực hiện một lần đánh giá cuối trên test bằng quy trình được thống nhất cho dự án.

## Tái lập

Tạo TF-IDF artifacts nếu chưa có:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli
```

Chạy baseline và các cấu hình `C`:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli --task train-svm
python -m sentiment_analysis.cli --task train-svm --c 0.1
python -m sentiment_analysis.cli --task train-svm --c 10
```

Để bỏ cân bằng trọng số lớp, thêm `--class-weight none`. Có thể chỉ định `--model-path` và `--model-report` riêng để giữ lại artifact từng thí nghiệm; nếu không, lần chạy sau ghi đè file mặc định.

## Ghi nhận

| Thí nghiệm | C | Class weight | Dev Accuracy | Dev Macro-F1 | Neutral F1 | Ghi chú |
|---|---:|---|---:|---:|---:|---|
| LinearSVC | 0.1 | balanced | 0.9090 | 0.7668 | 0.4444 | Accuracy cao nhất trong ba cấu hình |
| LinearSVC | 1.0 | balanced | 0.9078 | 0.7703 | 0.4559 | Macro-F1 và neutral F1 cao nhất; baseline được giữ |
| LinearSVC | 10 | balanced | 0.8895 | 0.7375 | 0.3885 | Hiệu quả dev giảm với C lớn |

Các kết quả trên dùng cùng train/dev TF-IDF artifacts; test không được tải hoặc đánh giá. Chọn `C=1.0` làm cấu hình baseline tạm thời vì câu hỏi nghiên cứu ưu tiên Macro-F1 và nhận diện lớp neutral hơn accuracy đơn lẻ. Báo cáo chi tiết baseline nằm ở `reports/svm_dev.md`.