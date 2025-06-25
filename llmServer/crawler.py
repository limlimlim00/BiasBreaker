import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
import time
import json

DOMAIN2PRESS = {
    "khan.co.kr": "경향신문",
    "donga.com": "동아일보",
    "joongang.co.kr": "중앙일보",
    "hani.co.kr": "한겨레",
    "hankookilbo.com": "한국일보",
    "news.kbs.co.kr": "KBS",
    "imnews.imbc.com": "MBC",
    "news.sbs.co.kr": "SBS",
    "yna.co.kr": "연합뉴스",
    "ytn.co.kr": "YTN",
}

def extract_press_from_url(url):
    domain = urlparse(url).netloc
    domain = domain.replace("www.", "")
    dom_parts = domain.split('.')
    if len(dom_parts) >= 4:
        domain = '.'.join(dom_parts[-4:])
    return DOMAIN2PRESS.get(domain, domain)


def has_classes(tag, classes):
    tag_classes = tag.get("class", [])
    return all(cls in tag_classes for cls in classes)

def crawl_naver_news_titles_and_links(query, max_results=100):
    headers = {"User-Agent": "Mozilla/5.0"}
    encoded_query = quote(query)
    news = []
    seen = set()
    page = 1
    
    allowed_presses = set(DOMAIN2PRESS.values())

    while len(news) < max_results:
        start = 1 + (page-1)*10
        url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&start={start}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 1. 리스트 블록 (fds-news-item-list-tab)
        for list_block in soup.find_all("div", class_=["sds-comps-vertical-layout", "sds-comps-full-layout", "fds-news-item-list-tab"]):
            # print(list_block)
            # 2. 1단계: 바로 아래 자식 - sds-comps-vertical-layout sds-comps-full-layout
            for child1 in list_block.find_all("div", recursive=False):
                if not has_classes(child1, ["sds-comps-vertical-layout", "sds-comps-full-layout"]):
                    continue
                # print(child1)
                # 3. 2단계: 바로 아래 자식 - sds-comps-base-layout sds-comps-full-layout
                for child2 in child1.find_all("div", recursive=False):
                    if not has_classes(child2, ["sds-comps-base-layout", "sds-comps-full-layout"]):
                        continue
                    # print(child2)
                    # 4. 3단계: 바로 아래 자식 - sds-comps-vertical-layout sds-comps-full-layout
                    for child3 in child2.find_all("div", recursive=False):
                        if not has_classes(child3, ["sds-comps-vertical-layout", "sds-comps-full-layout"]):
                            continue
                        # print(child3)
                        # 5. 기사 블록: a[nocr="1"]와 headline1 span 찾기
                        a_tag = child3.find("a", attrs={"nocr": "1"}, recursive=False)
                        if a_tag:
                            title_tag = a_tag.find("span", class_="sds-comps-text-type-headline1", recursive=False)
                            if title_tag:
                                url = a_tag.get("href")
                                title = title_tag.get_text(strip=True)
                                # print(url)
                                # print(title)
                                if url and title and (url, title) not in seen:
                                    press = extract_press_from_url(url)
                                    if press in allowed_presses:
                                        news.append({"press": press, "title": title, "url": url})
                                        seen.add((url, title))
                                        if len(news) >= max_results:
                                            return news
                                
        # 페이지에 기사 없으면 break
        if not soup.find_all("div", class_="fds-news-item-list-tab"):
            break
        page += 1
        time.sleep(0.5)

    return news

def crawl_query_list(base_query):
    # 1. 쿼리 리스트 생성
    query_list = [
        base_query,
        base_query + " 찬성",
        base_query + " 긍정",
        base_query + " 반대",
        base_query + " 부정"
    ]

    # 2. 각 쿼리별로 기사 크롤링
    all_news = []
    seen_urls = set()
    for query in query_list:
        news_items = crawl_naver_news_titles_and_links(query, max_results=1)
        for item in news_items:
            if item['url'] not in seen_urls:
                all_news.append(item)
                seen_urls.add(item['url'])

    # 3. id 부여
    for idx, item in enumerate(all_news, 1):
        item['id'] = idx

    return all_news

# 사용 예시
if __name__ == "__main__":
    base_query = "검찰청 폐지"
    result = crawl_query_list(base_query)
    # 결과 json 파일로 저장
    with open(f"/home/tag_cache/{base_query}_crawling.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"{len(result)}개 기사 저장 완료! (/home/tag_cache/crawling_{base_query}.json)")
    