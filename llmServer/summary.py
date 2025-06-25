import json
import re
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from newspaper import Article

# 1. LLM 직접 호출 함수
def ask_llm_content(model, tokenizer, query, content, instruction, max_new_tokens):
    prompt = f"""
문제 쟁점: "{query}"

기사 내용:
\"\"\"
{content}
\"\"\"

{instruction}
"""
    # 토크나이즈 및 생성
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            do_sample=True,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if result.startswith(prompt):
        return result[len(prompt):].strip()
    return result.strip()

def ask_llm_pick(model, tokenizer, query, content, instruction, max_new_tokens):
    prompt = f"""
문제 쟁점: "{query}"

문장 모음:
\"\"\"
{content}
\"\"\"

{instruction}
"""
    # 토크나이즈 및 생성
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            do_sample=True,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if result.startswith(prompt):
        return result[len(prompt):].strip()
    return result.strip()

# 2. 기사 본문 크롤링
def get_article_text(url):
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        text = article.text.strip()[:8192]
        if not text or len(text) < 50:
            raise ValueError("본문 없음 또는 너무 짧음")
        return text
    except Exception as e:
        print(f"[newspaper3k 본문 크롤링 실패] {url} -> {e}")
        return ""

# 3. 한 기사에서 찬성/반대 문장 추출
def extract_support_oppose(model, tokenizer, query, article):
    content = get_article_text(article["url"])
    if not content or len(content) < 50:
        return {"support": [], "oppose": []}

    instruction = (
        f"기사 내용 중 '{query}' 에 대해 찬성(긍정) 또는 반대(부정) 입장을 나타내는 문장이 있다면, "
        "각각 최대 1개씩만 반드시 아래 형식으로 인용해. \n"
        "출력 형식 예시:\n"
        "[찬성]\n- 찬성 논거는 이러하다.\n"
        "\n[반대]\n- 반대 논거는 저러하다.\n\n"
        "반드시 위 예시 형식대로, [찬성] 한 줄, [반대] 한 줄만 반환. "
        "찬성 또는 반대가 기사 내에 없으면 해당 부분은 [찬성] 또는 [반대] 아래에 아무 문장도 쓰지 말 것. "
        "해당 형식 외에는 절대 아무런 설명도 추가하지 말 것."
    )
    response = ask_llm_content(model, tokenizer, query, content, instruction, max_new_tokens=128)
    # print(response)
    # print()
    # 파싱: 첫 번째 항목만 추출하도록 변경
    support_match = re.search(r"\[찬성\][^\n\r]*\n-\s*(.+?)(?=\n|\Z)", response, flags=re.MULTILINE)
    oppose_match  = re.search(r"\[반대\][^\n\r]*\n-\s*(.+?)(?=\n|\Z)", response, flags=re.MULTILINE)

    def clean(text):
        if not text:
            return ""
        # /추가 설명, [태그] 등 의미 없는 부분 잘라냄
        text = text.split("[/")[0].strip()
        text = re.sub(r"\[/?[^\]]+\]", "", text)
        return text.strip()

    support = [clean(support_match.group(1))] if support_match and clean(support_match.group(1)) else []
    oppose  = [clean(oppose_match.group(1))] if oppose_match and clean(oppose_match.group(1)) else []
    
    return {
        "support": support,
        "oppose": oppose
    }

# 4. 전체 기사별 stance 문장과 출처 수집
def collect_stance_sentences(news_items, query, model, tokenizer):
    support_items = []
    oppose_items = []

    for art in tqdm(news_items):
        stance = extract_support_oppose(model, tokenizer, query, art)
        for s in stance["support"]:
            support_items.append({
                "sentence": s,
                "press": art.get("press"),
                "title": art.get("title"),
                "url": art.get("url"),
                "id": art.get("id")
            })
        for o in stance["oppose"]:
            oppose_items.append({
                "sentence": o,
                "press": art.get("press"),
                "title": art.get("title"),
                "url": art.get("url"),
                "id": art.get("id")
            })
    # print(support_items)
    # print()
    # print(oppose_items)
    # print()
    return support_items, oppose_items

# 5. 각 stance group 별 top_k 추출
def select_top_stance_sentences(model, tokenizer, stance_items, stance_label, query, top_k=3):
    """
    stance_items: support_items 또는 oppose_items 리스트
    stance_label: '찬성' 또는 '반대'
    query: 쟁점
    top_k: 추출할 문장 개수
    """
    # 1. 입력 데이터가 너무 적으면 전체 반환
    if len(stance_items) <= top_k:
        return stance_items

    # 2. 관련성/명확성 기반 상위 top_k개 선정 (LLM 활용)
    text_blocks = [
    f"- (ID: {item['id']}) 문장: {item['sentence']}"
    for item in stance_items
    ]
    input_text = "\n".join(text_blocks)
    instruction = (
        f"'문장 모음'은 '{query}' 쟁점에 대해 '{stance_label}'하는 기사들의 ID와 문장이야.\n"
        f"이 중에서 '{query}'와 가장 관련성이 높고 '{stance_label}' 입장이 명확하게 드러난다고 생각되는 문장을 {top_k}개 골라서 각 문장의 ID만 쉼표로 구분해서 반환해줘.\n"
        "반드시 ID만, 쉼표로 구분해서 한 줄로만 출력해.\n"
    )
    # LLM에 선정 작업을 맡김
    selected_text = ask_llm_pick(model, tokenizer, query, input_text, instruction, max_new_tokens=16)
    # print(selected_text)
    # print()

    # id 추출
    import re
    selected_ids = [int(x) for x in re.findall(r"\d+", selected_text)]
    # print(selected_ids)

    filtered_items = [item for item in stance_items if item.get('id') in selected_ids]

    # 개수 보정
    filtered_items = filtered_items[:top_k]
    if len(filtered_items) < top_k:
        remain = [item for item in stance_items if item.get('id') not in selected_ids]
        filtered_items += remain[:top_k - len(filtered_items)]
    # print (filtered_items)
    # print()
    return filtered_items

# 6. 공통 주장 요약
def extract_facts_from_article(model, tokenizer, item, label, query, max_facts=5):
    """
    각 기사별로 fact만 bullet point로 추출 (id는 item['id']에서 직접 지정)
    """
    # 본문 길이 제한 (예: 500자)
    content = get_article_text(item["url"])
    block = f"{item['press']} / {item['title']}\n{content}"

    instruction = (
        f"위 기사 내용은 '{query}' 이슈에 대한 기사야.\n"
        f"이 기사에서 '{query}'와 관련된, 명확히 진술된 사실(fact) {max_facts}개만 bullet point로 추출해줘. "
        "의견/주장/추론은 제외하고, 객관적인 사실만 뽑아줘. 각 bullet에는 fact만 써줘."
        "bullet point 기호는 '-'로 통일."
    )

    response = ask_llm_content(
        model, tokenizer, query, block, instruction, max_new_tokens=256
    )
    # print(response)
    # print()
    facts = []
    for line in response.strip().split("\n"):
        # bullet point만 추출
        m = re.match(r"[-•*]\s*(.+)", line.strip())
        if m:
            fact = m.group(1).strip()
            if fact:
                facts.append({"fact": fact, "id": item["id"]})
        if len(facts) >= max_facts:
            break
    # print(facts)
    # print()
    return facts

def collect_all_facts(model, tokenizer, items, label, query, max_facts=5):
    all_facts = []
    for item in items:
        facts = extract_facts_from_article(model, tokenizer, item, label, query, max_facts=max_facts)
        all_facts.extend(facts)
        import gc
        gc.collect()
        torch.cuda.empty_cache()
    # print(all_facts)
    # print()
    return all_facts

def extract_common_facts(model, tokenizer, support_items, oppose_items, query, top_k=3):
    # 각 진영에서 fact 추출
    support_facts = collect_all_facts(model, tokenizer, support_items, "찬성", query)
    oppose_facts  = collect_all_facts(model, tokenizer, oppose_items, "반대", query)

    # 팩트 전체 리스트를 하나로 합치고, 기사 id까지 표기
    text_blocks = []
    for f in support_facts:
        text_blocks.append(f"- (ID: {f['id']}, 진영: 찬성) {f['fact']}")
    for f in oppose_facts:
        text_blocks.append(f"- (ID: {f['id']}, 진영: 반대) {f['fact']}")
    all_facts_text = "\n".join(text_blocks)

    instruction = (
        f"'문장 모음'은 '{query}' 이슈에 대해 찬성/반대 진영 기사 각각에서 추출한 팩트와 해당 기사 id다.\n"
        f"이 중 '{query}'와 관련된 핵심 내용 중, 찬성과 반대 양쪽 기사에서 모두 언급되는 사실(fact) {top_k}개를 골라 bullet point로 추출하라.\n"
        "각 팩트별로 해당하는 찬성 기사 id와 반대 기사 id를 함께 써야 한다.\n"
        "모든 bullet point는 반드시 '-'로 시작한다.\n"
        "존댓말(높임말), '~요', '~습니다' 등의 표현, 의문문, 감탄문, 명령문, 대화체 등은 절대 사용하지 않는다.\n"
        "각 문장은 '~다'로 끝나는 평서문(서술문) 형태로만 작성한다.\n"
        "의견, 주장, 추론, 해석 없이, 기사에 객관적으로 명시된 사실(fact)만 골라야 한다.\n"
        "출력 형식 예시:\n"
        "- 해당 법안은 2025년 6월 5일에 더불어민주당에서 발의했다. (찬성: ID: 1; 반대: ID: 2)"
    )

    response = ask_llm_content(model, tokenizer, query, all_facts_text, instruction, max_new_tokens=256)
    # print(response)
    # print()

    # 후처리: 정규표현식으로 fact/ID 추출
    pattern = r"- (.+?) \(찬성: ID: ([\d, ]+); 반대: ID: ([\d, ]+)\)"
    fact_items = []
    for match in re.finditer(pattern, response):
        fact = match.group(1).strip()
        # 각 ID 그룹에서 첫 번째 id만 추출 (있으면)
        s_id_list = re.findall(r"\d+", match.group(2))
        o_id_list = re.findall(r"\d+", match.group(3))
        s_id = int(s_id_list[0]) if s_id_list else None
        o_id = int(o_id_list[0]) if o_id_list else None
        fact_items.append({
            "fact": fact,
            "support_id": s_id,
            "oppose_id": o_id
        })
        if len(fact_items) >= top_k:
            break

    # print(fact_items)
    return fact_items

# 7. 전체 파이프라인
def analyze_news_articles_by_query(input_json, output_json, base_query, model, tokenizer):
    # 1. 기사 로드
    with open(input_json, "r", encoding="utf-8") as f:
        news_items = json.load(f)
    print(f"{len(news_items)}개 기사에 대해 LLM 분석 시작…")

    # 2. 기사별 stance 문장 추출
    support_items, oppose_items = collect_stance_sentences(news_items, base_query, model, tokenizer)

    # 3. 각 stance별 대표 3개씩만 추출
    top_support_items = select_top_stance_sentences(model, tokenizer, support_items, "찬성", base_query)
    top_oppose_items  = select_top_stance_sentences(model, tokenizer, oppose_items, "반대", base_query)
    
    # 4. 공통 fact 추출
    common_facts = extract_common_facts(model, tokenizer, top_support_items, top_oppose_items, base_query)

    result = {
        "common_facts": common_facts,
        "top_support_items": top_support_items,
        "top_oppose_items": top_oppose_items
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"완료! 결과는 {output_json}에 저장됨.")
    return result

# --- 실행 예시 ---
if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained("AIDX-ktds/ktdsbaseLM-v0.14-onbased-llama3.1")
    model = AutoModelForCausalLM.from_pretrained("AIDX-ktds/ktdsbaseLM-v0.14-onbased-llama3.1").to(
        torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    base_query = "검찰청 폐지"  # 예시 쟁점

    input_json = f"/home/tag_cache/{base_query}_crawling.json"
    output_json = f"/home/tag_cache/{base_query}_summary.json"

    analyze_news_articles_by_query(
        input_json=input_json,
        output_json=output_json,
        base_query=base_query,
        model=model,
        tokenizer=tokenizer,
    )
