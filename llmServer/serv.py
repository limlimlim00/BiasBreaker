from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, json, uuid

from tag_generate import generate_tag_data
from tag_count import load_counts, increment_tag_count, today_str, week_str, month_str
from tag_embedding import get_tag_embedding, add_tag_embedding, find_similar_tags

app = FastAPI()

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "/home/tag_cache"
TAGS_FILE = "tags.json"
TAG_EMB_FILE = "tag_embeddings.json"
TASKS_DIR = "/home/tag_tasks"

class TagRequest(BaseModel):
    tag: str

# 태그 리스트 로드/저장 함수
def load_tags():
    if not os.path.exists(TAGS_FILE):
        return []
    with open(TAGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["tags"]

def save_tags(tags):
    with open(TAGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"tags": tags}, f, ensure_ascii=False, indent=2)

def get_task_path(task_id):
    return os.path.join(TASKS_DIR, f"{task_id}_summary.json")

#########################
# 1. 태그 조회 (캐시만 읽음)
@app.post("/summarize")
async def summarize(request: TagRequest):
    tag = request.tag
    tag_file = os.path.join(DATA_DIR, f"{tag}_summary.json")
    if os.path.exists(tag_file):
        with open(tag_file, "r", encoding="utf-8") as f:
            increment_tag_count(tag)
            return json.load(f)
    else:
        similar_tags = find_similar_tags(tag, topk=3)
        return {"not_found": True, "suggestions": similar_tags}

#########################
# 2. 태그 생성 작업 등록 (비동기)
@app.post("/create_tag_request")
async def create_tag_request(request: TagRequest, background_tasks: BackgroundTasks):
    tag = request.tag
    task_id = str(uuid.uuid4())

    # 태스크 상태 초기화
    with open(get_task_path(task_id), "w", encoding="utf-8") as f:
        json.dump({"status": "pending", "progress": 0, "tag": tag}, f)

    # 백그라운드 태그 생성 시작
    background_tasks.add_task(process_tag_creation, task_id, tag)
    return {"task_id": task_id}

#########################
# 3. 태그 생성 백그라운드 작업
def process_tag_creation(task_id, tag):
    task_path = get_task_path(task_id)
    tag_file = os.path.join(DATA_DIR, f"{tag}_summary.json")
    try:
        # (1) 상태: 시작
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump({"status": "processing", "progress": 20, "tag": tag}, f)

        # (2) generate_tag_data 호출 (오래 걸릴 수 있음)
        tag_data = generate_tag_data(tag)
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump({"status": "processing", "progress": 50, "tag": tag}, f)

        # (3) 결과 저장 (중요! _summary.json 파일)
        with open(tag_file, "w", encoding="utf-8") as f:
            json.dump(tag_data, f, ensure_ascii=False, indent=2)

        # (4) 임베딩 등 후처리
        emb = get_tag_embedding(tag)
        add_tag_embedding(tag, emb)
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump({"status": "processing", "progress": 80, "tag": tag}, f)

        # (5) 태그 목록 갱신
        tags = load_tags()
        if tag not in tags:
            tags.append(tag)
            save_tags(tags)

        # (6) 완료
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump({"status": "done", "progress": 100, "tag": tag, "message": f"'{tag}' 태그가 생성되었습니다."}, f)
    except Exception as e:
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump({"status": "error", "progress": 0, "tag": tag, "error": str(e)}, f)

#########################
# 4. 작업 상태 조회
@app.get("/create_tag_status")
async def create_tag_status(task_id: str):
    path = get_task_path(task_id)
    if not os.path.exists(path):
        return {"status": "not_found", "progress": 0}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

#########################
# 5. 인기 태그/전체 태그
@app.get("/popular_tags")
async def popular_tags(period: str = Query(..., regex="^(today|week|month)$"), limit: int = 10):
    counts = load_counts()
    key = {"today":"daily", "week":"weekly", "month":"monthly"}[period]
    now_key = {
        "today": today_str(),
        "week": week_str(),
        "month": month_str()
    }[period]

    result = []
    for tag, record in counts.items():
        cnt = record.get(key, {}).get(now_key, 0)
        if cnt > 0:
            result.append((tag, cnt))
    result.sort(key=lambda x: -x[1])  # 내림차순
    return {"tags": [tag for tag, cnt in result[:limit]]}

@app.get("/all_tags")
async def get_all_tags():
    tags = load_tags()
    return {"tags": tags}
