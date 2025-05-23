from openai import OpenAI
import feedparser
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# 1. 환경변수 로드 및 OpenAI 클라이언트 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. 키워드 기반 필터링 설정 (2차 필터로만 사용)
keywords = [
    "정책", "공모", "지원", "사업", "예산", "계획",
    "청년", "산업", "R&D", "소상공인", "청년정책", "일자리", "기업",
    "산업단지", "AI", "중소기업", "발표", "공개", "산단",
    "부산", "지자체", "지역", "행사", "포럼", "설명회",
    "박람회", "세미나", "간담회", "사회적경제",
    "복지", "주거", "돌봄", "의료", "탄소중립", "ESG",
    "박형준", "시장", "기회", "미래", "혁신"
]

# 3. rss_sources.json 파일에서 RSS 목록 불러오기
with open("rss_sources.json", "r", encoding="utf-8") as f:
    rss_data = json.load(f)

rss_urls_by_group = rss_data

# 4. 그룹별 요약 결과 저장용 딕셔너리 초기화
summaries_by_group = {
    "부산광역시": [],
    "중앙정부": [],
    "공공기관/기타": []
}

# 5. 모델 설정
MODEL_NAME = "gpt-3.5-turbo"  # 또는 "gpt-4"

# 5-1. 모델에 따른 요약 범위 자동 설정
if MODEL_NAME == "gpt-4":
    MAX_ENTRIES = 12
    MAX_SNIPPET_CHARS = 600
else:
    MAX_ENTRIES = 6
    MAX_SNIPPET_CHARS = 300

# 6. 각 그룹별 RSS URL 처리
for group, urls in rss_urls_by_group.items():
    for rss_url in urls:
        feed = feedparser.parse(rss_url)
        entries = feed.entries[:MAX_ENTRIES]

        article_snippets = []
        for i, entry in enumerate(entries):
            title = entry.title.strip()
            summary = (entry.get("summary", "") or entry.get("description", "")).strip()
            snippet = summary if len(summary) < MAX_SNIPPET_CHARS else summary[:MAX_SNIPPET_CHARS] + "..."
            article_snippets.append(f"{i+1}. 제목: {title}\n요약: {snippet}")

        article_block = "\n\n".join(article_snippets)

        select_prompt = f"""
다음은 최근 뉴스 기사들의 제목과 간단한 요약입니다. 이 중 정책적 가치가 있거나 요약할 만한 의미가 있는 기사 번호만 골라줘.
형식: [1, 3, 5] ← 숫자 리스트 형태로 반환해줘.

기사 목록:
{article_block}
"""

        try:
            selection_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 정책조정팀의 어시스턴트야. 중요한 정책 기사만 추려야 해."},
                    {"role": "user", "content": select_prompt}
                ],
                temperature=0.2,
            )
            raw_content = selection_response.choices[0].message.content.strip()
            if not raw_content.startswith("[") or not raw_content.endswith("]"):
                raise ValueError(f"GPT 반환 오류: {raw_content}")
            selected_indices = eval(raw_content)

        except Exception as e:
            group = "공공기관/기타" if group == "산하기관" else group
            summaries_by_group.setdefault(group, []).append(f"❗ 기사 선택 실패: {e}\n\n")
            continue

        for idx in selected_indices:
            try:
                entry = entries[int(idx)-1]
                title = entry.title.strip()
                summary = (entry.get("summary", "") or entry.get("description", "")).strip()
                link = entry.link
                full_text = f"{title}\n{summary}"

                if not any(keyword in full_text for keyword in keywords):
                    continue

                prompt = f"""
다음 뉴스 기사 내용을 기반으로 정책 관련 정보를 요약해줘.

※ 기사 간 내용이 비슷할 경우, 중복 요약을 피하고 가장 정보가 구체적이고 유용한 기사만 선택해 요약해줘.
※ 같은 주제를 다룬 여러 기사는 생략하거나 간략히 언급해도 괜찮아.

제목: {title}

내용: {summary}

### ✨ 기사 유형
(정책공고 / 공모전 / 설명회 / 통계동향 / 인터뷰 / 일반보도 / 기타 중 판단)

### 📌 핵심 요약 (2~3줄)

### 📋 주요 내용
(지원 대상, 조건, 주요 발표, 정책 변화 등 핵심 내용 중심)

### 📅 일정 정보
(공고일, 접수 기간, 행사일 등 가능하면 명시)

### 🏢 발신기관 또는 주최기관
※ 기사 안에 명확히 명시된 경우만 기재.
※ "문의처"(전화번호, 이메일 등)가 있다면 기사에 명시된 경우만 작성. 없으면 생략.
※ 기사에 등장하지 않는 기관명(예: 부산경제진흥원)은 절대 임의로 넣지 말 것.


※ Markdown 형식으로 작성.
※ 정보가 불충분하면 해당 항목은 생략해도 되고, 임의 추론은 하지 말 것.
"""

                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "너는 부산경제진흥원 정책조정팀의 스마트 요약 어시스턴트야."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                summaries_by_group.setdefault(group, []).append(
                    f"### 🎯 {title}\n🔗 {link}\n\n" + response.choices[0].message.content + "\n\n---\n"
                )

            except Exception as e:
                group = "공공기관/기타" if group == "산하기관" else group
                summaries_by_group.setdefault(group, []).append(f"❗ [{title}] 오류 발생: {e}\n\n")

# 7. Markdown 파일로 저장
today = datetime.now()
date_title = today.strftime("%Y.%m.%d")
output_file = f"policy_report_{today.strftime('%Y-%m-%d')}.md"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# 🗂️ 부산경제진흥원 정책조정팀 정책 리포트\n")
    f.write(f"**기준일자: {date_title} ({today.strftime('%A')})**\n\n")
    f.write("---\n\n")

    if summaries_by_group["부산광역시"]:
        f.write("## 1. 부산광역시 관련 기사\n\n")
        f.writelines(summaries_by_group["부산광역시"])

    if summaries_by_group["중앙정부"]:
        f.write("## 2. 중앙부처 관련 기사\n\n")
        f.writelines(summaries_by_group["중앙정부"])

    if summaries_by_group["공공기관/기타"]:
        f.write("## 3. 공공기관 및 기타 기사\n\n")
        f.writelines(summaries_by_group["공공기관/기타"])

    f.write("---\n")
    total_count = sum(len(v) for v in summaries_by_group.values())
    f.write(f"\n총 요약 기사 수: {total_count}\n")

print(f"✅ 요약 완료! 보고서가 저장되었습니다 → {output_file}")
print(f"📎 보고서를 PDF로 변환하려면 'report_converter.py' 파일을 실행하세요.")
