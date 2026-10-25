# Error Analysis workflow

## Mục tiêu

Error Analysis tìm ra các nhóm lỗi lặp lại và đặc điểm dữ liệu liên quan đến lỗi, thay vì chỉ báo một điểm số tổng hợp. Đây là phân tích chẩn đoán trên dev; nó không tự động giải thích nguyên nhân và không dùng test để sửa/tuning model.

## Đọc các metric

- Confusion matrix có hàng là nhãn thật, cột là nhãn dự đoán. Ô ngoài đường chéo là nhầm lẫn; ví dụ neutral → negative là mẫu neutral bị gán thành negative.
- Accuracy là tỷ lệ dự đoán đúng tổng thể; Macro-F1 trung bình F1 ba lớp, cho mỗi lớp trọng số ngang nhau.
- Phân tích theo topic giúp xác định nhóm phản hồi nào có nhiều lỗi. Đây là metric của sentiment trong từng topic, không phải model dự đoán topic.
- Luôn đọc support bên cạnh metric. Topic facility chỉ có 70 mẫu dev và có 1 neutral example; neutral recall ở nhóm này không đủ để khái quát.

## Tái lập báo cáo

Chạy từng model candidate đã tuning trên cùng dev artifacts:

```powershell
$env:PYTHONPATH="app/ml/src"
python -m sentiment_analysis.cli --task analyze-errors --model-path data/models/experiments/linear_svm_c_1_balanced.joblib --model-report app/ml/reports/error_analysis_svm_dev.md
python -m sentiment_analysis.cli --task analyze-errors --model-path data/models/experiments/logistic_regression_c_10_balanced.joblib --model-report app/ml/reports/error_analysis_logistic_regression_dev.md
python -m sentiment_analysis.cli --task analyze-errors --model-path data/models/experiments/naive_bayes_alpha_0_1.joblib --model-report app/ml/reports/error_analysis_naive_bayes_dev.md
```

Lệnh xác nhận số dòng processed dev, `y_dev` và `X_dev` bằng nhau; kiểm tra nhãn CSV khớp `y_dev`; kiểm tra số feature khớp model. Nếu alignment sai, dừng bằng lỗi thay vì gán nhầm câu. Chỉ nạp model, processed CSV, `X_dev` và `y_dev`; test không được tải hoặc đánh giá.

Mỗi report Markdown đi kèm CSV cùng basename, ví dụ `app/ml/reports/error_analysis_svm_dev_samples.csv`. CSV chứa tất cả dự đoán sai trên dev, nhãn thật/dự đoán, topic, hướng nhầm lẫn, nội dung gốc và cột trống `error_cause` để nhóm gán nhãn nguyên nhân.

## Quy trình gán nguyên nhân

1. Bắt đầu từ các cặp nhầm lẫn phổ biến trong report; sau đó mở CSV và lọc theo cặp nhầm lẫn/topic.
2. Đọc câu cùng topic và nhãn thật/dự đoán. Gán một nguyên nhân chính, có thể thêm ghi chú nếu câu thuộc nhiều nhóm.
3. Dùng codebook nhất quán: phủ định/phạm vi phủ định; câu có ý đối lập hoặc cảm xúc hỗn hợp; hàm ý/ngữ cảnh thiếu; từ lóng/viết tắt/emoji; câu quá ngắn hoặc khó phân cực; lỗi phân đoạn/tiền xử lý; có thể là nhãn mơ hồ/sai.
4. Gán nhãn tất cả lỗi nếu số lượng khả thi; nếu không, lấy mẫu phân tầng theo hướng nhầm lẫn và topic, ghi rõ cách lấy mẫu. Hai thành viên nên gán độc lập một phần mẫu rồi thống nhất các bất đồng.
5. Tổng hợp số lượng/tỷ lệ nguyên nhân và đưa ví dụ đã ẩn thông tin nhận diện nếu có. Chỉ sau khi thấy một nhóm lỗi lặp lại mới đề xuất thay đổi; mỗi vòng chỉ đổi một yếu tố và đánh giá lại trên dev.
6. Chốt model/preprocessing sau phân tích. Chỉ sau đó mới chạy đánh giá test cuối cùng một lần.

Không xem ba ví dụ tự động trong report là kết luận nguyên nhân. Chúng chỉ gợi ý hàng cần người nghiên cứu đọc.

## Kết quả dev hiện có

- LinearSVC C=1, balanced: 146 lỗi/1.583; Accuracy 0.9078; Macro-F1 0.7703. Lỗi lớn nhất: positive → negative (37), negative → positive (35), neutral → negative (28).
- Logistic Regression C=10, balanced: 162 lỗi/1.583; Accuracy 0.8977; Macro-F1 0.7647. Lỗi lớn nhất: positive → negative (38), negative → neutral (32), negative → positive (31).
- MultinomialNB alpha=0.1: 173 lỗi/1.583; Accuracy 0.8907; Macro-F1 0.6870. Lỗi lớn nhất: positive → negative (74), neutral → negative (42), negative → positive (30).

Theo topic, facility có support thấp và chỉ 1 neutral sample. Không nên kết luận model hoạt động tốt với neutral-facility chỉ từ metric nhóm đó. Xem các report theo model và CSV để hoàn thành gán nguyên nhân thủ công.

## Ranh giới với Final Test

Nếu Error Analysis dẫn đến sửa preprocessing, class weight hoặc model, đánh giá thay đổi trên dev. Không dùng test để quyết định sửa gì. Đóng băng model và cấu hình trước khi đánh giá test; nếu còn thử PhoBERT, hoàn thành việc chọn model trước lần test cuối cùng.
