# Model and preprocessing experiment results

## Protocol

- Chọn cấu hình bằng dev; các lệnh model chỉ nạp train/dev và không tính metric test. Pipeline vector hóa vẫn tạo `X_test` bằng `transform` từ vectorizer fit trên train, theo thiết kế artifacts hiện tại.
- Dùng cùng split: 11.426 train và 1.583 dev, tương ứng 73 mẫu neutral trên dev.
- Tuning mô hình dùng TF-IDF `text_segmented`, word unigram + bigram, 12.854 đặc trưng.
- Mỗi model/biến thể được fit riêng trên train; dev chỉ được transform.
- Các model candidate đã lưu riêng dưới `data/models/experiments/`; baseline hiện có không bị ghi đè.

## Tuning tham số

### Multinomial Naive Bayes

| Alpha | Accuracy | Macro-F1 | Neutral F1 |
|---:|---:|---:|---:|
| 0.1 | 0.8907 | 0.6870 | 0.2418 |
| 0.5 | 0.8844 | 0.6206 | 0.0533 |
| 1.0 | 0.8863 | 0.6046 | 0.0000 |
| 2.0 | 0.8844 | 0.6033 | 0.0000 |

Trong grid đã thử, giữ `alpha=0.1` làm candidate NB theo Macro-F1. Neutral vẫn là điểm yếu (recall 0.1507, F1 0.2418).

### LinearSVC

| C | Class weight | Accuracy | Macro-F1 | Neutral F1 |
|---:|---|---:|---:|---:|
| 0.1 | balanced | 0.9090 | 0.7668 | 0.4444 |
| 1.0 | balanced | 0.9078 | **0.7703** | **0.4559** |
| 10 | balanced | 0.8895 | 0.7375 | 0.3885 |
| 0.1 | none | 0.9084 | 0.6612 | 0.1282 |
| 1.0 | none | 0.9116 | 0.7404 | 0.3636 |
| 10 | none | 0.8958 | 0.7405 | 0.3902 |

Giữ `C=1.0`, balanced làm candidate SVM. Bỏ class weight cho accuracy cao hơn ở một số C nhưng giảm Macro-F1 và neutral F1.

### Logistic Regression

| C | Class weight | Accuracy | Macro-F1 | Neutral recall | Neutral F1 |
|---:|---|---:|---:|---:|---:|
| 0.1 | balanced | 0.8414 | 0.7075 | **0.6027** | 0.3607 |
| 1.0 | balanced | 0.8907 | 0.7573 | 0.5616 | 0.4339 |
| 10 | balanced | 0.8977 | **0.7647** | 0.5205 | **0.4497** |
| 0.1 | none | 0.8838 | 0.6029 | 0.0000 | 0.0000 |
| 1.0 | none | 0.9116 | 0.6922 | 0.1233 | 0.2169 |
| 10 | none | 0.9103 | 0.7395 | 0.2466 | 0.3636 |

Giữ `C=10`, balanced làm candidate LR nếu ưu tiên Macro-F1; `C=0.1`, balanced có neutral recall cao hơn nhưng Macro-F1 thấp. Bỏ class weight làm accuracy tăng nhưng Macro-F1 và neutral recall giảm mạnh.

## Thử nghiệm preprocessing

Dùng candidate alpha/C đã chọn ở trên và giữ nguyên train/dev split. Mỗi hàng là một vectorizer fit riêng trên train; feature count có thể khác do representation/ngram thay đổi.

| Text representation | N-gram | Feature count | NB Macro-F1 | SVM Macro-F1 | LR Macro-F1 |
|---|---|---:|---:|---:|---:|
| `text_segmented` | unigram + bigram | 12.854 | **0.6870** | **0.7703** | **0.7647** |
| `text_no_stopword` | unigram + bigram | 10.223 | 0.6885 | 0.7302 | 0.7318 |
| `text_segmented` | unigram | 2.019 | 0.6240 | 0.7579 | 0.7379 |

`text_no_stopword` cải thiện NB Macro-F1 chỉ 0.0015 nhưng làm giảm neutral errors/recall trade-off cần được xem cùng metric lớp; nó giảm Macro-F1 của SVM 0.0401 và LR 0.0329. Bỏ bigram làm Macro-F1 giảm ở cả ba model. Chọn `text_segmented` unigram + bigram để tiếp tục so sánh vì cho kết quả mạnh và ổn định hơn trên SVM/LR; không kết luận một thay đổi nhỏ của NB là cải thiện tổng quát.

## Kiểm tra rò rỉ trùng văn bản

Trong bước QA riêng (không dùng nhãn hoặc metric test để chọn model), chuẩn hóa văn bản các split bằng `clean_text` cho số câu trùng chính xác giữa các cặp như sau:

| Split pair | Overlap |
|---|---:|
| train–dev | 0 |
| train–test | 0 |
| dev–test | 0 |

Đây là kiểm tra trùng chính xác sau chuẩn hóa, không loại trừ câu gần trùng/paraphrase.

## Candidate cho bước so sánh ba model

| Model | Cấu hình candidate | Dev Accuracy | Dev Macro-F1 | Neutral recall | Neutral F1 |
|---|---|---:|---:|---:|---:|
| MultinomialNB | alpha=0.1 | 0.8907 | 0.6870 | 0.1507 | 0.2418 |
| LinearSVC | C=1, balanced | 0.9078 | **0.7703** | 0.4247 | **0.4559** |
| Logistic Regression | C=10, balanced | 0.8977 | 0.7647 | 0.5205 | 0.4497 |

Theo Macro-F1, SVM là candidate tốt nhất trong ba; LR có neutral recall cao nhất. Cần giữ tiêu chí lựa chọn rõ ràng khi phân tích lỗi. Đây vẫn là kết quả dev, không phải đánh giá cuối cùng.

Biểu đồ so sánh F1 theo lớp, Macro-F1 và Accuracy:

![Dev metric comparison](figures/model_comparison_dev.png)

Confusion matrices chuẩn hóa theo hàng; số trong ngoặc là số mẫu:

![Dev confusion matrices](figures/confusion_matrices_dev.png)

## Tái lập preprocessing experiments

```powershell
$env:PYTHONPATH="app/ml/src"
python -m sentiment_analysis.cli --text-column text_no_stopword --processed-dir $env:TEMP\sa-no-stopword\processed --vectorized-dir $env:TEMP\sa-no-stopword\vectorized --report $env:TEMP\sa-no-stopword\eda.md
python -m sentiment_analysis.cli --ngram-setting unigram --processed-dir $env:TEMP\sa-unigram\processed --vectorized-dir $env:TEMP\sa-unigram\vectorized --report $env:TEMP\sa-unigram\eda.md
```

CLI mặc định vẫn giữ `text_segmented` và unigram + bigram; mỗi phép thử tạo một bộ artifacts riêng. Reports model cụ thể của các candidates nằm trong `app/ml/reports/experiments/`.
