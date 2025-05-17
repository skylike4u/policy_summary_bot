import markdown2
import pdfkit
import os
from datetime import datetime

# 0. wkhtmltopdf 경로 설정
pdf_config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

# 1. 파일 경로 설정
today = datetime.now().strftime("%Y-%m-%d")
md_file = f"policy_report_{today}.md"
html_file = f"output/policy_report_{today}.html"
pdf_file = f"output/policy_report_{today}.pdf"

# 2. Markdown → HTML 변환
if not os.path.exists(md_file):
    print(f"❌ {md_file} 파일이 없습니다. 우선 요약을 먼저 실행해주세요.")
    exit()

with open(md_file, "r", encoding="utf-8") as f:
    md_text = f.read()

# 자동 링크 처리: autolink 사용
html_body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "autolink"])

# 링크 텍스트를 클릭 가능한 앵커로 변환
import re
html_body = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank">\1</a>', html_body)

# HTML 템플릿 정의
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

# 3. HTML 저장
os.makedirs("output", exist_ok=True)
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_template)

# 4. HTML → PDF 변환
pdfkit.from_file(html_file, pdf_file, configuration=pdf_config)

print(f"\n✅ 변환 완료!\n📄 HTML 파일: {html_file}\n📄 PDF 파일: {pdf_file}")
