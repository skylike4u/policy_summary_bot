from openai import OpenAI
import feedparser
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime

# 환경변수 로드 및 OpenAI 클라이언트 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 키워드 설정
keywords = [
    "정책", "공모", "지원", "사업", "예산", "계획", "핵심", "강조", "중점",
    "청년", "산업", "R&D", "소상공인", "청년정책", "일자리", "기업", "수출",
    "산업단지", "AI", "중소기업", "발표", "공개", "산단",
    "부산", "지자체", "행사", "설명회", "조성",
    "전시회", "세미나", "간담회", "사회적경제", "로컬", "골목", "조성", "이전",
    "복지", "주거", "의료관광", "이재명",
    "박형준", "시장", "기회", "미래", "혁신", "위기", "재난"
]

# RSS 목록 불러오기
with open("rss_sources.json", "r", encoding="utf-8") as f:
    rss_data = json.load(f)

rss_urls_by_group = rss_data
summaries_by_group = {"부산광역시": [], "중앙정부": [], "공공기관/기타": []}
errors = []

# 모델 설정
MODEL_NAME = "gpt-3.5-turbo"  # 필요 시, gpt-4 선택

for group, urls in rss_urls_by_group.items():
    # 🔖 변경사항② : 부산광역시의 기사수(MAX_ENTRIES)를 상향 조정
    if group == "부산광역시":
        MAX_ENTRIES = 30  # 당초 25에서 상향향
    else:
        MAX_ENTRIES = 15 if MODEL_NAME == "gpt-4" else 12  # 당초 10에서 상향

    MAX_SNIPPET_CHARS = 600 if MODEL_NAME == "gpt-4" else 400  # 당초 500에서 상향

    for rss_url in urls:
        feed = feedparser.parse(rss_url)
        entries = feed.entries[:MAX_ENTRIES]

        if not entries:
            errors.append(f"[{group}] RSS 피드가 비어 있음: {rss_url}")
            continue

        article_snippets = [
            f"{i+1}. 제목: {entry.title.strip()}\n요약: {entry.get('summary', '')[:MAX_SNIPPET_CHARS]}"
            for i, entry in enumerate(entries)
        ]

        article_block = "\n\n".join(article_snippets)

        select_prompt = f"""
다음은 {group}의 최근 뉴스 기사입니다. 정책적으로 가치가 높고 중복되지 않는 의미 있는 기사 번호만 골라줘.
특히 **{group} 기사 중 의미 있는 정책 기사 선별에 집중해줘.**

※ 부산광역시의 경우, 다음의 정책목표에 부합하는 기사를 우선 선별:
지역경제 활성화, 일자리 창출, 청년 지원, 소상공인 지원, 혁신기술(AI, ESG, 스마트시티 등), 수출지원

형식: [1, 3, 5] ← 숫자 리스트 형태로만 반환해줘

기사 목록:
{article_block}
"""

        try:
            selection_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 중요한 정책 기사만 선별하는 어시스턴트야."},
                    {"role": "user", "content": select_prompt}
                ],
                temperature=0.2,
            )
            raw_content = selection_response.choices[0].message.content.strip()
            match = re.search(r"\[(.*?)\]", raw_content)
            if not match:
                raise ValueError(f"GPT 응답 파싱 실패: {raw_content}")
            selected_indices = [int(i.strip()) for i in match.group(1).split(",")]

        except Exception as e:
            errors.append(f"[{group}] 기사 선별 실패: {e}")
            continue

        for idx in selected_indices:
            try:
                entry = entries[int(idx)-1]
                title = entry.title.strip()
                summary = entry.get("summary", "")
                link = entry.link

                if not any(kw in f"{title} {summary}" for kw in keywords):
                    continue

                detailed_prompt = f"""
다음 뉴스 기사를 간결하고 명료하게 정책적 관점에서 요약해줘.

※ 목적: 부산광역시 및 중앙부처 등 기관의 의미 있는 정책 정보를 수집하여 부산시 정책 발전에 활용하려 함.
※ 반드시 기사에 있는 정보만 사용할 것. 없거나 불확실한 항목은 생략할 것.

제목: {title}
내용: {summary}

아래 형식대로 Markdown으로 작성해줘:

### ■ 기사 유형
(정책공고 / 공모전 / 설명회 / 통계동향 / 인터뷰 / 일반보도 / 기타 중 가장 적합한 것만 작성)

### ■ 핵심 요약
(2~3줄로 간결히 핵심을 작성할 것)

### ■ 주요 내용
(지원 대상, 조건, 주요 발표, 정책 변화 등 중요한 정보가 있을 경우 명확히 기재. 없으면 생략.)

### ■ 일정 정보
(공고일, 접수기간, 행사일 등 날짜가 명확히 있는 경우만 작성. 없으면 항목 자체를 생략.)

### ■ 발신기관 또는 주최기관
(기사에서 명확히 기관명이 언급된 경우만 작성. 불확실하거나 없는 경우 항목을 생략.)

※ 전화번호, 이메일 등 연락처는 명확히 명시된 경우만 작성. 없으면 생략.
※ 항목 중, "일정 정보" 및 "발신기관 또는 주최기관"이 없는 경우는 해당 항목 자체를 생략할 것.
※ 절대로 추론하여 정보를 추가하지 말고, 빈 항목을 "없음"으로 표기하지 말고 생략할 것.
※ 기사에 존재하지 않는 기관명을 절대 추론하여 작성하지 말 것 (예: '부산광역시', '부산경제진흥원' 등).
"""


                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "너는 부산경제진흥원 정책조정팀의 스마트 어시스턴트야."},
                        {"role": "user", "content": detailed_prompt}
                    ],
                    temperature=0.3,
                )

                summaries_by_group[group].append(
                    f"### 🎯 {title}\n🔗 {link}\n\n{response.choices[0].message.content}\n\n---\n"
                )

            except Exception as e:
                errors.append(f"[{group}] {title} 요약 실패: {e}")

# Markdown 파일 저장
today = datetime.now()
date_title = today.strftime("%Y.%m.%d")
output_file = f"policy_report_{today.strftime('%Y-%m-%d')}.md"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# 🗂️ 부산경제진흥원 정책조정팀 정책기사 리포트\n")
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

if errors:
    print("\n⚠️ 오류 목록:")
    for err in errors:
        print("-", err)