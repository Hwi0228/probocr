import os
import cv2

def crop_text_lines(image_path, output_dir="cropped_lines"):
    # 1. 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"이미지를 찾을 수 없습니다: {image_path}")
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. 이진화 (흑백 전환) 및 반전
    # 글자를 흰색(255), 배경을 검은색(0)으로 만듭니다.
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. 가로 방향 팽창(Dilation) 연산
    # 같은 줄에 있는 글자들을 가로로 연결하여 하나의 커다란 띠로 만듭니다.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 4. 윤곽선(Contour) 탐지
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # Y축 좌표(위에서 아래 순서) 기준으로 윤곽선 정렬
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[1])  # y 좌표 기준 정렬

    cropped_files = []
    saved_count = 0

    for i, (x, y, w, h) in enumerate(bounding_boxes):
        # 너무 작은 잡음(노이즈) 선은 무시 (높이 10px, 너비 20px 미만)
        if h < 10 or w < 20:
            continue

        # 약간의 여백(Padding) 추가
        pad = 4
        img_h, img_w = image.shape[:2]
        y1 = max(0, y - pad)
        y2 = min(img_h, y + h + pad)
        x1 = max(0, x - pad)
        x2 = min(img_w, x + w + pad)

        # 이미지 크롭
        crop = image[y1:y2, x1:x2]

        # 저장
        save_path = os.path.join(output_dir, f"line_{saved_count + 1:02d}.png")
        cv2.imwrite(save_path, crop)
        cropped_files.append(save_path)
        saved_count += 1

    print(f"총 {saved_count}개의 텍스트 줄 이미지가 '{output_dir}' 폴더에 저장되었습니다.")
    return cropped_files


if __name__ == "__main__":
    # 테스트할 시험지 전체 이미지 경로
    test_image = "test\\exam_paper.png"

    cropped_paths = crop_text_lines(test_image)

    # 첫 번째 잘린 이미지를 TrOCR 테스트용 파일로 복사
    if cropped_paths:
        print(f"TrOCR 테스트용으로 첫 번째 줄({cropped_paths[0]})을 'crop_text_line.png'로 사용할 수 있습니다.")