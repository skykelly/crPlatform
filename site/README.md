# Life Signals 포털

모든 카테고리·질문의 아티클을 한 사이트에서 보여준다.

- 포털 주소(Claude 아티팩트): (첫 게시 후 기입)
- 원본: `site/catalog.json`(카테고리·질문 목록) + 각 질문 폴더의 `article_rN.html`
- 결과물: `site/dist/` (포털 `index.html`, 회차별 아티클 `<카테고리>/<질문 번호(f1, h1 …)>/rN.html`)

## 갱신 방법

1. 질문 폴더에서 `build_records.py` → `render_article.py`로 아티클을 만든다. 새 회차는 `article_r2.html`처럼 번호만 올린다.
2. 새 카테고리나 질문을 열 때는 `catalog.json`에 추가한다. 질문 폴더에 아티클이 있으면 catalog에 없어도 자동으로 포함된다.
3. `python3 site/build_site.py` 를 실행한다. 깨진 내부 링크가 있으면 실패한다.
4. 같은 아티팩트 주소로 다시 게시한다: 진입 페이지는 `site/dist/artifact_index.html`, 아티클 페이지는 `site/dist/manifest.json`의 `pages` 목록을 같은 경로로 함께 올린다.

`site/dist/index.html`은 완전한 HTML 문서라 GitHub Pages 같은 정적 호스팅에도 그대로 쓸 수 있다.
