import os
import html
import re
import smtplib
import requests

from google import genai
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("Naver News 수집합니다.")

url = "https://www.hankyung.com/economy/1073"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, 'html.parser')
# print(soup)
collected_headlines = []

def clean_text(value):
    """기사 제목의 HTML 태그와 특수문자 제거"""
    value = re.sub(r"<[^>]*>", "", value)
    return html.unescape(value).strip()


if soup:
    news_tag_2 = soup.find_all('p', class_='lead')
    for i, tags in enumerate(news_tag_2[:10], start=1):
        headline = tags.get_text(strip=True)
        collected_headlines.append(headline)

else:
    print("대형 섹션 상자를 찾을 수 없습니다. 클래스 명을 재확인 해주세요.")


if soup:
    news_tag_1 = soup.find_all('a', class_='news-tit')
    for i, tags in enumerate(news_tag_1[:10], start=1):
        headline = tags.get_text(strip=True)
        collected_headlines.append(headline)

else:
    print("대형 섹션 상자를 찾을 수 없습니다. 클래스 명을 재확인 해주세요.")


news_data = "\n".join(collected_headlines, )


api_key = os.environ.get("GEMINI_API_KEY") 
client = genai.Client(api_key = api_key)


prompt = f"""
당신은 최고의 국제 경제 및 시장 전문가 입니다.
아래 제공된 구글 뉴스 검색 결과를 바탕으로, 고등학생과 성인이 이해하기 쉽게 한글로
핵심 요약 보고서를 만들어주세요.

[뉴스데이터]
{news_data}

[작성규칙]
1. 친근하고 쉬운 말투(~요, ~습니다)를 사용 해주세요.
2. 통신 사업 시장의 핵심 포인트가 무엇인지, 앞으로 일론머스크 도전은 어떻게 이뤄지는지 요약해 주세요.
"""

try:
    response = client.models.generate_content(
        model = 'gemini-3.5-flash',
        contents = prompt,
    )

except Exception as e:
    print(f"구글 서버와 연결이 끊어졌습니다: {e}")

ai_summary = response.text
print(response.text)
sender_email = os.environ.get("SENDER_EMAIL") 
app_password = os.environ.get("GMAIL_APP_PASSWORD") 
receiver_email = sender_email

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["subject"] = '[AI News_Contents] 오늘의 뉴스 요약 브리핑'


message.attach(MIMEText(ai_summary, "plain", "utf-8"))
print(sender_email, app_password)

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("이메일이 성공적으로 발송되었습니다. 메일함을 확인해주세요!")


except Exception as e:
    print(f"메일 발송 중 오류 발생했습니다: {e}")
