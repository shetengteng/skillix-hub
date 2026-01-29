#!/usr/bin/env python3
"""
Swagger API 读取器 - 获取、解析并缓存 Swagger/OpenAPI 文档
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
import yaml

from doc_generator import generate_api_doc


def fetch_with_browser(url: str, timeout: int = 120) -> tuple:
    """使用浏览器获取内容（用于需要登录认证的场景）"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
    except ImportError:
        raise Exception("浏览器模式需要 selenium，请运行: pip install selenium")
    
    import time
    from urllib.parse import urljoin, urlparse
    
    print(f"\n🌐 正在打开浏览器...")
    print(f"   URL: {url}")
    print(f"   请在浏览器中完成登录，页面加载完成后将自动关闭\n")
    
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        print("⏳ 等待 Swagger UI 加载...\n")
        
        start_time = datetime.now()
        content = None
        actual_url = url
        
        while (datetime.now() - start_time).seconds < timeout:
            time.sleep(3)
            
            current_url = driver.current_url
            page_source = driver.page_source
            elapsed = (datetime.now() - start_time).seconds
            
            # 检测 Swagger UI 是否已加载
            swagger_loaded = False
            try:
                swagger_ui = driver.find_elements(By.CLASS_NAME, "swagger-ui")
                info_section = driver.find_elements(By.CLASS_NAME, "info")
                operations = driver.find_elements(By.CLASS_NAME, "opblock")
                
                if swagger_ui and (info_section or operations):
                    swagger_loaded = True
                    print(f"✅ 检测到 Swagger UI（{len(operations)} 个接口）")
            except Exception:
                print(f"   检查页面中... ({elapsed}s)")
            
            if swagger_loaded:
                # 尝试从页面提取 API 文档 URL
                extracted_url = extract_swagger_url_from_html(page_source, current_url)
                
                if not extracted_url:
                    # 尝试常见路径
                    parsed = urlparse(current_url)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    path_prefix = ""
                    if "/swagger-ui" in parsed.path:
                        path_prefix = parsed.path.split("/swagger-ui")[0]
                    
                    common_paths = [
                        f"{path_prefix}/v3/api-docs",
                        f"{path_prefix}/v2/api-docs",
                        f"{path_prefix}/api-docs",
                        f"{path_prefix}/swagger.json",
                        "/v3/api-docs",
                        "/v2/api-docs",
                        "/api-docs",
                    ]
                    
                    for path in common_paths:
                        test_url = urljoin(base, path)
                        print(f"   尝试: {test_url}")
                        try:
                            driver.get(test_url)
                            time.sleep(2)
                            
                            body_text = driver.find_element(By.TAG_NAME, "body").text
                            if body_text.strip().startswith("{"):
                                try:
                                    data = json.loads(body_text)
                                    if "swagger" in data or "openapi" in data or "paths" in data:
                                        print(f"✅ 找到 API 文档: {test_url}")
                                        content = body_text
                                        actual_url = test_url
                                        break
                                except json.JSONDecodeError:
                                    pass
                            
                            # 检查 pre 标签
                            pre_elements = driver.find_elements(By.TAG_NAME, "pre")
                            if pre_elements:
                                pre_text = pre_elements[0].text
                                if pre_text.strip().startswith("{"):
                                    try:
                                        data = json.loads(pre_text)
                                        if "swagger" in data or "openapi" in data or "paths" in data:
                                            print(f"✅ 找到 API 文档: {test_url}")
                                            content = pre_text
                                            actual_url = test_url
                                            break
                                    except json.JSONDecodeError:
                                        pass
                        except Exception:
                            continue
                    
                    if content:
                        break
                else:
                    print(f"✅ 找到 API 文档 URL: {extracted_url}")
                    driver.get(extracted_url)
                    time.sleep(2)
                    
                    try:
                        pre_elements = driver.find_elements(By.TAG_NAME, "pre")
                        if pre_elements:
                            content = pre_elements[0].text
                        else:
                            content = driver.find_element(By.TAG_NAME, "body").text
                        actual_url = extracted_url
                        break
                    except Exception as e:
                        print(f"   获取内容失败: {e}")
            
            if elapsed % 15 == 0 and elapsed > 0:
                print(f"   等待中... ({elapsed}s)")
        
        if not content:
            raise Exception(f"超时 ({timeout}s)，未能获取 API 文档")
        
        return content, actual_url
        
    finally:
        if driver:
            print("\n🔒 关闭浏览器...")
            driver.quit()


# 缓存目录
SCRIPT_DIR = Path(__file__).parent.parent
CACHE_DIR = SCRIPT_DIR / "cache"
INDEX_FILE = CACHE_DIR / "index.json"


def get_api_hash(url: str) -> str:
    """生成 URL 的哈希值"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def load_index() -> dict:
    """加载索引文件"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"apis": []}


def save_index(index: dict) -> None:
    """保存索引文件"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def find_api_by_alias_or_url(alias: Optional[str] = None, url: Optional[str] = None) -> Optional[dict]:
    """通过别名或 URL 查找 API"""
    index = load_index()
    for api in index["apis"]:
        if alias and api.get("alias") == alias:
            return api
        if url and api.get("url") == url:
            return api
    return None


def build_auth_headers(auth_type: Optional[str], **kwargs) -> dict:
    """构建认证请求头"""
    headers = {}
    
    if not auth_type:
        return headers
    
    if auth_type == "bearer":
        token = kwargs.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    
    elif auth_type == "basic":
        import base64
        username = kwargs.get("username", "")
        password = kwargs.get("password", "")
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"
    
    elif auth_type == "apikey":
        key_name = kwargs.get("key_name")
        key_value = kwargs.get("key_value")
        key_in = kwargs.get("key_in", "header")
        if key_in == "header" and key_name and key_value:
            headers[key_name] = key_value
    
    return headers


def build_auth_params(auth_type: Optional[str], **kwargs) -> dict:
    """构建认证查询参数"""
    params = {}
    
    if auth_type == "apikey":
        key_name = kwargs.get("key_name")
        key_value = kwargs.get("key_value")
        key_in = kwargs.get("key_in", "header")
        if key_in == "query" and key_name and key_value:
            params[key_name] = key_value
    
    return params


def extract_swagger_url_from_html(html_content: str, base_url: str) -> Optional[str]:
    """从 Swagger UI HTML 页面提取 API 文档 URL"""
    import re
    from urllib.parse import urljoin
    
    patterns = [
        r'url\s*:\s*["\']([^"\']+)["\']',
        r'configUrl\s*:\s*["\']([^"\']+)["\']',
        r'spec-url\s*=\s*["\']([^"\']+)["\']',
        r'data-url\s*=\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            found_url = match.group(1)
            if not found_url.startswith(('http://', 'https://')):
                found_url = urljoin(base_url, found_url)
            return found_url
    
    return None


def guess_swagger_json_url(html_url: str) -> list:
    """猜测可能的 Swagger JSON URL"""
    from urllib.parse import urlparse, urljoin
    
    parsed = urlparse(html_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    common_paths = [
        "/v3/api-docs", "/v2/api-docs", "/api-docs",
        "/swagger.json", "/openapi.json",
        "/api/swagger.json", "/api/openapi.json",
        "/swagger/v1/swagger.json", "/swagger/v2/swagger.json",
    ]
    
    if "swagger-ui" in html_url:
        path_base = parsed.path.rsplit("/swagger-ui", 1)[0]
        for p in common_paths:
            common_paths.append(path_base + p)
    
    return [urljoin(base, p) for p in common_paths]


def fetch_swagger(url: str, auth_type: Optional[str] = None, verify_ssl: bool = True, 
                  use_browser: bool = False, browser_timeout: int = 120, **auth_kwargs) -> tuple[dict, str]:
    """获取 Swagger/OpenAPI 文档，返回 (数据, 实际URL)"""
    
    # 浏览器模式
    if use_browser:
        content, actual_url = fetch_with_browser(url, browser_timeout)
        try:
            return json.loads(content), actual_url
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(content), actual_url
            except yaml.YAMLError:
                raise Exception("无法解析浏览器获取的内容")
    
    headers = build_auth_headers(auth_type, **auth_kwargs)
    params = build_auth_params(auth_type, **auth_kwargs)
    headers["Accept"] = "application/json, application/yaml, text/html, */*"
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=verify_ssl)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (401, 403):
            raise Exception(f"认证失败 (HTTP {e.response.status_code})，请提供有效的认证信息")
        raise Exception(f"HTTP 错误: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"请求失败: {e}")
    
    content_type = response.headers.get("Content-Type", "")
    content = response.text
    
    # 检测是否为 HTML 页面
    if "text/html" in content_type or content.strip().startswith(("<!DOCTYPE", "<html", "<HTML")):
        print("检测到 Swagger UI HTML 页面，正在提取 API 文档 URL...")
        
        extracted_url = extract_swagger_url_from_html(content, url)
        if extracted_url:
            print(f"找到 API 文档 URL: {extracted_url}")
            return fetch_swagger(extracted_url, auth_type, verify_ssl, **auth_kwargs)
        
        print("尝试常见 Swagger JSON 路径...")
        guessed_urls = guess_swagger_json_url(url)
        
        for guessed_url in guessed_urls:
            try:
                headers_json = headers.copy()
                headers_json["Accept"] = "application/json, application/yaml"
                resp = requests.get(guessed_url, headers=headers_json, params=params, 
                                   timeout=10, verify=verify_ssl)
                if resp.status_code == 200:
                    try:
                        data = json.loads(resp.text)
                        if "swagger" in data or "openapi" in data or "paths" in data:
                            print(f"找到 API 文档: {guessed_url}")
                            return data, guessed_url
                    except json.JSONDecodeError:
                        try:
                            data = yaml.safe_load(resp.text)
                            if isinstance(data, dict) and ("swagger" in data or "openapi" in data or "paths" in data):
                                print(f"找到 API 文档: {guessed_url}")
                                return data, guessed_url
                        except yaml.YAMLError:
                            pass
            except requests.exceptions.RequestException:
                continue
        
        raise Exception("无法找到 Swagger JSON URL，请直接提供 JSON/YAML URL")
    
    # 尝试解析 JSON
    try:
        return json.loads(content), url
    except json.JSONDecodeError:
        pass
    
    # 尝试解析 YAML
    try:
        return yaml.safe_load(content), url
    except yaml.YAMLError:
        pass
    
    raise Exception("无法解析响应内容为 JSON 或 YAML")


def cmd_add(args) -> None:
    """添加新 API"""
    url = args.url
    alias = args.alias or urlparse(url).netloc.replace(".", "-")
    
    # 检查是否已存在
    existing = find_api_by_alias_or_url(alias=alias)
    if existing:
        print(f"错误: 别名 '{alias}' 已存在，请使用 'refresh' 更新")
        sys.exit(1)
    
    existing_url = find_api_by_alias_or_url(url=url)
    if existing_url:
        print(f"错误: URL 已缓存，别名为 '{existing_url['alias']}'，请使用 'refresh' 更新")
        sys.exit(1)
    
    print(f"正在获取 Swagger: {url}")
    
    auth_kwargs = {
        "token": args.token,
        "username": args.username,
        "password": args.password,
        "key_name": args.key_name,
        "key_value": args.key_value,
        "key_in": args.key_in,
    }
    
    try:
        swagger_data, actual_url = fetch_swagger(
            url, args.auth_type, 
            verify_ssl=not args.no_verify,
            use_browser=args.browser,
            browser_timeout=args.browser_timeout,
            **auth_kwargs
        )
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    if actual_url != url:
        print(f"使用实际 API 文档 URL: {actual_url}")
        url = actual_url
    
    # 提取信息
    info = swagger_data.get("info", {})
    title = info.get("title", "Unknown API")
    version = info.get("version", "unknown")
    description = info.get("description", "")
    
    # 统计接口数量
    paths = swagger_data.get("paths", {})
    endpoint_count = sum(len([m for m in p.keys() if m in ("get", "post", "put", "delete", "patch")])
                        for p in paths.values())
    
    # 创建缓存目录
    api_hash = get_api_hash(url)
    api_dir = CACHE_DIR / api_hash
    api_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存原始数据
    with open(api_dir / "raw.json", "w", encoding="utf-8") as f:
        json.dump(swagger_data, f, indent=2, ensure_ascii=False)
    
    # 生成并保存文档
    doc_content = generate_api_doc(swagger_data, url)
    with open(api_dir / "api-doc.md", "w", encoding="utf-8") as f:
        f.write(doc_content)
    
    # 保存元数据
    now = datetime.now().isoformat()
    meta = {
        "url": url,
        "alias": alias,
        "title": title,
        "version": version,
        "description": description[:200] if description else "",
        "endpoint_count": endpoint_count,
        "created_at": now,
        "updated_at": now,
        "auth_type": args.auth_type,
    }
    
    with open(api_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    # 更新索引
    index = load_index()
    index["apis"].append({
        "id": api_hash,
        "alias": alias,
        "url": url,
        "title": title,
        "version": version,
        "last_updated": now,
    })
    save_index(index)
    
    print(f"\n✅ API 添加成功!")
    print(f"   别名: {alias}")
    print(f"   标题: {title}")
    print(f"   版本: {version}")
    print(f"   接口数: {endpoint_count}")
    print(f"\n使用 'swagger read --alias {alias}' 查看文档")


def cmd_list(args) -> None:
    """列出所有已缓存的 API"""
    index = load_index()
    
    if not index["apis"]:
        print("暂无缓存的 API，请使用 'add' 命令添加")
        return
    
    print("\n📚 已缓存的 API:\n")
    print(f"{'别名':<20} {'标题':<30} {'版本':<10} {'更新时间':<20}")
    print("-" * 80)
    
    for api in index["apis"]:
        alias = api.get("alias", "N/A")[:19]
        title = api.get("title", "N/A")[:29]
        version = api.get("version", "N/A")[:9]
        updated = api.get("last_updated", "N/A")[:19]
        print(f"{alias:<20} {title:<30} {version:<10} {updated:<20}")
    
    print(f"\n共 {len(index['apis'])} 个 API")


def cmd_read(args) -> None:
    """读取并输出 API 文档"""
    api = find_api_by_alias_or_url(alias=args.alias, url=args.url)
    
    if not api:
        identifier = args.alias or args.url
        print(f"错误: 未找到 API '{identifier}'，请使用 'list' 查看可用的 API")
        sys.exit(1)
    
    api_dir = CACHE_DIR / api["id"]
    doc_file = api_dir / "api-doc.md"
    
    if not doc_file.exists():
        print(f"错误: 文档文件不存在，请尝试 'refresh --alias {api['alias']}'")
        sys.exit(1)
    
    with open(doc_file, "r", encoding="utf-8") as f:
        print(f.read())


def cmd_refresh(args) -> None:
    """刷新 API 缓存"""
    api = find_api_by_alias_or_url(alias=args.alias, url=args.url)
    
    if not api:
        identifier = args.alias or args.url
        print(f"错误: 未找到 API '{identifier}'，请先使用 'add' 添加")
        sys.exit(1)
    
    api_dir = CACHE_DIR / api["id"]
    meta_file = api_dir / "meta.json"
    
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    url = meta["url"]
    print(f"正在刷新 API: {url}")
    
    auth_type = args.auth_type or meta.get("auth_type")
    auth_kwargs = {
        "token": args.token,
        "username": args.username,
        "password": args.password,
        "key_name": args.key_name,
        "key_value": args.key_value,
        "key_in": args.key_in,
    }
    
    try:
        swagger_data, _ = fetch_swagger(
            url, auth_type, 
            verify_ssl=not args.no_verify,
            use_browser=args.browser,
            browser_timeout=args.browser_timeout,
            **auth_kwargs
        )
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    # 更新信息
    info = swagger_data.get("info", {})
    paths = swagger_data.get("paths", {})
    endpoint_count = sum(len([m for m in p.keys() if m in ("get", "post", "put", "delete", "patch")])
                        for p in paths.values())
    
    with open(api_dir / "raw.json", "w", encoding="utf-8") as f:
        json.dump(swagger_data, f, indent=2, ensure_ascii=False)
    
    doc_content = generate_api_doc(swagger_data, url)
    with open(api_dir / "api-doc.md", "w", encoding="utf-8") as f:
        f.write(doc_content)
    
    now = datetime.now().isoformat()
    meta.update({
        "title": info.get("title", meta.get("title")),
        "version": info.get("version", meta.get("version")),
        "description": info.get("description", "")[:200],
        "endpoint_count": endpoint_count,
        "updated_at": now,
        "auth_type": auth_type,
    })
    
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    index = load_index()
    for idx_api in index["apis"]:
        if idx_api["id"] == api["id"]:
            idx_api["title"] = meta["title"]
            idx_api["version"] = meta["version"]
            idx_api["last_updated"] = now
            break
    save_index(index)
    
    print(f"\n✅ API 刷新成功!")
    print(f"   标题: {meta['title']}")
    print(f"   版本: {meta['version']}")
    print(f"   接口数: {endpoint_count}")


def cmd_remove(args) -> None:
    """删除 API 缓存"""
    api = find_api_by_alias_or_url(alias=args.alias, url=args.url)
    
    if not api:
        identifier = args.alias or args.url
        print(f"错误: 未找到 API '{identifier}'")
        sys.exit(1)
    
    import shutil
    
    api_dir = CACHE_DIR / api["id"]
    if api_dir.exists():
        shutil.rmtree(api_dir)
    
    index = load_index()
    index["apis"] = [a for a in index["apis"] if a["id"] != api["id"]]
    save_index(index)
    
    print(f"✅ API '{api['alias']}' 已删除")


def main():
    parser = argparse.ArgumentParser(description="Swagger API 读取器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # add 命令
    add_parser = subparsers.add_parser("add", help="添加新 API")
    add_parser.add_argument("--url", required=True, help="Swagger/OpenAPI URL")
    add_parser.add_argument("--alias", help="API 别名（可选）")
    add_parser.add_argument("--auth-type", choices=["bearer", "basic", "apikey"], help="认证类型")
    add_parser.add_argument("--token", help="Bearer token")
    add_parser.add_argument("--username", help="Basic auth 用户名")
    add_parser.add_argument("--password", help="Basic auth 密码")
    add_parser.add_argument("--key-name", help="API key 名称")
    add_parser.add_argument("--key-value", help="API key 值")
    add_parser.add_argument("--key-in", choices=["header", "query"], default="header", help="API key 位置")
    add_parser.add_argument("--no-verify", action="store_true", help="跳过 SSL 验证")
    add_parser.add_argument("--browser", action="store_true", help="使用浏览器模式（SSO/OAuth）")
    add_parser.add_argument("--browser-timeout", type=int, default=120, help="浏览器超时时间（秒）")
    
    # list 命令
    subparsers.add_parser("list", help="列出已缓存的 API")
    
    # read 命令
    read_parser = subparsers.add_parser("read", help="读取 API 文档")
    read_parser.add_argument("--alias", help="API 别名")
    read_parser.add_argument("--url", help="API URL")
    
    # refresh 命令
    refresh_parser = subparsers.add_parser("refresh", help="刷新 API 文档")
    refresh_parser.add_argument("--alias", help="API 别名")
    refresh_parser.add_argument("--url", help="API URL")
    refresh_parser.add_argument("--auth-type", choices=["bearer", "basic", "apikey"], help="认证类型")
    refresh_parser.add_argument("--token", help="Bearer token")
    refresh_parser.add_argument("--username", help="Basic auth 用户名")
    refresh_parser.add_argument("--password", help="Basic auth 密码")
    refresh_parser.add_argument("--key-name", help="API key 名称")
    refresh_parser.add_argument("--key-value", help="API key 值")
    refresh_parser.add_argument("--key-in", choices=["header", "query"], default="header", help="API key 位置")
    refresh_parser.add_argument("--no-verify", action="store_true", help="跳过 SSL 验证")
    refresh_parser.add_argument("--browser", action="store_true", help="使用浏览器模式")
    refresh_parser.add_argument("--browser-timeout", type=int, default=120, help="浏览器超时时间（秒）")
    
    # remove 命令
    remove_parser = subparsers.add_parser("remove", help="删除 API 缓存")
    remove_parser.add_argument("--alias", help="API 别名")
    remove_parser.add_argument("--url", help="API URL")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "read": cmd_read,
        "refresh": cmd_refresh,
        "remove": cmd_remove,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
