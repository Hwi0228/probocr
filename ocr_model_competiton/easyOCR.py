import csv
import os
import time
import unicodedata


def normalize_text(text, ignore_space=True, normalize_quotes=True):
    t = unicodedata.normalize("NFC", text)
    if normalize_quotes:
        quote_map = {
            "‘": "'",
            "’": "'",
            "`": "'",
            "´": "'",
            "“": '"',
            "”": '"',
        }
        for q, rep in quote_map.items():
            t = t.replace(q, rep)
    if ignore_space:
        t = t.replace(" ", "")
    return t.strip()


def calculate_metrics(ref_text, hyp_text):
    r = normalize_text(ref_text)
    h = normalize_text(hyp_text)

    dp = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    edit_distance = dp[len(r)][len(h)]
    ref_len = len(r) if len(r) > 0 else 1

    cer = (edit_distance / ref_len) * 100
    accuracy = max(0.0, 100.0 - cer)
    return edit_distance, accuracy


def run_easyocr_evaluation(
    gt_file="ground_truth.txt",
    image_dir="cropped_lines",
    output_csv="easyocr_results.csv",
):
    if not os.path.exists(gt_file):
        print(f"원문 파일이 없습니다: {gt_file}")
        return

    with open(gt_file, "r", encoding="utf-8") as f:
        gt_lines = [line.strip() for line in f if line.strip()]

    import easyocr

    print("EasyOCR 모델 로딩 중 (한국어/영어)...")
    reader = easyocr.Reader(["ko", "en"], gpu=False)

    print(
        f"\nEasyOCR 평가 시작 (총 {len(gt_lines)}개 줄, 정규화 기준 적용)"
    )
    print("=" * 85)
    print(
        f"{'번호':^5} | {'이미지 파일':<15} | {'추론시간':^8} | {'일치율':^8} | {'상태':^6}"
    )
    print("=" * 85)

    results = []
    total_acc = 0.0
    total_time = 0.0
    valid_count = 0

    for idx, gt_text in enumerate(gt_lines, start=1):
        img_name = f"line_{idx:02d}.png"
        img_path = os.path.join(image_dir, img_name)

        if not os.path.exists(img_path):
            continue

        start_t = time.perf_counter()
        ocr_res_list = reader.readtext(img_path, detail=0)
        ocr_result = " ".join(ocr_res_list)
        infer_time = time.perf_counter() - start_t

        errors, acc = calculate_metrics(gt_text, ocr_result)

        total_acc += acc
        total_time += infer_time
        valid_count += 1

        status = "PERFECT" if errors == 0 else f"{errors}자 오차"
        print(
            f"[{idx:02d}]   | {img_name:<15} | {infer_time:.3f}초   | {acc:6.1f}%  | {status}"
        )

        results.append(
            {
                "index": idx,
                "ground_truth": gt_text,
                "ocr_result": normalize_text(ocr_result, False, True),
                "errors": errors,
                "accuracy": round(acc, 2),
                "infer_time_sec": round(infer_time, 4),
            }
        )

    if results:
        with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    print("=" * 85)
    if valid_count > 0:
        print(f"[EasyOCR 최종 결과]")
        print(f"• 전체 검증 줄 수   : {valid_count} / {len(gt_lines)}")
        print(f"• 평균 글자 일치율  : {total_acc / valid_count:.2f}%")
        print(f"• 평균 장당 추론 속도: {total_time / valid_count:.3f}초")
        print(f"• 결과 저장 파일    : {os.path.abspath(output_csv)}")
    print("=" * 85)


if __name__ == "__main__":
    run_easyocr_evaluation()