from kobert_transformers import get_tokenizer, get_kobert_model
import torch
import json
import numpy as np

TAG_EMB_FILE = "tag_embeddings.json"

tokenizer = get_tokenizer()  # KoBERT용
model = get_kobert_model()   # transformers.BertModel과 인터페이스 동일

def get_tag_embedding(text: str):
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    emb = outputs.pooler_output.squeeze(0).cpu().numpy()
    return emb  # numpy array

def add_tag_embedding(tag, emb, json_path=TAG_EMB_FILE):
    # 로드
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[tag] = emb.tolist()
    # 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_similar_tags(query_tag, topk=5, json_path=TAG_EMB_FILE):
    with open(json_path, "r", encoding="utf-8") as f:
        tag_emb_dict = json.load(f)
    tags = list(tag_emb_dict.keys())
    result = []

    # 1. 완전일치
    if query_tag in tags:
        result.append(query_tag)
    # 2. 부분문자열 일치
    partial = [t for t in tags if query_tag in t or t in query_tag and t != query_tag]
    for t in partial:
        if t not in result:
            result.append(t)
    # 3. 단어 단위 겹침 (토큰)
    query_tokens = set(query_tag.split())
    for t in tags:
        t_tokens = set(t.split())
        if len(query_tokens & t_tokens) > 0 and t not in result:
            result.append(t)
    # 4. 코사인 유사도 (중복 없이)
    emb_matrix = np.array([tag_emb_dict[t] for t in tags])
    query_emb = get_tag_embedding(query_tag)
    query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-10)
    emb_matrix_norm = emb_matrix / (np.linalg.norm(emb_matrix, axis=1, keepdims=True) + 1e-10)
    sims = np.dot(emb_matrix_norm, query_emb)
    top_idx = sims.argsort()[::-1]
    for idx in top_idx:
        t = tags[idx]
        if t not in result and t != query_tag:
            result.append(t)
        if len(result) >= topk:
            break
    return result[:topk]
        
if __name__ == "__main__":
    tags = [
    "검찰청 폐지",
    "기초연금 인상",
    "낙태 전면 합법화",
    "대입 정시 확대",
    "동성혼 합법화",
    "방위비 분담금 인상",
    "병사 월급 200만 원",
    "사형제 폐지",
    "의대 정원 확대",
    "이재명 재판 중지",
    "주 4일제 근무 도입",
    "청년 기본소득 지급",
    "탈원전 정책",
    "포괄적 차별금지법 제정"
    ]

    for tag in tags:
        emb = get_tag_embedding(tag)
        add_tag_embedding(tag, emb)
        print(f"'{tag}' 임베딩이 tag_embeddings.json에 저장되었습니다.")    
