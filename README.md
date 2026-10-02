# E-learning Sentiment Analysis

> Phân tích cảm xúc từ phản hồi của người học trên nền tảng e-learning.

## Cấu trúc dự án

```text
.
├── configs/                  # Cấu hình dữ liệu và mô hình
├── data/
│   ├── train/                # Dữ liệu gốc: câu, nhãn cảm xúc, topic
│   ├── dev/                  # Tập phát triển
│   ├── test/                 # Tập kiểm tra
│   └── processed/            # Dữ liệu sau tiền xử lý
├── docs/                     # Tài liệu, phân công, quyết định kỹ thuật
├── models/                   # Model và tokenizer đã huấn luyện
├── notebooks/                # EDA, thử nghiệm và phân tích kết quả
├── reports/                  # Báo cáo EDA và hình minh họa
├── src/sentiment_analysis/   # Mã nguồn chính
├── tests/                    # Kiểm thử
├── .env.example              # Biến môi trường mẫu
└── requirements.txt          # Thư viện Python
```

## Bắt đầu

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Chạy các lệnh tiếp theo trong PowerShell tại thư mục gốc project, sau khi đã activate `.venv`.

Dataset đã được chia sẵn thành ba tập trong `data/`. Mỗi dòng ở ba file `sents.txt`, `sentiments.txt` và `topics.txt` trong cùng một thư mục là một mẫu tương ứng. Nhãn cảm xúc là `0` tiêu cực, `1` trung tính và `2` tích cực; nhãn topic là `0` giảng viên, `1` chương trình đào tạo, `2` cơ sở vật chất và `3` khác.

## Workflow Tuần 2–5

### Tuần 2–4: EDA, tiền xử lý và TF-IDF

Lệnh này đọc dataset, sinh dữ liệu đã tiền xử lý, báo cáo EDA và TF-IDF artifacts. Chạy lại khi dataset hoặc bước tiền xử lý thay đổi:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli
```

Lệnh trên đọc dữ liệu từ `data/`, làm sạch văn bản tiếng Việt, tách từ bằng `underthesea`, loại stop-word có chọn lọc và tạo:

- `data/processed/dataset_preprocessed.csv`: dữ liệu có `text_clean`, `text_segmented`, `text_no_stopword`, `text_length` và `word_count`, dùng cho vector hóa và các bước tiếp theo.
- `data/processed/vectorized/`: ma trận TF-IDF sparse `X_{train,dev,test}.npz`, nhãn `y_{train,dev,test}.npy`, vectorizer đã lưu và metadata. TF-IDF chỉ fit trên train; dev/test chỉ được transform.
- `reports/eda_report.md`: báo cáo số mẫu, tỷ lệ nhãn và độ dài văn bản.

Trong `vectorized/`, `X_train/dev/test.npz` là ma trận đặc trưng và `y_train/dev/test.npy` là nhãn tương ứng. Vectorizer chỉ được fit trên train; dev/test chỉ transform.

Các từ phủ định như `không`, `chưa` và `chẳng` được giữ lại khi loại stop-word để không làm mất tín hiệu cảm xúc.

Kết quả EDA hiện tại: **16.175 mẫu**, trung bình **58,74 ký tự** và **14,22 từ** mỗi văn bản. Phân bố cảm xúc: tiêu cực **45,99%**, trung tính **4,32%**, tích cực **49,69%**.

Sau pipeline, có thể dùng các notebook theo thứ tự:

1. `01_eda.ipynb`: khám phá và kiểm tra chất lượng dữ liệu.
2. `02_preprocessing.ipynb`: làm sạch, chuẩn hóa và chia tập dữ liệu.
3. `03_baseline_model.ipynb`: xây dựng mô hình baseline.
4. `04_evaluation.ipynb`: đánh giá, trực quan hóa và phân tích lỗi.

TF-IDF Tuần 4 dùng unigram + bigram từ cột `text_segmented`. Tập đặc trưng này có thể dùng chung cho baseline SVM và Naive Bayes ở Tuần 5.

### Tuần 5: Naive Bayes baseline

Sau khi đã tạo TF-IDF artifacts, huấn luyện Multinomial Naive Bayes với `alpha=1.0` và đánh giá trên `dev`. Lệnh này không chạy lại preprocessing và không sử dụng test:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli --task train-naive-bayes
```

Model được lưu trong `models/naive_bayes_tfidf.joblib`; metric dev và confusion matrix trong `reports/naive_bayes_dev.md`. Baseline hiện đạt Accuracy **0,8863**, Macro-F1 **0,6046**; lớp neutral có F1 **0,0000**, cần đối chiếu với SVM. Tập test chưa được dùng.

### Tuần 5: Linear SVM

LinearSVC tìm siêu phẳng phân tách các lớp với biên lớn nhất trên vector TF-IDF. Tham số `C` điều chỉnh mức phạt lỗi so với độ rộng biên: `C` lớn ưu tiên fit dữ liệu train hơn, còn `C` nhỏ regularize mạnh hơn. Vì lớp neutral chỉ chiếm tỷ lệ nhỏ, cấu hình baseline dùng `class_weight="balanced"`; chỉ train được dùng để tính trọng số lớp.

Huấn luyện baseline và đánh giá trên dev:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli --task train-svm
```

Mặc định dùng `C=1.0`, lưu model ở `models/svm_tfidf.joblib` và báo cáo ở `reports/svm_dev.md`. Trên dev hiện tại, cấu hình này đạt Accuracy **0,9078**, Macro-F1 **0,7703**, neutral F1 **0,4559**; so với Naive Bayes, Macro-F1 tăng từ **0,6046** và neutral F1 từ **0,0000**. Đây là kết quả dev, chưa phải kết quả test. Thử các giá trị `C` bằng cách chạy riêng từng thí nghiệm, ví dụ:

```powershell
python -m sentiment_analysis.cli --task train-svm --c 0.1
python -m sentiment_analysis.cli --task train-svm --c 1.0
python -m sentiment_analysis.cli --task train-svm --c 10
```

Mỗi lần chạy ghi đè model và báo cáo mặc định; hãy ghi lại `C`, class weight, dev Macro-F1 và F1 từng lớp trước khi chọn cấu hình. Chọn theo Macro-F1 cùng khả năng nhận diện lớp neutral, không theo accuracy đơn lẻ. Sau khi lựa chọn, so sánh báo cáo SVM với [Naive Bayes](docs/naive_bayes.md); chỉ mở test cho đánh giá cuối cùng. Chi tiết câu hỏi nghiên cứu, lý thuyết và workflow được trình bày trong [tài liệu SVM](docs/svm.md).

### Kiểm thử

```powershell
python -m pytest -q
```

Nếu gặp lỗi không tìm thấy module `sentiment_analysis`, hãy đặt `$env:PYTHONPATH="src"` trong terminal hiện tại trước khi chạy lệnh CLI.

## Phân chia gợi ý cho nhóm hai người

- **Thành viên 1:** thu thập dữ liệu, EDA, tiền xử lý và đặc trưng.
- **Thành viên 2:** mô hình hóa, đánh giá, trực quan hóa và demo.
- Cùng thống nhất nhãn cảm xúc, tiêu chí đánh giá và ghi kết quả vào `docs/`.

## Lệnh hữu ích

```powershell
pytest
python -m sentiment_analysis.cli --help
```