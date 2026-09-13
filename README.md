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
pip install -r requirements.txt
```

Dataset đã được chia sẵn thành ba tập trong `data/`. Mỗi dòng ở ba file `sents.txt`, `sentiments.txt` và `topics.txt` trong cùng một thư mục là một mẫu tương ứng. Nhãn cảm xúc là `0` tiêu cực, `1` trung tính và `2` tích cực; nhãn topic là `0` giảng viên, `1` chương trình đào tạo, `2` cơ sở vật chất và `3` khác.

## EDA và tiền xử lý

Chạy pipeline từ thư mục gốc của project:

```powershell
$env:PYTHONPATH="src"
python -m sentiment_analysis.cli
```

Lệnh trên đọc dữ liệu từ `data/`, làm sạch văn bản tiếng Việt, tách từ bằng `underthesea`, loại stop-word có chọn lọc và tạo:

- `data/processed/dataset_clean.csv`: dữ liệu có `text_clean`, `text_length` và `word_count`, sẵn sàng vector hóa.
- `data/processed/dataset_preprocessed.csv`: dữ liệu đầy đủ với thêm `text_segmented` và `text_no_stopword`, dùng trực tiếp cho Tuần 4.
- `reports/eda_report.md`: báo cáo số mẫu, tỷ lệ nhãn và độ dài văn bản.

Các từ phủ định như `không`, `chưa` và `chẳng` được giữ lại khi loại stop-word để không làm mất tín hiệu cảm xúc.

Kết quả EDA hiện tại: **16.175 mẫu**, trung bình **58,74 ký tự** và **14,22 từ** mỗi văn bản. Phân bố cảm xúc: tiêu cực **45,99%**, trung tính **4,32%**, tích cực **49,69%**.

Sau pipeline, có thể dùng các notebook theo thứ tự:

1. `01_eda.ipynb`: khám phá và kiểm tra chất lượng dữ liệu.
2. `02_preprocessing.ipynb`: làm sạch, chuẩn hóa và chia tập dữ liệu.
3. `03_baseline_model.ipynb`: xây dựng mô hình baseline.
4. `04_evaluation.ipynb`: đánh giá, trực quan hóa và phân tích lỗi.

## Phân chia gợi ý cho nhóm hai người

- **Thành viên 1:** thu thập dữ liệu, EDA, tiền xử lý và đặc trưng.
- **Thành viên 2:** mô hình hóa, đánh giá, trực quan hóa và demo.
- Cùng thống nhất nhãn cảm xúc, tiêu chí đánh giá và ghi kết quả vào `docs/`.

## Lệnh hữu ích

```powershell
pytest
python -m sentiment_analysis.cli --help
```