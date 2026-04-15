import polib
from deep_translator import GoogleTranslator
import time


def translate_po_file(file_path, target_lang):
    print(f"\n[{target_lang.upper()}] Открываем файл: {file_path}")

    try:
        # Парсим .po файл с помощью polib
        po = polib.pofile(file_path)
    except Exception as e:
        print(f"Ошибка чтения файла: {e}. Проверьте правильность пути.")
        return

    # Настраиваем переводчик с английского на целевой язык (ru или kk)
    translator = GoogleTranslator(source='en', target=target_lang)

    # polib сам находит все строки, где msgstr пустой
    untranslated = po.untranslated_entries()
    total = len(untranslated)

    if total == 0:
        print("Отлично! Все строки уже переведены.")
        return

    print(f"Найдено непереведенных строк: {total}. Начинаем перевод...\n")

    count = 0
    for entry in untranslated:
        original_text = entry.msgid

        # Пропускаем технические пустые строки
        if not original_text.strip():
            continue

        try:
            # Делаем запрос к Google Translate
            translated_text = translator.translate(original_text)

            # Записываем перевод обратно в объект строки
            entry.msgstr = translated_text
            count += 1

            # Выводим прогресс в консоль, чтобы видеть, что скрипт не завис
            print(f"[{count}/{total}] {original_text[:30]}... -> {translated_text[:30]}...")

            # ВАЖНО: Делаем паузу в 0.5 секунды.
            # Если отправлять тысячи запросов без паузы, Google временно заблокирует ваш IP за спам.
            time.sleep(0.5)

        except Exception as e:
            print(f"Ошибка при переводе фразы '{original_text}': {e}")

    # После перевода всех строк сохраняем файл на диск
    po.save()
    print(f"\n[{target_lang.upper()}] Готово! Успешно переведено строк: {count}.")


# --- ЗАПУСК СКРИПТА ---

# 1. Переводим файл для Русского языка
# Укажите точный путь к вашему django.po
translate_po_file('src/locale/ru/LC_MESSAGES/django.po', 'ru')

# 2. Переводим файл для Казахского языка
translate_po_file('src/locale/kk/LC_MESSAGES/django.po', 'kk')