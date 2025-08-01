import markdown2
import pdfkit
import os
from datetime import datetime
import re

# 0. wkhtmltopdf 경로 설정
pdf_config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

# 1. 파일 경로 설정
today = datetime.now().strftime("%Y-%m-%d")
md_file = f"policy_report_{today}.md"
html_file = f"output/policy_report_{today}.html"
pdf_file = f"output/policy_report_{today}.pdf"

# 2. Markdown 파일 확인
if not os.path.exists(md_file):
    print(f"❌ {md_file} 파일이 없습니다. 우선 요약을 먼저 실행해주세요.")
    exit()

with open(md_file, "r", encoding="utf-8") as f:
    md_text = f.read()

# 3. 의미 없는 링크 제거
md_text = re.sub(r'\n?\[ *(?:기사|링크|링크 바로가기)? *\]\(https?://[^\s\)]+?\)', '', md_text, flags=re.IGNORECASE)

# 4. Markdown → HTML 변환
html_body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "autolink"])

# 5. 순수 URL을 하이퍼링크로 변환 (이미 앵커 태그가 아닌 경우만)
html_body = re.sub(r'(?<!href=")(https?://[^\s<]+)', r'<a href="\1" target="_blank">\1</a>', html_body)

# 6. 개선된 HTML 템플릿 구성 (가독성 대폭 향상)
html_template = f"""
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
        line-height: 1.8;
        padding: 50px;
        color: #333;
        background-color: #fdfdfd;
    }}
    h1 {{
        font-size: 28px;
        border-bottom: 4px solid #004080;
        padding-bottom: 12px;
        color: #004080;
    }}
    h2 {{
        font-size: 22px;
        margin-top: 40px;
        border-left: 6px solid #007acc;
        padding-left: 10px;
        color: #007acc;
    }}
    h3 {{
        font-size: 20px;
        margin-top: 25px;
        color: #333;
    }}
    ul {{
        margin-left: 20px;
        padding-left: 0;
    }}
    p, li {{
        font-size: 16px;
    }}
    a {{
        color: #0055cc;
        text-decoration: underline;
    }}
    hr {{
        border: none;
        border-top: 1px dashed #aaa;
        margin: 40px 0;
    }}
    .article {{
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 25px;
        background-color: #fff;
        box-shadow: 2px 2px 6px #ccc;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

# 7. HTML 저장
os.makedirs("output", exist_ok=True)
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_template)

# 8. HTML → PDF 변환 옵션 (가독성 및 여백 향상)
options = {
    "enable-local-file-access": "",
    "encoding": "UTF-8",
    "page-size": "A4",
    "margin-top": "15mm",
    "margin-right": "15mm",
    "margin-bottom": "15mm",
    "margin-left": "15mm",
    "zoom": "1.1",
    "quiet": ""
}

# 9. PDF 생성
pdfkit.from_file(html_file, pdf_file, configuration=pdf_config, options=options)

print(f"\n✅ 변환 완료!\n📄 HTML 파일: {html_file}\n📄 PDF 파일: {pdf_file}")
