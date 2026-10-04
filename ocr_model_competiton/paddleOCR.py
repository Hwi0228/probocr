import os

# PaddlePaddle 3.x PIR / OneDNN 연산 충돌 방지
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

import csv
import time
import warnings
import unicodedata

# Pydantic 및 라이브러리 경고 메시지 무시
warnings.filterwarnings("ignore")


def normalize_text(text, ignore_space=True, normalize_quotes=True):
    if not text:
        return ""
    t = unicodedata.normalize("NFC", str(text))
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


def extract_text_from_paddle_res(raw_res):
    """PaddleOCR v2/v3(PaddleX) 반환 구조 자동 탐색 및 텍스트 추출"""
    if not raw_res:
        return ""

    extracted_texts = []
    res = raw_res[0] if isinstance(raw_res, list) and len(raw_res) > 0 else raw_res

    # 1. PaddleOCR 3.x (PaddleX) Dict 또는 객체 형태 처리
    if isinstance(res, dict) or hasattr(res, "get") or hasattr(res, "keys"):
        res_dict = res if isinstance(res, dict) else (res.__dict__ if hasattr(res, "__dict__") else {})
        for key in ["rec_text", "rec_texts", "text", "texts", "rec_res"]:
            val = res_dict.get(key) if isinstance(res_dict, dict) else getattr(res, key, None)
            if val is not None:
                if isinstance(val, (list, tuple)):
                    for item in val:
                        if isinstance(item, str):
                            extracted_texts.append(item)
                        elif isinstance(item, (list, tuple)) and len(item) > 0:
                            extracted_texts.append(str(item[0]))
                        elif isinstance(item, dict):
                            extracted_texts.append(str(item.get("text") or item.get("rec_text") or ""))
                elif isinstance(val, str):
                    extracted_texts.append(val)
                break

    # 2. PaddleOCR v2 전통적인 리스트 형태 처리
    if not extracted_texts and isinstance(res, (list, tuple)):
        for item in res:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                if isinstance(item[1], (list, tuple)):
                    extracted_texts.append(str(item[1][0]))
                elif isinstance(item[1], str):
                    extracted_texts.append(str(item[1]))
            elif isinstance(item, dict):
                text_val = item.get("text") or item.get("rec_text") or item.get("transcription") or ""
                if text_val:
                    extracted_texts.append(str(text_val))
            elif isinstance(item, str):
                extracted_texts.append(item)

    return " ".join(extracted_texts)


def run_paddleocr_evaluation(
    gt_file="ground_truth.txt",
    image_dir="cropped_lines",
    output_csv="paddleocr_results.csv",
):
    if not os.path.exists(gt_file):
        print(f"원문 파일이 없습니다: {gt_file}")
        return

    with open(gt_file, "r", encoding="utf-8") as f:
        gt_lines = [line.strip() for line in f if line.strip()]

    from paddleocr import PaddleOCR

    print("PaddleOCR 모델 로딩 중 (한국어)...")
    ocr = PaddleOCR(
        use_textline_orientation=False,
        lang="korean",
        enable_mkldnn=False,
    )

    print(f"\nPaddleOCR 평가 시작 (총 {len(gt_lines)}개 줄, 정규화 기준 적용)")
    print("=" * 85)
    print(f"{'번호':^5} | {'이미지 파일':<15} | {'추론시간':^8} | {'일치율':^8} | {'상태':^6}")
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

        raw_res = ocr.ocr(img_path)
        ocr_result = extract_text_from_paddle_res(raw_res)

        infer_time = time.perf_counter() - start_t

        errors, acc = calculate_metrics(gt_text, ocr_result)

        total_acc += acc
        total_time += infer_time
        valid_count += 1

        status = "PERFECT" if errors == 0 else f"{errors}자 오차"
        print(f"[{idx:02d}]   | {img_name:<15} | {infer_time:.3f}초   | {acc:6.1f}%  | {status}")

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
        print(f"[PaddleOCR 최종 결과]")
        print(f"• 전체 검증 줄 수   : {valid_count} / {len(gt_lines)}")
        print(f"• 평균 글자 일치율  : {total_acc / valid_count:.2f}%")
        print(f"• 평균 장당 추론 속도: {total_time / valid_count:.3f}초")
        print(f"• 결과 저장 파일    : {os.path.abspath(output_csv)}")
    print("=" * 85)


if __name__ == "__main__":
    run_paddleocr_evaluation()