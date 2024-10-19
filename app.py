import os, json, asyncio

from dotenv import load_dotenv

from datetime import datetime

from playwright.async_api import async_playwright

from telegram import Bot


load_dotenv(override=True)

BOOKING_URL = os.getenv("BOOKING_URL")
CHECKIN_DATE_STR = os.getenv("CHECKIN_DATE")
CHECKIN_DATE = datetime.strptime(CHECKIN_DATE_STR, "%Y-%m-%d")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


if os.path.exists("booking_data.json"):
    with open("booking_data.json", "r", encoding="utf-8") as f:
        booking_data = json.load(f)
else:
    booking_data = {"status": None}

def save_booking_data(booking_data: dict):
    with open("booking_data.json", "w", encoding="utf-8") as f:
        json.dump(booking_data, f, ensure_ascii=False, indent=4)

def escape_markdown(text: str) -> str:
    escape_chars = r"\_*[]~`>#+-=|{}.!()\""
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def send_telegram_message(message: str):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="MarkdownV2")

async def run(playwright):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        await page.goto(BOOKING_URL)
        
        title = await page.text_content("h1.title .text")
        msg_title = f"[네이버 예약] {title}"
        info_title = await page.text_content(".info_title")
        
        while True:
            calendar_title = await page.text_content(".calendar_title")
            if calendar_title != CHECKIN_DATE.strftime("%Y.%m"):
                await page.click(".btn_next")
            else:
                break
        
        parent_element = None
        elements = await page.query_selector_all('span.num')
        
        for element in elements:
            text = await element.evaluate("node => node.textContent.trim()")
            if text == str(CHECKIN_DATE.day):
                parent_element = await element.evaluate_handle('node => node.parentElement')
                break
        
        if not parent_element:
            print(f"{msg_title} : 날짜를 찾을 수 없음")
            return
        
        parent_class_list = await parent_element.evaluate('node => node.classList.contains("unselectable")')
        if parent_class_list:
            print(f"{msg_title} : 예약 불가능")
            save_booking_data({"status": False})
            
            if booking_data["status"] == False:
                print("이미 메시지가 전송되었습니다.")
                return

            await send_telegram_message(f"""\
*{escape_markdown(msg_title)}* _{escape_markdown(f'({info_title})')}_
`{escape_markdown(CHECKIN_DATE.strftime("%Y년 %-m월 %-d일"))}` 예약 *불가능*
[예약하러 가기]({BOOKING_URL})\
""")
            return
        
        print(f"{msg_title} : 예약 가능")
        save_booking_data({"status": True})
        
        if booking_data["status"] == True:
            print("이미 메시지가 전송되었습니다.")
            return
        
        await send_telegram_message(f"""\
*{escape_markdown(msg_title)}* _{escape_markdown(f'({info_title})')}_
`{escape_markdown(CHECKIN_DATE.strftime("%Y년 %-m월 %-d일"))}` 예약 *가능*
[예약하러 가기]({BOOKING_URL})\
""")
    finally:
        await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
