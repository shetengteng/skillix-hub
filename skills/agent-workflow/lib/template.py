"""模板渲染 + 条件表达式求值（白名单 parser，绝不使用 eval/exec）。

对外：
    render(text, vars, strict_vars=True)        # 渲染 {{var.path}}
    evaluate_condition(expr, vars)               # 评估白名单表达式
    redact_secrets(text, secrets)                # 把 secret 在文本中替换为 ***REDACTED***
    expand_env_in_vars(vars_)                    # 把 vars 中的 "$ENV:NAME" 展开为环境变量值
    collect_secret_values(vars_)                 # 提取 vars._secrets 标记字段的实际值

变量寻址：
    {{x}}                  → vars["x"]
    {{node.research.output}} → vars["node"]["research"]["output"]
    支持点路径任意深度。
"""
from __future__ import annotations

import os
import re
from typing import Any

from lib.errors import ErrorCode, WorkflowError

VAR_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][\w\.]*)\s*\}\}")
SECRET_MASK = "***REDACTED***"
ENV_PREFIX = "$ENV:"

ALLOWED_OPERATORS = {"==", "!=", "<", ">", "<=", ">="}


def _lookup(path: str, vars_: dict[str, Any]) -> Any:
    """按点路径取值，找不到抛 KeyError（用于 strict 模式）。"""
    parts = path.split(".")
    cur: Any = vars_
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def render(text: str, vars_: dict[str, Any], *, strict_vars: bool = True) -> str:
    """把字符串中所有 `{{path}}` 替换为 vars 对应值。

    - strict_vars=True：未定义变量 → 抛 WorkflowError(VAR_NOT_IN_SCOPE)
    - strict_vars=False：未定义变量 → 保留原 `{{...}}`
    - 非字符串值会被 str(...)
    """
    if not isinstance(text, str):
        return text

    def repl(match: re.Match[str]) -> str:
        path = match.group(1)
        try:
            value = _lookup(path, vars_)
        except KeyError:
            if strict_vars:
                raise WorkflowError(
                    ErrorCode.VAR_NOT_IN_SCOPE,
                    f"undefined variable: {{{{{path}}}}}",
                    location={"path": path},
                )
            return match.group(0)
        return str(value) if not isinstance(value, str) else value

    return VAR_PATTERN.sub(repl, text)


def redact_secrets(text: str, secrets: list[str] | None) -> str:
    """把 text 中出现的 secret 值替换为 ***REDACTED***（仅用于 events/audit 写盘）。"""
    if not secrets or not isinstance(text, str):
        return text
    for value in secrets:
        if not isinstance(value, str) or not value:
            continue
        text = text.replace(value, SECRET_MASK)
    return text


def redact_in_obj(obj: Any, secrets: list[str] | None) -> Any:
    """递归对 dict / list / str 中的 secret 值做脱敏。其他类型原样返回。"""
    if not secrets:
        return obj
    if isinstance(obj, str):
        return redact_secrets(obj, secrets)
    if isinstance(obj, list):
        return [redact_in_obj(item, secrets) for item in obj]
    if isinstance(obj, dict):
        return {k: redact_in_obj(v, secrets) for k, v in obj.items()}
    return obj


def expand_env_in_vars(vars_: dict[str, Any]) -> dict[str, Any]:
    """把 vars 中所有形如 "$ENV:NAME" 的字符串替换为环境变量值。

    - 仅顶层 + 一级嵌套字典中的字符串值会被处理（避免误伤业务数据）
    - 找不到环境变量 → 抛 WorkflowError(PARAMS_INVALID)
    """
    if not isinstance(vars_, dict):
        return vars_
    expanded: dict[str, Any] = {}
    for key, value in vars_.items():
        if isinstance(value, str) and value.startswith(ENV_PREFIX):
            env_name = value[len(ENV_PREFIX):].strip()
            if not env_name:
                raise WorkflowError(
                    ErrorCode.PARAMS_INVALID,
                    f"empty env var name in vars.{key}",
                    location={"path": f"vars.{key}"},
                )
            env_val = os.environ.get(env_name)
            if env_val is None:
                raise WorkflowError(
                    ErrorCode.PARAMS_INVALID,
                    f"environment variable {env_name} required by vars.{key} is not set",
                    location={"path": f"vars.{key}", "env": env_name},
                )
            expanded[key] = env_val
        elif isinstance(value, dict):
            expanded[key] = expand_env_in_vars(value)
        else:
            expanded[key] = value
    return expanded


def collect_secret_values(vars_: dict[str, Any]) -> list[str]:
    """从 vars._secrets（字段名列表）中提取实际值，去重去空，仅返回非空字符串。"""
    if not isinstance(vars_, dict):
        return []
    secret_keys = vars_.get("_secrets")
    if not isinstance(secret_keys, list):
        return []
    values: list[str] = []
    seen: set[str] = set()
    for key in secret_keys:
        if not isinstance(key, str):
            continue
        val = vars_.get(key)
        if isinstance(val, str) and val and val not in seen:
            values.append(val)
            seen.add(val)
    # 较长的先 replace，避免短串吃掉长串前缀
    values.sort(key=len, reverse=True)
    return values


_TOKEN_PATTERN = re.compile(
    r"""
    \s*(
        \{\{\s*[A-Za-z_][\w\.]*\s*\}\}     |   # var ref
        "(?:[^"\\]|\\.)*"                  |   # double quoted string
        '(?:[^'\\]|\\.)*'                  |   # single quoted string
        -?\d+\.\d+ | -?\d+                 |   # number
        true | false | null                |   # literal
        == | != | <= | >= | < | >          |   # cmp
        && | \|\|                          |   # logical
        ! | \( | \)                            # unary / paren
    )
    """,
    re.VERBOSE,
)


def _tokenize(expr: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(expr):
        match = _TOKEN_PATTERN.match(expr, pos)
        if not match:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"invalid condition token at pos {pos}: {expr[pos:pos+16]!r}",
            )
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


class _Parser:
    """recursive descent: or → and → not → cmp → atom（白名单内）"""

    def __init__(self, tokens: list[str], vars_: dict[str, Any]) -> None:
        self.tokens = tokens
        self.vars = vars_
        self.pos = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> Any:
        value = self._or()
        if self.pos != len(self.tokens):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"unexpected token after expression: {self.tokens[self.pos]!r}",
            )
        return value

    def _or(self) -> Any:
        left = self._and()
        while self._peek() == "||":
            self._consume()
            right = self._and()
            left = bool(left) or bool(right)
        return left

    def _and(self) -> Any:
        left = self._not()
        while self._peek() == "&&":
            self._consume()
            right = self._not()
            left = bool(left) and bool(right)
        return left

    def _not(self) -> Any:
        if self._peek() == "!":
            self._consume()
            return not bool(self._not())
        return self._cmp()

    def _cmp(self) -> Any:
        left = self._atom()
        if self._peek() in ALLOWED_OPERATORS:
            op = self._consume()
            right = self._atom()
            return _apply_cmp(op, left, right)
        return left

    def _atom(self) -> Any:
        tok = self._peek()
        if tok is None:
            raise WorkflowError(ErrorCode.PARAMS_INVALID, "unexpected end of expression")
        if tok == "(":
            self._consume()
            value = self._or()
            if self._peek() != ")":
                raise WorkflowError(ErrorCode.PARAMS_INVALID, "missing )")
            self._consume()
            return value
        self._consume()
        if tok.startswith("{{"):
            inner = tok[2:-2].strip()
            try:
                return _lookup(inner, self.vars)
            except KeyError:
                raise WorkflowError(
                    ErrorCode.VAR_NOT_IN_SCOPE,
                    f"undefined variable in condition: {{{{{inner}}}}}",
                    location={"path": inner},
                )
        if tok == "true":
            return True
        if tok == "false":
            return False
        if tok == "null":
            return None
        if tok.startswith('"') or tok.startswith("'"):
            return tok[1:-1].encode().decode("unicode_escape")
        try:
            if "." in tok:
                return float(tok)
            return int(tok)
        except ValueError:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID, f"unrecognised literal: {tok!r}"
            )


def _apply_cmp(op: str, left: Any, right: Any) -> bool:
    try:
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
    except TypeError as exc:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"incompatible types for operator {op!r}: {type(left).__name__} vs {type(right).__name__}",
        ) from exc
    raise WorkflowError(ErrorCode.PARAMS_INVALID, f"unsupported operator {op!r}")


def evaluate_condition(expr: str, vars_: dict[str, Any]) -> bool:
    """评估白名单条件表达式，返回 bool。"""
    if not isinstance(expr, str) or not expr.strip():
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "condition must be a non-empty string")
    tokens = _tokenize(expr)
    if not tokens:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "condition tokenised to empty")
    parser = _Parser(tokens, vars_)
    return bool(parser.parse())
