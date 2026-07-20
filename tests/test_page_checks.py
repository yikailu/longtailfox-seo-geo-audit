from longtailfox_audit.checks import page_checks
from longtailfox_audit.page import parse_page

HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <title>跨境 SaaS SEO 与 GEO 内容增长平台｜长尾狐</title>
  <meta name="description" content="长尾狐帮助跨境网站规划内容、完成多语言写作、站内优化与外链管理，把自然流量工作沉淀为可持续的数字内容资产。">
  <link rel="canonical" href="https://example.com/">
  <meta property="og:title" content="长尾狐 SEO/GEO">
  <meta property="og:description" content="内容和外链资产平台">
  <meta property="og:image" content="https://example.com/cover.png">
  <meta property="og:url" content="https://example.com/">
  <meta property="og:type" content="website">
  <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Organization","name":"长尾狐","url":"https://example.com/"}
  </script>
</head>
<body>
  <h1>长尾狐 SEO/GEO 内容与外链管理平台</h1>
  <h2>什么是 GEO？</h2>
  <p>GEO 帮助内容在生成式搜索中被理解和引用。我们的项目持续运营 3 年。</p>
  <ul><li>内容规划</li><li>多语言写作</li></ul>
  <table><tr><th>能力</th><th>结果</th></tr><tr><td>内容</td><td>增长</td></tr></table>
  <img src="/cover.png" alt="长尾狐平台">
  <a href="/about">关于我们</a><a href="/contact">联系我们</a>
  <a href="/privacy">隐私政策</a><a href="/terms">服务条款</a>
  <a href="https://developers.google.com/">Google 文档</a>
  <span class="author">长尾狐团队</span><time datetime="2026-07-20">2026-07-20</time>
</body>
</html>
"""


def test_parse_and_check_branded_page() -> None:
    page = parse_page(HTML, "https://example.com/")
    assert page.language == "zh-CN"
    assert "Organization" in page.schema_types
    assert page.images_missing_alt == 0
    checks = page_checks(page, "https://example.com/", 200)
    by_id = {item.check_id: item for item in checks}
    assert by_id["seo.title"].status == "pass"
    assert by_id["seo.schema"].status == "pass"
    assert by_id["geo.entity_clarity"].status == "pass"
    assert by_id["geo.answerability"].status == "pass"
