# ProbOCR

스캔한 문제 이미지를 입력하면 OCR해서 한글 파일, LaTeX, Typst 중 하나로 제공하는 서비스입니다.

## 문제 DB

Flask 앱을 실행한 다음 사이드바의 **문제 DB 등록**을 눌러 문제를 입력할 수 있습니다. 등록된 문제는 SQLite의 `instance/probocr.sqlite3`에 저장되며, 문제 DB 화면에는 저장된 문제와 실제 문항 수만 표시됩니다. SQLite 파일은 Git에 포함되지 않습니다.

```powershell
python -m pip install -r requirements.txt
python app.py
```
