import json
import re
from scrapling import StealthyFetcher
from deep_translator import GoogleTranslator
 
def translate_to_zh(text):
    if not text or text == "No description":
        return text
    try:
        return GoogleTranslator(source='auto', target='zh-CN').translate(text)
    except:
        return text

def get_text_from_selectors(selectors):
    """
    【核心核武器】
    传入 xpath 的 //text() 结果，无视任何 HTML 标签和 SVG 阻挡，
    直接把里面所有的纯文本抠出来，拼成干净的字符串。
    """
    if not selectors:
        return ""
    texts = []
    for t in selectors:
        # 兼容 Scrapling 底层的各种数据对象
        if hasattr(t, 'get'):
            val = t.get()
        elif hasattr(t, 'text'):
            val = t.text
        else:
            val = str(t)
        
        if val and str(val).strip():
            texts.append(str(val).strip())
    return " ".join(texts).strip()
 
def fetch_github_trending():
    url = "https://github.com/trending?since=daily"
    print("🌍 正在抓取 GitHub Trending...")
 
    fetcher = StealthyFetcher()
    page = fetcher.fetch(url)
 
    repos = page.css("article.Box-row")
    print(f"✅ 找到 {len(repos)} 个仓库\n")
    results = []
 
    for repo in repos:
        try:
            # 1. 仓库名
            title_nodes = repo.css("h2 a")
            if not title_nodes:
                continue
            href = title_nodes[0].attrib.get("href", "")
            repo_name = href.strip("/")
            repo_url = "https://github.com" + href
 
            # 2. 描述
            desc_nodes = repo.css("p")
            description_en = get_text_from_selectors(desc_nodes[0].xpath('.//text()')) if desc_nodes else "No description"
            description_zh = translate_to_zh(description_en)
 
            # 3. 语言
            lang_nodes = repo.css('[itemprop="programmingLanguage"]')
            language = get_text_from_selectors(lang_nodes[0].xpath('.//text()')) if lang_nodes else "Unknown"
 
            # ==============================================
            # ✅ 游离文本碎渣拼接 + 正则提取
            # ==============================================
            total_stars = "N/A"
            forks = "N/A"
            stars_today = "N/A"
            
            # 提取总 Stars
            st_texts = repo.xpath('.//a[contains(@href, "stargazers")]//text()')
            for word in get_text_from_selectors(st_texts).split():
                if re.match(r'^[\d,]+$', word):
                    total_stars = word
                    break

            # 提取 Forks
            fk_texts = repo.xpath('.//a[contains(@href, "forks") or contains(@href, "members")]//text()')
            for word in get_text_from_selectors(fk_texts).split():
                if re.match(r'^[\d,]+$', word):
                    forks = word
                    break
                    
            # 提取今日 Stars
            all_card_text = get_text_from_selectors(repo.xpath('.//text()')).lower()
            today_match = re.search(r'([\d,]+)\s*stars?\s*today', all_card_text)
            if today_match:
                stars_today = today_match.group(1)
 
            # 5. 贡献者
            built_by = []
            for img in repo.css("img.avatar"):
                alt = img.attrib.get("alt", "")
                user = alt.replace("@", "").strip()
                if user:
                    built_by.append(user)
 
            item = {
                "repo_name": repo_name,
                "repo_url": repo_url,
                "description_en": description_en,
                "description_zh": description_zh,
                "language": language,
                "total_stars": total_stars,
                "forks": forks,
                "stars_today": stars_today,
                "built_by": built_by
            }
            results.append(item)
 
        except Exception as e:
            print(f"❌ 解析失败：{e}")
 
    # ==============================================
    # 💾 数据输出与保存阶段
    # ==============================================

    # 1. 输出到终端
    for idx, item in enumerate(results, 1):
        if item['repo_name']:
            print(f"{idx}. {item['repo_name']}")
            print(f"   ⭐ Stars: {item['total_stars']}")
            print(f"   🍴 Forks: {item['forks']}")
            print(f"   🚀 今日 Star: {item['stars_today']} stars\n")
 
    # 2. 保存 JSON 文件
    with open("github_trending.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 3. 自动生成 Markdown (MD) 文件
    with open("github_trending.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 GitHub Trending 每日趋势榜单\n\n")
        f.write("> 🤖 *本榜单由 Python Scrapling 爬虫自动生成*\n\n---\n\n")
        
        for idx, item in enumerate(results, 1):
            if item['repo_name']:
                f.write(f"### {idx}. [{item['repo_name']}]({item['repo_url']})\n")
                f.write(f"- **核心语言**: `{item['language']}`\n")
                f.write(f"- **数据统计**: ⭐ {item['total_stars']} Stars | 🍴 {item['forks']} Forks | 🚀 今日新增 **{item['stars_today']}** Stars\n")
                f.write(f"- **英文简介**: {item['description_en']}\n")
                f.write(f"- **中文翻译**: {item['description_zh']}\n\n")
                f.write("---\n\n")

    print("💾 抓取完成！")
    print("✅ JSON 数据已保存至: github_trending.json")
    print("✅ Markdown 文档已生成至: github_trending.md")
 
if __name__ == "__main__":
    fetch_github_trending()