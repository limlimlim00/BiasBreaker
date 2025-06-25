from datetime import datetime
import os
import json

COUNTS_FILE = "/home/tag_counts.json"

def load_counts():
    if not os.path.exists(COUNTS_FILE):
        return {}
    with open(COUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_counts(counts):
    with open(COUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def week_str():
    dt = datetime.now()
    return f"{dt.year}-W{dt.isocalendar()[1]}"

def month_str():
    return datetime.now().strftime("%Y-%m")

def increment_tag_count(tag):
    counts = load_counts()
    if tag not in counts:
        counts[tag] = {"daily":{}, "weekly":{}, "monthly":{}}
    # 오늘/이번주/이번달 key
    d, w, m = today_str(), week_str(), month_str()
    counts[tag]["daily"][d] = counts[tag]["daily"].get(d, 0) + 1
    counts[tag]["weekly"][w] = counts[tag]["weekly"].get(w, 0) + 1
    counts[tag]["monthly"][m] = counts[tag]["monthly"].get(m, 0) + 1
    save_counts(counts)

if __name__ == "__main__":
    # 테스트용 태그명
    test_tag = "테스트 이슈"
    print(f"[+] '{test_tag}' 태그 카운트 1 증가!")
    increment_tag_count(test_tag)
    counts = load_counts()
    today = today_str()
    week = week_str()
    month = month_str()
    # 오늘/이번주/이번달 카운트 출력
    print("----[counts 최신 상태]----")
    print(f"오늘({today}) 카운트:", counts[test_tag]["daily"].get(today, 0))
    print(f"이번주({week}) 카운트:", counts[test_tag]["weekly"].get(week, 0))
    print(f"이번달({month}) 카운트:", counts[test_tag]["monthly"].get(month, 0))
    print("-------------------------")
    # 전체 counts 출력
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    