from crawler import crawl_query_list
from summary import analyze_news_articles_by_query
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def generate_tag_data(tag):
    """
    태그가 들어오면 관련 기사 크롤링, 요약, fact 추출 등 전체 데이터 파이프라인 실행.
    결과를 dict로 반환하며, 크롤링/요약 결과 모두 파일로 저장.
    """
    import json

    # 1. 관련 뉴스 기사 크롤링
    news_items = crawl_query_list(tag)
    crawling_path = f"/home/tag_cache/{tag}_crawling.json"
    with open(crawling_path, "w", encoding="utf-8") as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)

    # 2. 크롤링 결과 파일을 summary.py에 그대로 넘겨 사용 (임시파일 대신 고정 경로)
    input_json = crawling_path
    output_json = f"/home/tag_cache/{tag}_summary.json"

    # 3. 모델 및 토크나이저 로드 (한 번만 로딩하게 개선 필요)
    model_name = "AIDX-ktds/ktdsbaseLM-v0.14-onbased-llama3.1"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    # 4. 요약 및 fact 추출 (summary.py 파이프라인 사용)
    result = analyze_news_articles_by_query(
        input_json=input_json,
        output_json=output_json,
        base_query=tag,
        model=model,
        tokenizer=tokenizer,
    )
    # result는 dict임, output_json 파일에도 저장됨

    return result

if __name__ == "__main__":
    issue_tags = [
        "의대 정원 확대",
        "주 4일제 근무",
        "병사 월급 200",
        "동성혼 합법화",
        "낙태 전면 합법화",
        "사형제 폐지",
        "탈원전 정책",
        "포괄적 차별금지법",
        "기초연금 인상",
        "청년 기본소득",
        "검찰청 폐지",
        "이재명 재판",
        "고교학점제",
        "학원 일요휴무제",
        "부동산 보유세 강화",
        "부동산 임대차 3법",
        "정시 확대",
        "여성징병제",
        "일본 오염수 방류",
        "청년 주택 정책",
        "공기업 민영화",
        "외국인 노동자 확대",
        "교원평가제 폐지",
        "노란봉투법"
    ]

    for tag in issue_tags:
        tag_data = generate_tag_data(tag)
        print(f"=== {tag} ===")
        print(tag_data)
        print()
