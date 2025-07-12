import smtplib

# 내 네이버 이메일 계정
my_email = "#"
password = "#"

# 서비스 제공자마다 smtp 서버주소 상이 (parameter에 이메일 제공자마다 다른 SMTP주소 넣음)
with smtplib.SMTP("smtp.naver.com", 587) as connection:
    # starttls에서 tls는 Transport Layer Security의 약자이고, 이메일 서버와의 연결을 안전하게 만드는 방식(보안을 위한 코드라인)
    connection.starttls()
    connection.login(user=my_email, password=password)
    connection.sendmail(from_addr=my_email, 
                        to_addrs="skylike4u@gmail.com", 
                        msg="Subject:Test Mail\n\nHello from Python"
                        )

# the positivity blog(동기부여 명언) : https://www.positivityblog.com/

# import datetime as dt

# now = dt.datetime.now()
# year = now.year
# month = now.month
# day_of_week = now.weekday()
# print(day_of_week)

# date_of_birth = dt.datetime(year=1983, month=1, day=24, hour=4)
# print(date_of_birth)