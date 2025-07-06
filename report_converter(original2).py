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

# 3. 의미 없는 링크 제거 (링크 텍스트가 "기사", "링크", "링크 바로가기" 등일 때 제거)
md_text = re.sub(r'\n?\[ *(?:기사|링크|링크 바로가기)? *\]\(https?://[^\s\)]+?\)', '', md_text, flags=re.IGNORECASE)

# 4. Markdown → HTML 변환
html_body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "autolink"])

# 5. 순수 URL을 하이퍼링크로 변환 (이미 앵커 태그가 아닌 경우만)
html_body = re.sub(r'(?<!href=")(https?://[^\s<]+)', r'<a href="\1" target="_blank">\1</a>', html_body)

# 6. HTML 템플릿 구성
html_template = f"""
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
        line-height: 1.75;
        padding: 40px;
        color: #222;
        background-color: #fff;
    }}
    h1 {{
        font-size: 24px;
        border-bottom: 3px solid #444;
        padding-bottom: 10px;
    }}
    h2 {{
        font-size: 20px;
        margin-top: 40px;
        color: #003366;
    }}
    h3 {{
        font-size: 18px;
        margin-top: 30px;
        color: #444;
    }}
    p, li {{
        font-size: 15px;
    }}
    a {{
        color: #0066cc;
        text-decoration: underline;
    }}
    hr {{
        border: none;
        border-top: 1px dashed #aaa;
        margin: 30px 0;
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

# 8. HTML → PDF 변환 옵션
options = {
    "enable-local-file-access": "",
    "disable-external-links": "",
    "no-images": "",
    "disable-javascript": "",
    "quiet": ""
}

# 9. PDF 생성
pdfkit.from_file(html_file, pdf_file, configuration=pdf_config, options=options)

print(f"\n✅ 변환 완료!\n📄 HTML 파일: {html_file}\n📄 PDF 파일: {pdf_file}")
