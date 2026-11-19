#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tgu-mcp — MCP-сервер для tgu (Telegram CLI): даёт агенту прямой доступ к
Telegram-аккаунту через инструменты MCP.

Параметры конфига (опционально):
  TGU            путь к бинарнику tgu (по умолчанию: ~/projects/tgu/tgu)
  TGU_ARGS       доп. аргументы, например "--no-color"
"""

import asyncio
import json
import os
import subprocess
import sys

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations as ToolAnnotation

TGU_BIN = os.environ.get("TGU", os.path.expanduser("~/projects/tgu/tgu"))
TGU_ARGS = os.environ.get("TGU_ARGS", "").split()
TIMEOUT = int(os.environ.get("TGU_MCP_TIMEOUT", "120"))

READONLY = ToolAnnotation(readOnlyHint=True, idempotentHint=True)
NEUTRAL = ToolAnnotation(destructiveHint=True, idempotentHint=False)

server = MCPServer(
    name="tgu",
    title="tgu — Telegram CLI (MCP bridge)",
    description=(
        "Инструменты для управления Telegram через tgu CLI: чаты, чтение, отправка, "
        "поиск, разведка (похожих юзеры, стаж по id), миниаппы бота (URL + IP), web view."
    ),
    instructions=(
        "Эти инструменты используют аккаунт пользователя через tgu. "
        "READ-only инструменты (list/read/get) можно звать свободно. "
        "send/reply/delete/react — только по явной просьбе пользователя."
    ),
    version="1.0.0",
)


async def _run(args, stdin_text=None, timeout=TIMEOUT):
    cmd = [TGU_BIN, *TGU_ARGS, *args]
    env = dict(os.environ)
    env.setdefault("NO_COLOR", "1")
    try:
        proc = await asyncio.to_thread(
            lambda: subprocess.run(
                cmd, env=env, capture_output=True, text=True,
                input=stdin_text, timeout=timeout,
            )
        )
    except FileNotFoundError:
        return "tgu не найден: %s. Установи tgu или задай TGU=/path/to/tgu" % TGU_BIN
    except subprocess.TimeoutExpired:
        return "tgu не ответил за %d сек" % timeout
    out = proc.stdout
    if proc.returncode != 0:
        out = (out + "\n" if out else "") + proc.stderr.strip()
    return out.strip() or "(пусто)"


@server.tool(annotations=READONLY, description="Список чатов: имя, id, тип, непрочитанные, превью последнего сообщения. JSON-массив; name — фильтр по подстроке.")
async def chats(limit: int = 30, unread_only: bool = False, type: str = "", name: str = "") -> str:
    args = ["chats", "--limit", str(int(limit)), "--json"]
    if unread_only:
        args.append("--unread")
    if type:
        args += ["--type", str(type)]
    out = await _run(args)
    if not name:
        return out
    try:
        arr = json.loads(out)
    except Exception:
        return out
    n = name.lower()
    return json.dumps([r for r in arr
                       if n in str(r.get("name", "")).lower()
                       or n in str(r.get("username", "")).lower()],
                      ensure_ascii=False, indent=2)


@server.tool(annotations=READONLY, description="Прочитать последние сообщения чата. chat: часть имени/@юзер/id/'me'. JSON-массив сообщений.")
async def read(chat: str, last: int = 10) -> str:
    return await _run(["read", chat, "-l", str(int(last)), "--json"])


@server.tool(annotations=READONLY, description="Список id последних сообщений чата (через пробел).")
async def read_ids(chat: str, last: int = 10) -> str:
    return await _run(["read", chat, "-l", str(int(last)), "--ids-only"])


@server.tool(annotations=READONLY, description="Инфа о пользователе/канале/группе по имени, @юзеру, id или ссылке t.me.")
async def user(who: str) -> str:
    return await _run(["user", who])


@server.tool(annotations=READONLY, description="Инфа о себе (аккаунт пользователя).")
async def me() -> str:
    return await _run(["me"])


@server.tool(annotations=READONLY, description="Статус авторизации tgu.")
async def status() -> str:
    return await _run(["status"])


@server.tool(annotations=READONLY, description="Поиск сообщений: query — запрос; chat — ограничить чат (иначе глобальный по последним чатам). JSON-массив.")
async def search(query: str, chat: str = "", limit: int = 20) -> str:
    args = ["search", query, "--limit", str(int(limit)), "--json"]
    if chat:
        args += ["--chat", chat]
    return await _run(args)


@server.tool(annotations=READONLY, description="Похожие юзеры/боты/каналы по подстроке имени или юзернейма.")
async def similar(query: str, limit: int = 15) -> str:
    return await _run(["similar", query, "-l", str(int(limit))])


@server.tool(annotations=READONLY, description="Сводка по пользователю: id, оценка регистрации, общие чаты, флаги, статус.")
async def intel(who: str) -> str:
    return await _run(["intel", who])


@server.tool(annotations=READONLY, description="Примерная дата регистрации по user_id (оценка по публичным якорям).")
async def estdate(user: str) -> str:
    return await _run(["estdate", user])


@server.tool(annotations=READONLY, description="Инфа о миниаппе/вебаппе бота: меню-кнопка, команды, ссылки, app settings.")
async def app(bot: str) -> str:
    return await _run(["app", bot])


@server.tool(annotations=READONLY, description="Открыть web view бота: полный URL с токеном, хост и его IP (A/AAAA). platform: android|ios|web.")
async def webview(bot: str, platform: str = "android", start_param: str = "", short_name: str = "",
                  compact: bool = False, fullscreen: bool = False) -> str:
    args = ["webview", bot]
    if short_name:
        args.append(short_name)
    if platform in ("android", "ios", "web"):
        args += ["--platform", platform]
    if start_param:
        args += ["--start-param", start_param]
    if compact:
        args.append("--compact")
    if fullscreen:
        args.append("--fullscreen")
    return await _run(args)


@server.tool(annotations=READONLY, description="t.me-ссылка на чат и/или сообщение.")
async def link(chat: str, id: int = 0) -> str:
    args = ["link", chat]
    if id:
        args.append(str(int(id)))
    return await _run(args)


@server.tool(annotations=NEUTRAL, description="Отправить сообщение в чат. chat: имя/@юзер/id/'me'. button: 'Текст|URL' или 'Текст' (список). Действие меняет состояние!")
async def send(chat: str, text: str, reply_to: int = 0, plain: bool = False, silent: bool = False,
               button: list[str] | None = None) -> str:
    args = ["send", chat, text]
    if plain:
        args.append("--plain")
    if silent:
        args.append("--silent")
    if reply_to:
        args += ["--reply", str(int(reply_to))]
    for b in (button or []):
        args += ["--button", str(b)]
    return await _run(args)


@server.tool(annotations=NEUTRAL, description="Быстрый ответ на сообщение. chat, id — id сообщения, text — ответ. Действие меняет состояние!")
async def reply(chat: str, id: int, text: str) -> str:
    return await _run(["reply", chat, str(int(id)), text])


@server.tool(annotations=NEUTRAL, description="Удалить сообщения (у всех по умолчанию; recover=True — только у себя). ids — список id. Действие меняет состояние!")
async def delete(chat: str, ids: list[int], recover: bool = False, yes: bool = True) -> str:
    args = ["delete", chat, *[str(int(i)) for i in (ids or [])]]
    if recover:
        args.append("--recover")
    if yes:
        args.append("-y")
    return await _run(args)


@server.tool(annotations=NEUTRAL, description="Поставить/убрать реакцию у сообщения. emoji: эмодзи (по умолчанию 👍); 'clear' — убрать. Действие меняет состояние!")
async def react(chat: str, id: int, emoji: str = "👍", big: bool = False) -> str:
    args = ["react", chat, str(int(id)), emoji or "👍"]
    if big:
        args.append("--big")
    return await _run(args)


@server.tool(annotations=NEUTRAL, description="Отметить чат прочитанным. up_to — id до которого читать (0 — всё). Действие меняет состояние!")
async def mark_read(chat: str, up_to: int = 0) -> str:
    args = ["mark", chat]
    if up_to:
        args += ["--up-to", str(int(up_to))]
    return await _run(args)


@server.tool(annotations=NEUTRAL, description="Переслать сообщения в другой чат. to — чат назначения. Действие меняет состояние!")
async def forward(chat: str, ids: list[int], to: str) -> str:
    return await _run(["forward", chat, *[str(int(i)) for i in (ids or [])], "--to", to])


@server.tool(annotations=NEUTRAL, description="Скачать медиа из чата в указанную папку. Только по явной просьбе пользователя.")
async def pull(chat: str, dest: str = "", type: str = "", last: int = 20, dry_run: bool = True) -> str:
    args = ["pull", chat, "-l", str(int(last))]
    if dest:
        args += ["-d", dest]
    if type:
        args += ["--type", str(type)]
    if dry_run:
        args.append("-n")
    return await _run(args)


def main():
    server.run("stdio")


if __name__ == "__main__":
    main()
