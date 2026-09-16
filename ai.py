from rubka.asynco import Robot, Message
import asyncio
import aiohttp
import json
import os
import re
import urllib.parse

TOKEN = ""
API_BASE = ""
HISTORY_FILE = "chat_history.json"

bot = Robot(TOKEN)


def load_history(chat_id):
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(chat_id), [])
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_history(chat_id, history):
    data = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass
    data[str(chat_id)] = history
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


ALLOWED_FORMATS = [
    "txt", "py", "html", "css", "js", "json", "xml",
    "md", "csv", "yaml", "yml", "sh", "log", "ini", "svg"
]
DISALLOWED_FORMATS = ["apk", "exe", "zip", "rar", "dll", "bin", "so", "dat", "bat", "cmd"]


SYSTEM_PROMPT = """You are DOCTUR-Mini, a professional coding assistant by TechnoloGia.

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW EXACTLY:

1. Your ONLY job is to output PURE JSON. Nothing else. No text before or after.
2. NEVER use markdown code blocks like ```json or ```
3. NEVER add any explanation outside the JSON
4. The JSON must be valid and parseable
5. Do NOT escape the JSON with backslashes

REQUIRED JSON FORMAT (copy this structure exactly):
{
  "response_type": "text",
  "message": "Your complete answer in Persian/English with 🍂🧡 emojis only",
  "file_name": null,
  "file_content": null
}

OR if creating a file:
{
  "response_type": "file",
  "message": "Explanation of the file in Persian/English with 🍂🧡 emojis",
  "file_name": "example.py",
  "file_content": "The actual code content here"
}

RULES:
- response_type: MUST be exactly "text" or "file"
- message: Your answer with ONLY 🍂🧡 emojis
- file_name: filename with extension (like "test.py") OR null
- file_content: raw code/content OR null
- Use ONLY double quotes for JSON strings
- Escape special characters in strings properly

START YOUR RESPONSE WITH { and END WITH }
NO OTHER TEXT ALLOWED."""


@bot.on_message()
async def ai_flow(bot: Robot, message: Message):
    chat_id = message.chat_id
    text = message.text.strip()

    if text == "/start":
        await bot.send_message(
            chat_id=chat_id,
            text="**🍂🧡 سلام! من DOCTUR-Mini، دستیار هوش مصنوعی شما هستم. من می‌توانم ۱۵ پیام اخیر مکالمه را به خاطر بسپارم. برای بازنشانی کامل حافظه از دستور `/DelHistory` استفاده کنید. اگر حافظه بازنشانی نشود، پس از هر ۱۶ پیام، ۱۵ پیام قدیمی حذف و مکالمات جدید جایگزین می‌شوند. 🧡🍂**"
        )
        save_history(chat_id, [])
        return

    if text.lower() == "/delhistory":
        save_history(chat_id, [])
        await bot.send_message(
            chat_id=chat_id,
            text="**🍂🧡 حافظه مکالمه (تاریخچه ۱۵ پیام اخیر) با موفقیت بازنشانی شد. 🧡🍂**"
        )
        return

    if "." in text and re.match(r"^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$", text):
        try:
            file_format = text.rsplit(".", 1)[1].lower()
            if file_format in DISALLOWED_FORMATS:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"**🍂🧡 متاسفم، ساخت فایل با فرمت `{file_format}` امکان‌پذیر نیست. 🧡🍂**"
                )
                return

            if file_format in ALLOWED_FORMATS:
                await bot.send_message(
                    chat_id=chat_id,
                    text="**🍂🧡 لطفاً سوال خود را بپرسید تا هوش مصنوعی فایل مورد نیاز را (در صورت نیاز) تولید کند. 🧡🍂**"
                )
                return

        except:
            pass

    if text:
        abuse_keywords = ["برنامه بساز", "اپلیکیشن", "هک", "ویروس", "بدافزار", "برنامه کامل", "پروژه بزرگ", "برنامه نویسی"]
        if any(k in text for k in abuse_keywords):
            await bot.send_message(
                chat_id=chat_id,
                text="**🍂🧡 تیم تکنولوجیا درحال ساخت این قابلیت هست. فقط کدهای ابتدایی در نسخه Mini قابل ساخت است. 🧡🍂**"
            )
            return

        sent = await bot.send_message(chat_id=chat_id, text="••••")

        frames = ["••••", "•••", "••", "•", "•", "••", "•••", "••••"]
        frame_index = 0
        answer_data = None
        error_occurred = False
        history = load_history(chat_id)

        async def call_api():
            nonlocal answer_data, error_occurred
            try:
                parts = [SYSTEM_PROMPT, ""]
                for msg in history[-10:]:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    parts.append(f"{role}: {msg.get('content', '')}")
                parts.append(f"User: {text}")
                parts.append("")
                parts.append("Remember: Output ONLY valid JSON with no markdown, no extra text. Start with { and end with }")
                parts.append("Assistant:")

                full_prompt = "\n".join(parts)
                url = f"{API_BASE}?{urllib.parse.urlencode({'chat': full_prompt})}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=90)
                    ) as resp:
                        if resp.status != 200:
                            error_occurred = True
                            answer_data = {
                                "response_type": "text",
                                "message": f"**🍂🧡 مشکل فنی در سرور رخ داد. (کد: {resp.status}). لطفاً بعداً امتحان کنید. 🧡🍂**",
                                "file_name": None,
                                "file_content": None
                            }
                            return

                        data = await resp.json(content_type=None)

                        if not data.get("success"):
                            error_occurred = True
                            answer_data = {
                                "response_type": "text",
                                "message": "**🍂🧡 سرور پاسخ ناموفق برگرداند. لطفاً دوباره تلاش کنید. 🧡🍂**",
                                "file_name": None,
                                "file_content": None
                            }
                            return

                        raw_response = (data.get("reply") or "").strip()

                        if not raw_response:
                            error_occurred = True
                            answer_data = {
                                "response_type": "text",
                                "message": "**🍂🧡 پاسخی از سرور دریافت نشد. 🧡🍂**",
                                "file_name": None,
                                "file_content": None
                            }
                            return

                        try:
                            raw_response = re.sub(r'```json\s*', '', raw_response)
                            raw_response = re.sub(r'```\s*', '', raw_response)

                            start_idx = raw_response.find('{')
                            end_idx = raw_response.rfind('}')

                            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                                raise ValueError("No valid JSON found in response")

                            clean_json = raw_response[start_idx:end_idx + 1]
                            answer_data = json.loads(clean_json)

                            if "response_type" not in answer_data or "message" not in answer_data:
                                raise ValueError("Invalid JSON structure")

                            if "file_name" not in answer_data:
                                answer_data["file_name"] = None
                            if "file_content" not in answer_data:
                                answer_data["file_content"] = None

                        except (json.JSONDecodeError, ValueError, KeyError) as e:
                            error_occurred = True
                            answer_data = {
                                "response_type": "text",
                                "message": f"**🍂🧡 متأسفانه پاسخ هوش مصنوعی قابل پردازش نبود. خطا: {str(e)[:100]}\n\nلطفاً سوال را ساده‌تر بپرسید یا مجدداً تلاش کنید. 🧡🍂**",
                                "file_name": None,
                                "file_content": None
                            }

            except asyncio.TimeoutError:
                error_occurred = True
                answer_data = {
                    "response_type": "text",
                    "message": "**🍂🧡 زمان انتظار تمام شد. لطفاً دوباره تلاش کنید. 🧡🍂**",
                    "file_name": None,
                    "file_content": None
                }
            except Exception as e:
                error_occurred = True
                answer_data = {
                    "response_type": "text",
                    "message": f"**🍂🧡 خطای ناگهانی: {str(e)[:100]}. لطفاً چند لحظه دیگر امتحان کنید. 🧡🍂**",
                    "file_name": None,
                    "file_content": None
                }

        async def animate_loading():
            nonlocal frame_index
            while answer_data is None and not error_occurred:
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent.message_id,
                        text=frames[frame_index]
                    )
                except:
                    pass
                frame_index = (frame_index + 1) % len(frames)
                await asyncio.sleep(0.5)

        api_task = asyncio.create_task(call_api())
        animation_task = asyncio.create_task(animate_loading())

        await api_task

        if not animation_task.done():
            animation_task.cancel()

        try:
            await bot.delete_message(chat_id=chat_id, message_id=sent.message_id)
        except:
            pass

        if answer_data:
            if not error_occurred:
                history.append({"role": "user", "content": text})
                assistant_msg = answer_data.get("message", "پاسخ")[:500]
                history.append({"role": "assistant", "content": assistant_msg})
                save_history(chat_id, history[-15:])

            await bot.send_message(
                chat_id=chat_id,
                text=answer_data.get("message", "**🍂🧡 خطای نامشخص در پاسخ. 🧡🍂**")
            )

            if (answer_data.get("response_type") == "file" and
                answer_data.get("file_content") and
                answer_data.get("file_name")):

                file_name = answer_data["file_name"]
                file_content = answer_data["file_content"]

                file_format = file_name.rsplit(".", 1)[1].lower() if "." in file_name else "txt"
                if file_format in DISALLOWED_FORMATS:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"**🍂🧡 فایل با فرمت `{file_format}` تولید شد، اما به دلایل امنیتی ارسال نمی‌شود. 🧡🍂**"
                    )
                    return

                try:
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(file_content)

                    await bot.send_document(chat_id=chat_id, path=file_name)
                    os.remove(file_name)

                except Exception as e:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"**🍂🧡 خطا در ساخت/ارسال فایل: {str(e)[:100]} 🧡🍂**"
                    )


async def main():
    try:
        print("🍂🧡 DOCTUR-Mini Bot Started! 🧡🍂")
        await bot.run()
    except KeyboardInterrupt:
        print("\n🍂🧡 Bot Stopped! 🧡🍂")
    except Exception as e:
        print(f"❌ Critical Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
