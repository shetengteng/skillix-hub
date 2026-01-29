#!/usr/bin/env python3
"""
文档生成器 - 从 Swagger/OpenAPI 数据生成 Markdown 文档
"""

from datetime import datetime
from typing import Any, Optional


def get_base_url(swagger_data: dict, source_url: str) -> str:
    """提取 Base URL"""
    # OpenAPI 3.x
    servers = swagger_data.get("servers", [])
    if servers:
        return servers[0].get("url", "")
    
    # Swagger 2.x
    host = swagger_data.get("host", "")
    base_path = swagger_data.get("basePath", "")
    schemes = swagger_data.get("schemes", ["https"])
    
    if host:
        scheme = schemes[0] if schemes else "https"
        return f"{scheme}://{host}{base_path}"
    
    # 回退到源 URL
    from urllib.parse import urlparse
    parsed = urlparse(source_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_security_info(swagger_data: dict) -> str:
    """提取认证信息"""
    lines = []
    
    # OpenAPI 3.x
    components = swagger_data.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    
    # Swagger 2.x
    if not security_schemes:
        security_schemes = swagger_data.get("securityDefinitions", {})
    
    if not security_schemes:
        return "无需认证"
    
    for name, scheme in security_schemes.items():
        scheme_type = scheme.get("type", "unknown")
        
        if scheme_type == "apiKey":
            location = scheme.get("in", "header")
            key_name = scheme.get("name", "api_key")
            lines.append(f"- **{name}**: API Key ({location}: `{key_name}`)")
        elif scheme_type == "http":
            http_scheme = scheme.get("scheme", "bearer")
            lines.append(f"- **{name}**: HTTP {http_scheme.title()}")
        elif scheme_type == "oauth2":
            flows = scheme.get("flows", {})
            flow_types = list(flows.keys())
            lines.append(f"- **{name}**: OAuth2 ({', '.join(flow_types)})")
        elif scheme_type == "basic":
            lines.append(f"- **{name}**: HTTP Basic")
        else:
            lines.append(f"- **{name}**: {scheme_type}")
    
    return "\n".join(lines) if lines else "无需认证"


def resolve_ref(ref: str, swagger_data: dict) -> dict:
    """解析 $ref 引用"""
    if not ref.startswith("#/"):
        return {}
    
    parts = ref[2:].split("/")
    current = swagger_data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return {}
    
    return current if isinstance(current, dict) else {}


def schema_to_string(schema: dict, swagger_data: dict, depth: int = 0) -> str:
    """将 schema 转换为可读字符串"""
    if not schema:
        return "any"
    
    if "$ref" in schema:
        ref = schema["$ref"]
        ref_name = ref.split("/")[-1]
        return f"[{ref_name}](#model-{ref_name.lower()})"
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "array":
        items = schema.get("items", {})
        items_type = schema_to_string(items, swagger_data, depth + 1)
        return f"array[{items_type}]"
    
    if schema_type == "object":
        return "object"
    
    if "enum" in schema:
        enum_values = schema["enum"]
        return f"{schema_type} (enum: {', '.join(str(v) for v in enum_values[:5])}{'...' if len(enum_values) > 5 else ''})"
    
    fmt = schema.get("format")
    if fmt:
        return f"{schema_type} ({fmt})"
    
    return schema_type


def format_parameters(parameters: list, swagger_data: dict) -> str:
    """格式化参数为 Markdown 表格"""
    if not parameters:
        return "无"
    
    lines = [
        "| 名称 | 位置 | 类型 | 必填 | 描述 |",
        "|------|------|------|------|------|"
    ]
    
    for param in parameters:
        if "$ref" in param:
            param = resolve_ref(param["$ref"], swagger_data)
            if not param:
                continue
        
        name = param.get("name", "")
        location = param.get("in", "")
        required = "是" if param.get("required", False) else "否"
        description = param.get("description", "").replace("\n", " ")[:50]
        schema = param.get("schema", param)
        param_type = schema_to_string(schema, swagger_data)
        
        lines.append(f"| `{name}` | {location} | {param_type} | {required} | {description} |")
    
    return "\n".join(lines)


def format_request_body(request_body: dict, swagger_data: dict) -> str:
    """格式化请求体"""
    if not request_body:
        return "无"
    
    if "$ref" in request_body:
        request_body = resolve_ref(request_body["$ref"], swagger_data)
    
    content = request_body.get("content", {})
    required = "必填" if request_body.get("required", False) else "可选"
    description = request_body.get("description", "")
    
    lines = [f"**{required}**"]
    if description:
        lines.append(f"\n{description}")
    
    for content_type, content_data in content.items():
        schema = content_data.get("schema", {})
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            lines.append(f"\n- Content-Type: `{content_type}`")
            lines.append(f"- Schema: [{ref_name}](#model-{ref_name.lower()})")
        else:
            schema_type = schema_to_string(schema, swagger_data)
            lines.append(f"\n- Content-Type: `{content_type}`")
            lines.append(f"- Schema: {schema_type}")
    
    return "\n".join(lines)


def format_responses(responses: dict, swagger_data: dict) -> str:
    """格式化响应为 Markdown 表格"""
    if not responses:
        return "无"
    
    lines = [
        "| 状态码 | 描述 | Schema |",
        "|--------|------|--------|"
    ]
    
    for status, response in responses.items():
        if "$ref" in response:
            response = resolve_ref(response["$ref"], swagger_data)
        
        description = response.get("description", "").replace("\n", " ")[:40]
        schema_str = "-"
        content = response.get("content", {})
        
        # OpenAPI 3.x
        if content:
            for content_type, content_data in content.items():
                schema = content_data.get("schema", {})
                if "$ref" in schema:
                    ref_name = schema["$ref"].split("/")[-1]
                    schema_str = f"[{ref_name}](#model-{ref_name.lower()})"
                else:
                    schema_str = schema_to_string(schema, swagger_data)
                break
        
        # Swagger 2.x
        schema = response.get("schema", {})
        if schema and schema_str == "-":
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                schema_str = f"[{ref_name}](#model-{ref_name.lower()})"
            else:
                schema_str = schema_to_string(schema, swagger_data)
        
        lines.append(f"| {status} | {description} | {schema_str} |")
    
    return "\n".join(lines)


def format_model(name: str, schema: dict, swagger_data: dict) -> str:
    """格式化模型/Schema"""
    lines = [f"### {name}", ""]
    
    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], swagger_data)
    
    description = schema.get("description", "")
    if description:
        lines.append(description)
        lines.append("")
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        properties = schema.get("properties", {})
        required_props = schema.get("required", [])
        
        if properties:
            lines.append("| 属性 | 类型 | 必填 | 描述 |")
            lines.append("|------|------|------|------|")
            
            for prop_name, prop_schema in properties.items():
                prop_type = schema_to_string(prop_schema, swagger_data)
                is_required = "是" if prop_name in required_props else "否"
                prop_desc = prop_schema.get("description", "").replace("\n", " ")[:40]
                lines.append(f"| `{prop_name}` | {prop_type} | {is_required} | {prop_desc} |")
        else:
            lines.append("*空对象或动态属性*")
    
    elif schema_type == "array":
        items = schema.get("items", {})
        items_type = schema_to_string(items, swagger_data)
        lines.append(f"数组元素: {items_type}")
    
    else:
        lines.append(f"类型: {schema_to_string(schema, swagger_data)}")
    
    return "\n".join(lines)


def generate_api_doc(swagger_data: dict, source_url: str) -> str:
    """从 Swagger/OpenAPI 数据生成 Markdown 文档"""
    lines = []
    
    # 头部信息
    info = swagger_data.get("info", {})
    title = info.get("title", "API 文档")
    version = info.get("version", "unknown")
    description = info.get("description", "")
    base_url = get_base_url(swagger_data, source_url)
    
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> **版本**: {version}  ")
    lines.append(f"> **Base URL**: `{base_url}`  ")
    lines.append(f"> **来源**: {source_url}  ")
    lines.append(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    if description:
        lines.append("## 概述")
        lines.append("")
        lines.append(description)
        lines.append("")
    
    # 认证
    lines.append("## 认证")
    lines.append("")
    lines.append(get_security_info(swagger_data))
    lines.append("")
    
    # 接口
    lines.append("---")
    lines.append("")
    lines.append("## 接口")
    lines.append("")
    
    paths = swagger_data.get("paths", {})
    tags_endpoints: dict[str, list] = {}
    
    for path, path_item in paths.items():
        common_params = path_item.get("parameters", [])
        
        for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
            if method not in path_item:
                continue
            
            operation = path_item[method]
            tags = operation.get("tags", ["其他"])
            
            for tag in tags:
                if tag not in tags_endpoints:
                    tags_endpoints[tag] = []
                
                tags_endpoints[tag].append({
                    "path": path,
                    "method": method.upper(),
                    "operation": operation,
                    "common_params": common_params,
                })
    
    for tag, endpoints in sorted(tags_endpoints.items()):
        lines.append(f"### {tag}")
        lines.append("")
        
        for ep in endpoints:
            path = ep["path"]
            method = ep["method"]
            operation = ep["operation"]
            common_params = ep["common_params"]
            
            summary = operation.get("summary", "")
            op_description = operation.get("description", "")
            operation_id = operation.get("operationId", "")
            deprecated = operation.get("deprecated", False)
            
            lines.append(f"#### `{method}` {path}")
            lines.append("")
            
            if deprecated:
                lines.append("> ⚠️ **已废弃**")
                lines.append("")
            
            if summary:
                lines.append(f"**摘要**: {summary}")
                lines.append("")
            
            if op_description and op_description != summary:
                lines.append(op_description)
                lines.append("")
            
            if operation_id:
                lines.append(f"**操作ID**: `{operation_id}`")
                lines.append("")
            
            # 参数
            params = common_params + operation.get("parameters", [])
            lines.append("**参数**:")
            lines.append("")
            lines.append(format_parameters(params, swagger_data))
            lines.append("")
            
            # 请求体 (OpenAPI 3.x)
            request_body = operation.get("requestBody")
            if request_body:
                lines.append("**请求体**:")
                lines.append("")
                lines.append(format_request_body(request_body, swagger_data))
                lines.append("")
            
            # 响应
            responses = operation.get("responses", {})
            lines.append("**响应**:")
            lines.append("")
            lines.append(format_responses(responses, swagger_data))
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # 数据模型
    lines.append("## 数据模型")
    lines.append("")
    
    # OpenAPI 3.x
    components = swagger_data.get("components", {})
    schemas = components.get("schemas", {})
    
    # Swagger 2.x
    if not schemas:
        schemas = swagger_data.get("definitions", {})
    
    if schemas:
        for name, schema in sorted(schemas.items()):
            lines.append(f'<a id="model-{name.lower()}"></a>')
            lines.append("")
            lines.append(format_model(name, schema, swagger_data))
            lines.append("")
    else:
        lines.append("*无数据模型*")
    
    return "\n".join(lines)
