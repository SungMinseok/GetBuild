import csv
import os
from datetime import datetime

def export_upload_result(aws_link, full_build_name, option=None, result=None):
    """
    커스텀 업로드 완료 시 결과를 CSV로 저장/업데이트하는 함수.
    aws_link: 전체 URL (예: https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2)
    full_build_name: 빌드명
    option: 작업 종류 (client_copy, server_copy, all_copy, aws_upload, aws_apply, make_build, test)
    result: 작업 결과 (pass, loading, fail)
    """

    # 오늘 날짜로 파일명 생성 (예: getbuild_result_250728.csv)
    today_str = datetime.now().strftime("%y%m%d")
    csv_path = f"getbuild_result_{today_str}.csv"

    # 모든 옵션 열
    option_fields = ["client_copy", "server_copy", "all_copy", "aws_upload", "aws_apply", "make_build", "test"]

    # 현재 시각
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # result 값 변환
    result_map = {
        "pass": ":update_done:",
        "loading": ":loading:",
        "fail": ":failed:"
    }
    result_final = result_map.get(result, result)

    # 기본 row 데이터 (옵션 필드 없음)
    row_data = {
        "time": now_str,
        "aws_link": aws_link,
        "build_name": full_build_name,
    }
    # 옵션/결과 반영
    if option in option_fields and result_final:
        row_data[option] = result_final

    rows = []
    updated = False
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8", newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["aws_link"] == aws_link:
                    # 기존 row 업데이트
                    row["time"] = now_str
                    row["build_name"] = full_build_name
                    if option in option_fields and result:
                        row[option] = result
                    # 없는 옵션 필드는 빈 값으로 맞춰줌
                    for field in option_fields:
                        if field not in row:
                            row[field] = ""
                    updated = True
                rows.append(row)
    if not updated:
        rows.append(row_data)

    # slack 열 추가 (맨 뒤)
    for row in rows:
        # aws_apply 값이 없으면 빈 문자열
        aws_apply_val = row.get("aws_apply", "")
        # aws_link에서 마지막 슬래시 뒤 부분만 추출
        aws_link_last = row.get("aws_link", "").rstrip('/').split('/')[-1]
        row["slack"] = f'{aws_link_last}: {row.get("build_name", "")} {aws_apply_val}'

    # 헤더 정의 (time이 맨 앞, slack이 맨 뒤)
    fieldnames = ["time", "aws_link", "build_name"] + option_fields + ["slack"]

    with open(csv_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)