# tgu — Telegram из терминала

Удобный CLI-клиент Telegram для Termux/Linux на базе **Telethon**.
Один файл, без обвязки. Первым запуском логинишься — дальше пользуешься
аккаунтом через простые команды.

## Установка

```sh
cd ~/projects/tgu
./install.sh        # симлинк в $PREFIX/bin → команда `tgu` доступна везде
```

Зависимость `telethon` уже установлена в этом окружении.
Если нет: `pip install telethon`.

## Первый запуск (вход в аккаунт)

```sh
tgu login
```

Спросит **api_id / api_hash** (олучить на https://my.telegram.org →
"API development tools"), затем телефон, код из Telegram и пароль 2FA.
Их можно и не вводить руками: передать `--api-id/--api-hash` или
переменные окружения `TG_API_ID` / `TG_API_HASH`.

Сессия хранится в `~/.config/tgu/` (сессия + config.json).
Проверка: `tgu status` · Выход: `tgu logout`.

## Адресат чата

Везде, где нужен `<chat>`, можно писать **что угодно из**:
- часть имени чата/контакта (поиск по списку чатов: `Друзья`, `Работа`);
- `@username`;
- числовой id (`123456`);
- `t.me`-ссылку (в т.ч. инвайт-ссылки);
- `me` / `избранное` — Saved Messages (сам себе).

## Команды

| Команда | Что делает |
|---|---|
| `tgu login` / `logout` / `status` | вход / выход / статус авторизации |
| `tgu me` | инфа о себе |
| `tgu user <кто>` | профиль пользователя/канала/группы |
| `tgu contacts` | контакты |
| `tgu chats` | список чатов (непрочитанные, типы, превью) |
| `tgu read <chat>` | читать сообщения (фильтры: кто, текст, даты, медиа) |
| `tgu search <текст> [--chat CH]` | поиск (без `--chat` — по всем чатам) |
| `tgu send <chat> текст` | отправить (markdown по умолч., `--plain`/`--html`) |
| `tgu send <chat> текст --button` | + кнопки: `--button "Сайт\|https://..."` или `--button "Меню"` |
| `tgu send <chat> --file f` | отправить файл (с `--photo` — как фото, тоже можно `--button`) |
| `tgu click <chat> <id> <кнопка>` | нажать кнопку (номер от 0 или текст; reply-кнопка → отправит её текст) |
| `tgu reply <chat> <id> текст` | ответить на сообщение |
| `tgu edit <chat> <id> текст` | отредактировать своё сообщение |
| `tgu delete <chat> [id...]` | удалить (`--last N`, `--mine`, `--recover`) |
| `tgu push <chat> файлы` | отправить файлы документами |
| `tgu pull <chat>` | скачать медиа/файлы (`--type`, `--dest`, `--dry-run`) |
| `tgu forward <chat> id --to CH` | переслать |
| `tgu mark <chat>` | отметить прочитанным |
| `tgu pin/unpin <chat> [id]` | закрепить/открепить |
| `tgu config [ключ] [знач]` | настройки (напр. `download_dir`) |

Короткие алиасы: `ls`=chats, `r`=read, `s`/`msg`=send, `msgs`=read,
`upload`=push, `download`/`dl`=pull, `rm`=delete, `fw`=forward.

### Фильтры чтения и скачивания (read / pull)

```
-l, --last N      сколько последних (по умолчанию 20)
-a, --all         все
--ids ID...       конкретные сообщения
-f, --from NAME   от кого: @user, id или часть имени
-m, --mine        только свои; --incoming — только чужие
--search TEXT     текст внутри чата (серверно)
-s, --since WHEN  с даты: 2026-10-22, '2026-10-22 10:00', 3d, 2w, 5ч, yesterday
-u, --until WHEN  до даты
-t, --type TYPE   photo/video/doc/voice/audio/gif/round/url/sticker
--json            машинный вывод
--ids-only        только id (удобно пайпить в delete/forward)
```

### Примеры

```sh
tgu chats --unread                          # чаты с непрочитанными
tgu chats --type c --limit 100              # каналы
tgu read Друзья -l 30                       # последние 30 сообщений
tgu read "Работа" --from @vasya --since 3d  # от Васи за 3 дня
tgu read me -l 5                            # избранное
tgu read Друзья --type photo --ids-only     # id сообщений с фото
tgu send Друзья Привет! Как дела?           # просто текст
echo "длинное сообщение" | tgu send Друзья  # из stdin (Ctrl+D)
tgu send Друзья --file foto.jpg --photo     # фото со сжатием
tgu push Друзья file1.pdf file2.zip -c "доки по проекту"
tgu pull Друзья --type photo -l 50          # скачать фото
tgu pull Друзья --since yesterday -d ~/dl   # → в ~/dl
tgu pull Работа --type doc --all            # все документы чата
tgu search встреча --chat Работа -l 10      # поиск в чате
tgu search "руководство" --deep             # по всем чатам
tgu user @durov                             # профиль
tgu click "Бот" 123 Подписаться             # нажать кнопку (или по номеру: 0)
tgu send Друзья Привет! --button "Сайт|https://example.com"  # с inline-кнопкой
tgu send Друзья "Выдели меня" --button "Да" --button "Нет"   # reply-кнопки
tgu delete Друзья 1234 1235 --mine -y       # удалить свои
tgu forward Работа 1234 --to Друг           # переслать
tgu mark Друзья                             # всё прочитано
```

### Настройки

```sh
tgu config                       # показать всё
tgu config download_dir /путь    # куда складывать pull (по умолчанию ~/tgu-downloads)
```

Безопасность: сессия — обычный Telethon-логин, сервер ничего не видит
стороннего; выход делает `tgu logout` (удаляет сессию и на сервере).
