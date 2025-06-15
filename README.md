# 📰 BiasBreaker

**BiasBreaker**는 하나의 키워드로 검색하면 **상반된 시각의 뉴스 기사**를 나란히 보여줌으로써, 정보 편향을 줄이고 균형 잡힌 시각을 갖도록 돕는 뉴스 비교 플랫폼입니다.

---

## 🔍 주요 기능

- 🔎 검색 키워드 기반 뉴스 수집 및 좌우 시각 정렬
- 📜 사용자별 검색 기록(히스토리) 확인 및 개별/전체 삭제
- 📁 뉴스 비교 결과 PDF 저장 (아카이브)
- 🔐 Google 로그인 (OAuth 2.0)
- 💽 검색 및 아카이브 기록 DB 저장
- 📤 cafe24 호스팅 환경 지원

---

## 🌐 데모 주소

[https://cis0105.mycafe24.com]


---

## 🛠 기술 스택

| 영역        | 사용 기술                                     |
|-------------|----------------------------------------------|
| **Frontend** | HTML, CSS, JavaScript                        |
| **Backend**  | PHP (세션 기반 인증), MariaDB                |
| **PDF 생성** | Dompdf (한글 폰트 내장 포함)                 |
| **인증**     | Google OAuth 2.0                             |
| **호스팅**   | cafe24 웹 호스팅                             |

---

## 📁 디렉토리 구조 예시

```
/archives/              → 저장된 PDF 파일 경로
/fonts/                 → NotoSansKR.ttf 등 한글 폰트
/vendor/                → Composer 패키지 (Dompdf)
db.php                  → DB 연결 설정
login.php               → Google 로그인 처리
logout.php              → 로그아웃 처리
me.php                  → 로그인 상태 확인 API
save_pdf.php            → 아카이브 저장 API
delete_history.php      → 히스토리 삭제 API
delete_archive.php      → 아카이브 삭제 API
index.html              → 검색 및 로그인 UI
history.html            → 히스토리/아카이브 확인
searchresult.html       → 뉴스 비교 결과 페이지
```

---

## ⚙️ 설치 방법

1. **클론 & 설치**
   ```bash
   git clone https://github.com/yourusername/biasbreaker.git
   cd biasbreaker
   composer install
   ```

2. **폰트 준비**
   - `fonts/` 폴더에 `NotoSansKR-Regular.ttf` 추가

3. **DB 구성**
   - `db.php` 파일에 접속 정보 설정
   - 테이블 예시:

     ```sql
     CREATE TABLE search_history (
         id INT AUTO_INCREMENT PRIMARY KEY,
         email VARCHAR(255),
         query TEXT,
         searched_at DATETIME DEFAULT CURRENT_TIMESTAMP
     );

     CREATE TABLE archive_list (
         id INT AUTO_INCREMENT PRIMARY KEY,
         email VARCHAR(255),
         query TEXT,
         pdf_path TEXT,
         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
     );
     ```

4. **Google OAuth 설정**
   - Google Cloud Console에서 웹 애플리케이션용 OAuth 클라이언트 ID 발급
   - 로그인 성공 시 `$_SESSION['user']`에 사용자 정보 저장

5. **cafe24 업로드 시 주의사항**
   - `archives/` 디렉토리는 쓰기 권한 필요 (`chmod 755 archives`)
   - `/vendor` 폴더 함께 업로드 필요


