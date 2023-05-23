import json


def save_cases():

    config_data = {
        "cases": [
            {
                "description": "일반적 상황",
                "targetPointCnt": [5, 5, 5, 10, 10],
                "case": [
                    [1.0, 1.5, 2.0, 1.6, 1.0],
                    [1.5, 1.75, 2.0, 1.75, 1.5],
                    [1.75, 1.8, 2.0, 1.8, 1.75],
                    [1.8, 1.85, 1.9, 1.95, 2.0, 1.97, 1.95, 1.9, 1.85, 1.8],
                    [1.95, 1.96, 1.97, 1.98, 1.99, 2.0, 1.99, 1.98, 1.97, 1.96]
                ]
            }, {
                "description": "초점이 상단에 자리함(끝부분)",
                "targetPointCnt": [15, 5, 5, 10, 10],
                "case": [   # 테스트 코드 상 포지션이 앞으로 옮겨진게 구현이 안돼 있으므로 반복이 발생
                    [1.0, 1.2, 1.3, 1.5, 1.6,       # 0
                     1.3, 1.5, 1.6, 1.8, 2.0,
                     1.6, 1.8, 2.0, 1.8, 1.6],
                    [1.6, 1.75, 2.0, 1.75, 1.6],    # 1
                    [1.75, 1.8, 2.0, 1.8, 1.75],    # 2
                    [1.8, 1.85, 1.9, 1.95, 2.0, 1.97, 1.95, 1.9, 1.85, 1.8],    # 3
                    [1.95, 1.96, 1.97, 1.98, 1.99, 2.0, 1.99, 1.98, 1.97, 1.96] # 4
                ]
            }
        ]
    }

    with open("config.json", "w", encoding="utf-8") as config_file:
        json.dump(config_data, config_file, ensure_ascii=False)


def load_case(num=0):
    with open("config.json", "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)["cases"]
        print(config_data[num])

        if num >= 0:
            return config_data[num]
        else:
            return config_data


if __name__ == "__main__":
    save_cases()
    num = 1

    case = load_case(num)

    #for case_num, cases in enumerate(cases):
        #print(f"case{case_num}")
    print(f"case number #{num}")
    print(f"description: {case['description']}")
    print(f"targetPointCnt targetPointCnt: {case['targetPointCnt']}")
    for idx, data in enumerate(case["case"]):
        print(f"case{idx}: {data}")
