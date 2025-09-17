import matplotlib.pyplot as plt
import json
from lunar_python import Solar
from datetime import datetime
import pytz
import pandas as pd
from statistics import mean

# 五行映射
STEM_TO_ELEMENT = {
    "甲": "木", 
    "乙": "木",
    "丙": "火", 
    "丁": "火",
    "戊": "土", 
    "己": "土",
    "庚": "金", 
    "辛": "金",
    "壬": "水", 
    "癸": "水",
}

# 地支藏干 + 权重
BRANCH_HIDDEN_STEMS = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.7), ("癸", 0.2), ("辛", 0.1)],
    "寅": [("甲", 0.7), ("丙", 0.2), ("戊", 0.1)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.7), ("乙", 0.2), ("癸", 0.1)],
    "巳": [("丙", 0.7), ("庚", 0.2), ("戊", 0.1)],
    "午": [("丁", 0.8), ("己", 0.2)],
    "未": [("己", 0.8), ("丁", 0.2), ("乙", 0.1)],
    "申": [("庚", 0.7), ("壬", 0.2), ("戊", 0.1)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.7), ("辛", 0.2), ("丁", 0.1)],
    "亥": [("壬", 0.8), ("甲", 0.2)],
}

# 每个地支 → 每个五行 → 状态
SEASON_TABLE = {
    "寅": {"木": "旺", "火": "相", "土": "休", "金": "囚", "水": "死"},
    "卯": {"木": "旺", "火": "相", "土": "休", "金": "囚", "水": "死"},
    "辰": {"木": "余", "火": "旺", "土": "相", "金": "休", "水": "囚"},
    "巳": {"火": "旺", "土": "相", "木": "休", "金": "囚", "水": "死"},
    "午": {"火": "旺", "土": "相", "木": "休", "金": "囚", "水": "死"},
    "未": {"土": "旺", "火": "相", "木": "休", "金": "囚", "水": "死"},
    "申": {"金": "旺", "水": "相", "土": "休", "木": "囚", "火": "死"},
    "酉": {"金": "旺", "水": "相", "土": "休", "木": "囚", "火": "死"},
    "戌": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    "亥": {"水": "旺", "木": "相", "金": "休", "火": "囚", "土": "死"},
    "子": {"水": "旺", "木": "相", "金": "休", "火": "囚", "土": "死"},
    "丑": {"土": "旺", "金": "相", "水": "休", "木": "囚", "火": "死"},
}

ELEMENT_TRANSLATION = {
        "木": "wood",
        "火": "fire",
        "土": "earth",
        "金": "metal",
        "水": "water"
    }

# 五行能量强度调整
STATE_WEIGHTS = {
    "旺": 1.3,   # 旺季：+30%
    "相": 1.15,  # 相：+15%
    "余": 1.05,  # 有余气：+5%
    "休": 1.0,   # 休：保持不变
    "囚": 0.85,  # 囚：-15%
    "死": 0.7    # 死：-30%
}

POSITION_WEIGHTS = {
        "年干": 0.5,
        "年支": 0.5,
        "月干": 1.5,
        "月支": 3.5,   # 月令最重要
        "日干": 1.5,
        "日支": 1.5,
        "时干": 1.0,
        "时支": 1.0,
}

""" # 日主旺衰倾向修正
STATE_SCORE = {
    "旺": 1,
    "相": 1,
    "余": 0.5,
    "休": 0,
    "囚": -1,
    "死": -1
} """


GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # 我生

OVERCOME = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # 我克

MOTHER = {v: k for k, v in GENERATE.items()}  # 生我

RESTRAIN = {v: k for k, v in OVERCOME.items()}  # 克我

# 五行阴阳
STEM_POLARITY = {
    "甲":"阳","乙":"阴",
    "丙":"阳","丁":"阴",
    "戊":"阳","己":"阴",
    "庚":"阳","辛":"阴",
    "壬":"阳","癸":"阴",
}

# ten-god english translations (optional)
TEN_GOD_TRANSLATION = {
    "比肩":"BiJian", "劫财":"JieCai",
    "伤官":"ShangGuan", "食神":"ShiShen",
    "偏印":"PianYin", "正印":"ZhengYin",
    "七杀":"QiSha", "正官":"ZhengGuan",
    "偏财":"PianCai", "正财":"ZhengCai",
}

def calc_bazi(data):
    birth = data["birth"]
    time = data["time"]
    tz_str = data["tz"]

    year, month, day = map(int, birth.split("-"))
    hour, minute = map(int, time.split(":"))

    local_tz = pytz.timezone(tz_str)
    beijing_tz = pytz.timezone("Asia/Shanghai")
    dt_local = local_tz.localize(datetime(year, month, day, hour, minute))
    dt_bj = dt_local.astimezone(beijing_tz)

    solar = Solar.fromYmdHms(
        dt_bj.year, dt_bj.month, dt_bj.day, dt_bj.hour, dt_bj.minute, dt_bj.second)
    lunar = solar.getLunar()

    pillars = {
        "年柱": lunar.getYearInGanZhi(),
        "月柱": lunar.getMonthInGanZhi(),
        "日柱": lunar.getDayInGanZhi(),
        "时柱": lunar.getTimeInGanZhi(),
    }



    explanation = []
    explanation.append(f"出生日期当地时区为 = {datetime(year, month, day, hour, minute)}, 该数据信息不会被系统所保留，退出页面后自动删除。")
    explanation.append(f"对应八字年柱为: {pillars['年柱']}, 月柱为: {pillars['月柱']}, 日柱为: {pillars['日柱']}, 时柱为: {pillars['时柱']}。")
    bazi_exp = "\n".join(explanation)

    result = {
        "local_tz": tz_str,
        "beijing_tz": dt_bj,
        "fourPillars": pillars,
        "dayMaster": lunar.getDayGan(),
        "bazi_explanation": bazi_exp
    }

    return result   


def five_elements(pillars,day_master):
    # 五行得分
    elements_score = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    pillars_elements_str = []  # 每柱的五行表示

    for pos, p in pillars.items():
        gan, zhi = p[0], p[1]

        # 记录天干对应的五行
        gan_elem = STEM_TO_ELEMENT[gan] 

        # 天干直接加 1.0
        elements_score[STEM_TO_ELEMENT[gan]] += 1.0
        elements_score[gan_elem] += POSITION_WEIGHTS[pos[0] + "干"] # 根据天干位置调整得分
     
        # 地支藏干记录
        zhi_elems = [STEM_TO_ELEMENT[hidden_gan] for hidden_gan, _ in BRANCH_HIDDEN_STEMS[zhi]]

        zhi_elem_str = "".join(zhi_elems)
 
        # 地支藏干加权 根据权重表“地支藏干 + 权重”
        for hidden_gan, weight in BRANCH_HIDDEN_STEMS[zhi]:
            hidden_elem = STEM_TO_ELEMENT[hidden_gan]
            elements_score[hidden_elem] += weight * POSITION_WEIGHTS[pos[0] + "支"] # 根据地支位置调整得分

        # 生成展示字符串，比如 "辛巳 → 辛(金) + 巳(火土金)"
        pillar_str = f"{gan}({gan_elem}) + {zhi}({zhi_elem_str})"
        pillars_elements_str.append(pillar_str)


    #elements_score_eng = {f"{cn} {ELEMENT_TRANSLATION[cn]}": val 
          #for cn, val in elements_score.items()}
    

    # 根据月令调整五行得分
    month_branch = pillars["月柱"][1]  # 月柱地支
    season_state = SEASON_TABLE[month_branch]  # 获取当月旺衰状态表
    adjusted_score = {}
    state_record = {}   # 记录每个五行的状态
    for elem, score in elements_score.items():
        state = season_state[elem]             # 该五行在月令的状态
        state_record[elem] = state

        weight = STATE_WEIGHTS[state]    # 状态对应的修正系数 "旺": 1.3, "相": 1.15, "余": 1.05, "休": 1.0, "囚": 0.85, "死": 0.7
        adjusted_score[elem] = round(score * weight, 3)
 
    #adjusted_score_eng = {f"{cn} {ELEMENT_TRANSLATION[cn]}": val 
    #      for cn, val in adjusted_score.items()}

    
    explanation = []
    explanation.append(
    f"八字的五行（天干+地支）为: " + ", ".join(pillars_elements_str) + "。"
    f"根据月令（月柱地支）对应的五行状态为: "
    + " ".join([f"{k}={v}" for k, v in state_record.items()]) + "。"
    )

    score_explanation = []
    score_explanation.append(
    f"在五行强弱的具体分布上，未经过月令调整的五行得分为: "
    + " ".join([f"{k} = {round(v, 2)}" for k, v in elements_score.items()]) + "。"
    f"而经过月令调整后，五行得分变为: "
    + " ".join([f"{k} = {round(v, 2)}" for k, v in adjusted_score.items()]) + "。"
    f"这一调整反映了月令对五行力量的修正，使整体格局更贴近实际情况。"
    )

    fiveElement_exp = "\n".join(explanation)
    fiveElement_score_exp = "\n".join(score_explanation)

    result = {
        "fiveElementsScore": elements_score,
        #"fiveElementsScore_eng": elements_score_eng,
        "fiveElementsScore_adjusted": adjusted_score, 
        #"fiveElementsScore_adjusted_eng": adjusted_score_eng,
        "fiveElementsState": state_record,
        "pillarsElements_str": pillars_elements_str,
        "fiveElement_explanation": fiveElement_exp,
        "fiveElement_score_explanation": fiveElement_score_exp

    }
    return result

def judge_strength(dayMaster, fiveElementsScore_adjusted, fiveElementsState):
    dayElement = STEM_TO_ELEMENT[dayMaster]

    # 日主状态
    dayElement_state = fiveElementsState[dayElement]
    #dayElement_score = STATE_SCORE[dayElement_state]
    
    # 力量分数
    same_score   = fiveElementsScore_adjusted[dayElement]        # 比劫 (同我)  属木的话看木
    helper_score = fiveElementsScore_adjusted[MOTHER[dayElement]]# 印星 (生我) 属木的话看水
    leak_score   = fiveElementsScore_adjusted[GENERATE[dayElement]] # 食伤 (我生) 属木的话看火
    drain_score  = fiveElementsScore_adjusted[OVERCOME[dayElement]] # 财星 (我克) 属木的话看土
    enemy_score  = fiveElementsScore_adjusted[RESTRAIN[dayElement]]   # 官杀 (克我) 属木的话看金

    stars_strength = {
        "比劫": same_score,
        "印星": helper_score,
        "食伤": leak_score,
        "财星": drain_score,
        "官杀": enemy_score
    }

    # 总结
    power = round(same_score + helper_score, 3)
    resistance = round(leak_score + drain_score + enemy_score,3)

    explanation = []
    #explanation.append(f"日主五行为 {dayElement}, 状态为 {dayElement_state}")
    explanation.append(f"比劫 = {same_score}")
    explanation.append(f"印星 = {helper_score}")
    explanation.append(f"总结：助力合计 = {same_score} + {helper_score} = {power}")
    explanation.append(f"食伤 = {leak_score}")
    explanation.append(f"财星 = {drain_score}")
    explanation.append(f"官杀 = {enemy_score}")
    explanation.append(f"总结：克泄合计 = {leak_score} + {drain_score} + {enemy_score} = {resistance}")


    if power > resistance * 1.5:
        strength = "身强"
        explanation.append(f"因为 助力 {power} 明显大于 克泄 {resistance}，所以日主偏强。")
    elif resistance > power:
        strength = "身弱"
        explanation.append(f"因为 克泄 {resistance} 明显大于 助力 {power}，所以日主偏弱。")
    else:
        strength = "中和"
        explanation.append(f"因为 助力 {power} 与 克泄 {resistance} 接近，所以日主中和。")

    strength_exp = "\n".join(explanation)
    result = {"dayElement": dayElement, "dayElement_state": dayElement_state, "strength": strength, "stars_strength": stars_strength, "strength_explanation": strength_exp}

    return result

def get_ten_god(dayMaster, other_gan):
    """
    Return the ten-god (Chinese) name for 'other_gan' relative to 'dayMaster'.
    Deterministic based on five-element relation and yin/yang.
    用来计算十神的一个中间步骤，比对日干和其他天干的关系，根据阴阳和五行生克来决定。
    """
    if dayMaster not in STEM_TO_ELEMENT or other_gan not in STEM_TO_ELEMENT:
        return None  # invalid stems

    if dayMaster == other_gan:
        # same exact stem: treat as same-element with same polarity => 比肩
        # (if you want to mark the day pillar itself, you can return "日主" externally)
        return "比肩"

    day_elem = STEM_TO_ELEMENT[dayMaster]
    other_elem = STEM_TO_ELEMENT[other_gan]
    day_pol = STEM_POLARITY[dayMaster] # 日干阴阳
    other_pol = STEM_POLARITY[other_gan] # 其他天干阴阳

    # 日干天干相同
    if other_elem == day_elem:
        return "比肩" if other_pol == day_pol else "劫财"

    # 日干 生 其他天干  => 食神/伤官
    if GENERATE[day_elem] == other_elem:
        return "食神" if other_pol == day_pol else "伤官"

    # 其他天干 生 日干 => 正印/偏印
    if GENERATE[other_elem] == day_elem:
        return "偏印" if other_pol == day_pol else "正印"

    # 其他天干 克 日干 => 七杀/正官
    if OVERCOME[other_elem] == day_elem:
        return "七杀" if other_pol == day_pol else "正官"

    # 日干 克 其他天干 => 偏财/正财
    if OVERCOME[day_elem] == other_elem:
        return "偏财" if other_pol == day_pol else "正财"

    # fallback (should not happen)
    return None


def ten_gods(fourPillars, dayMaster, gender=None):

    # 初始化 summary 统计表
    tg_summary = {tg: 0 for tg in TEN_GOD_TRANSLATION.keys()}

    # 构造表格（两行四列）
    tg_table = {
        "年柱": {"天干": "", "地支": ""},
        "月柱": {"天干": "", "地支": ""},
        "日柱": {"天干": "", "地支": ""},
        "时柱": {"天干": "", "地支": ""},
    }

    ten_gods = {}
    for pos, pillar in fourPillars.items():
        gan, zhi = pillar[0], pillar[1] #天干和地支

        if pos == "日柱":
            if gender:
                tg = f"元{gender}"
            else:
                tg = "日主"
        else:
            tg = get_ten_god(dayMaster, gan)

        # 更新统计（天干默认权重 1.0）
        if tg in tg_summary:
            tg_summary[tg] += 1.0

        tg_table[pos]["天干"] = tg  # 天干行

        # 地支藏干十神
        hidden_list = [] #某一个柱下面的地支藏干列表
        hidden_strs = [] #只记录十神 拼在一起 放在table的一个格子里
        for hidden_gan, weight in BRANCH_HIDDEN_STEMS[zhi]: #每个柱有n个地支藏干（1-3个）权重不一
            hidden_tg = get_ten_god(dayMaster, hidden_gan) #某一个柱下面的地支藏干的十神
            hidden_list.append({
                "hidden_gan": hidden_gan,
                "ten_god": hidden_tg,
                "weight": weight
            })
            hidden_strs.append(f"{hidden_tg}({weight})") 


            # 更新统计
            if hidden_tg in tg_summary:
                tg_summary[hidden_tg] += weight

        ten_gods[pos] = {"天干": gan, "天干十神": tg, "地支藏干":hidden_list} #举例：年柱的天干和对应的十神 和 地支藏干列表对应的十神
        tg_table[pos]["地支"] = "; ".join(hidden_strs)  # 地支行

    # 转换为 DataFrame 方便展示
    tg_table_df = pd.DataFrame(tg_table)


    # 保存统计结果
    result = {
        "tenGods": ten_gods,
        "tenGodsTable": tg_table_df,
        "tenGodsSummary": tg_summary
    }

    return result

def suggest_five_elem(dayMaster, strength, stars_strength, fiveElementsScore_adjusted):
    """
    纯五行角度的喜用神推荐
    """
    day_elem = STEM_TO_ELEMENT[dayMaster]

    suggestion_lines = []

    # 找出最弱和最强的两个五行
    min_elem = min(fiveElementsScore_adjusted, key=fiveElementsScore_adjusted.get)
    max_elem = max(fiveElementsScore_adjusted, key=fiveElementsScore_adjusted.get)

    if strength == "身强":
        favored = [RESTRAIN[day_elem], GENERATE[day_elem]]
        unfavored = [day_elem, MOTHER[day_elem]]
        suggestion_lines.append("日主偏强，应以制衡和泄耗为主。")
        suggestion_lines.append(f"日主不弱，财星（{OVERCOME[day_elem]}）为喜。")
        if stars_strength["财星"] <= mean(stars_strength.values()) * 0.1:
            suggestion_lines.append(f"财星（{OVERCOME[day_elem]}）在命局中较弱，宜补财星。")
            favored.append(OVERCOME[day_elem])
        if stars_strength["印星"] > stars_strength["比劫"]:
            suggestion_lines.append(f"印星（{MOTHER[day_elem]}）在命局中过旺，导致财星被压制，宜补财星。")
            favored.append(OVERCOME[day_elem])

        favored = list(set(favored))
        unfavored = list(set(unfavored))
        suggestion_lines.append(f"喜用神五行为: {' '.join(favored)}。")
        suggestion_lines.append(f"忌用神五行为: {' '.join(unfavored)}。")
        
    elif strength == "身弱":
        favored = [day_elem, MOTHER[day_elem]]
        unfavored = [RESTRAIN[day_elem], GENERATE[day_elem]]
        suggestion_lines.append("日主偏弱，应以扶助和生养为主。")
        if stars_strength["财星"] > stars_strength["比劫"] + stars_strength["印星"]:
            suggestion_lines.append(f"财星（{OVERCOME[day_elem]}）在命局中过旺，而日主偏弱，难以承受，因此财星为忌。")
            unfavored.append(OVERCOME[day_elem])
        elif stars_strength["财星"] > stars_strength["比劫"] * 1.05:
            suggestion_lines.append(f"财星（{OVERCOME[day_elem]}）虽比日主强，但有印星帮扶，整体能驾驭财，财可为喜，但需要有印来护日主（{MOTHER[day_elem]}）。")
            unfavored.append(OVERCOME[day_elem])

        favored = list(set(favored))
        unfavored = list(set(unfavored))
        suggestion_lines.append(f"喜用神五行为: {' '.join(favored)}。")
        suggestion_lines.append(f"忌用神五行为: {' '.join(unfavored)}。")

    else: 
        suggestion_lines.append("日主中和，五行能量相对均衡。")
        favored, unfavored = [], []
        # 提供补充性建议
        max_controller = RESTRAIN[max_elem]
        max_mother = MOTHER[max_elem]

        if max_elem in [RESTRAIN[day_elem], GENERATE[day_elem]]:
            suggestion_lines.append(f"{max_elem} 过旺，起到一定制衡和泄耗作用，可补充些许 {max_controller} 来制衡。")
            favored.append(max_controller)
            favored.append(MOTHER[day_elem])
            favored.append(day_elem)
            unfavored.append(max_elem, MOTHER[max_elem])
        elif max_elem == day_elem and stars_strength["比劫"] > mean(stars_strength.values()) * 2:
            suggestion_lines.append(f"{max_elem} 过旺，起到扶助作用，可考虑补充 {max_controller} {MOTHER[max_controller]} 来缓冲克制；")
            favored.append(max_controller)
            favored.append(MOTHER[max_controller])
            unfavored.append(max_elem)
        elif max_elem == MOTHER[day_elem] and stars_strength["印星"] > mean(stars_strength.values()) * 2:
            suggestion_lines.append(f"{max_elem} 过旺，起到生养作用，可考虑补充 {max_controller} {MOTHER[max_controller]} 来缓冲克制；")
            favored.append(max_controller)
            favored.append(MOTHER[max_controller])
            unfavored.append(max_elem)

        else: #财星最大，比日主大
            suggestion_lines.append(f"财星（{max_elem}）在命局中过旺，而日主偏弱，难以承受，因此财星为忌, 宜补印星（{MOTHER[day_elem]}）来护日主。")
            favored.append(MOTHER[day_elem])
            unfavored.append(RESTRAIN[day_elem])
            unfavored.append(max_elem)
        

        min_controller = MOTHER[RESTRAIN[min_elem]]
        min_mother = MOTHER[min_elem]

        if min_elem in [day_elem, MOTHER[day_elem]]:
            if min_mother != max_elem:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，起到扶助和生养作用，可适当补充 {min_elem} 和 {min_mother}。")
                favored.append(min_elem)
                favored.append(min_mother)
                unfavored.append(min_controller)
            else:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，起到扶助和生养作用，可适当补充 {min_elem}。")
                favored.append(min_elem)
                unfavored.append(min_controller)

        elif min_elem == RESTRAIN[day_elem]:
            if stars_strength["官杀"] >= mean(stars_strength.values()) * 0.7:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，起到一定制衡和泄耗作用，无需特殊处理。")
            else:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，如果官杀太小，命局缺少约束与规范，宜补官杀({min_elem})。")
                favored.append(min_elem)
                unfavored.append(min_controller)
        
        elif min_elem == GENERATE[day_elem]:
            if stars_strength["食伤"] >= mean(stars_strength.values()) * 0.7:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，起到一定制衡和泄耗作用，无需特殊处理。")
            else:
                suggestion_lines.append(f"五行最弱的是 {min_elem}，食伤表现了日主的才华、创造力、表达欲、子女运，同时是生财之源宜。如果食伤太小，宜补({min_elem})。")
                favored.append(min_elem)
                unfavored.append(min_controller)
        else: #财星
            suggestion_lines.append(f"五行最弱的是 {min_elem}，代表财星（{OVERCOME[day_elem]}），宜补财星。")
            favored.append(min_elem)
            unfavored.append(min_controller)

        favored = list(set(favored))
        unfavored = list(set(unfavored))
        if favored:
            suggestion_lines.append(f"喜用神五行为: {' '.join(favored)}。")
        #if unfavored:
        #    suggestion_lines.append(f"忌用神五行为: {' '.join(unfavored)}。")


        


    return {
        "favored": favored,
        "unfavored": unfavored,
        "suggestion": "".join(suggestion_lines)
    }



def elem_to_stem(elem):
    """
    把五行元素映射到对应的天干（阳+阴）。
    返回一个 list，例如 木 -> ["甲", "乙"]
    """
    return [gan for gan, e in STEM_TO_ELEMENT.items() if e == elem]


def ten_god_advice(dayMaster, favored_elems, unfavored_elems):
    """
    把五行喜忌翻译成十神喜忌 + 人事建议
    支持一个五行对应多个十神（阴阳干）
    """

    favorable_map = {
        "比肩": "代表自我、兄弟、伙伴。喜比肩时，多合作、结交志同道合的人，可以增强自信和行动力",
        "劫财": "代表朋友、同伴、竞争。喜劫财时，朋友能带来帮助和资源共享",
        "正印": "代表学习、贵人、保护。喜正印时，应多学习、提升学识，并依靠贵人支持",
        "偏印": "代表灵感、创造、直觉。喜偏印时，有助于发展创造力、灵性与直觉",
        "食神": "代表才华、子女、表达。喜食神时，应多发挥才华，注重表达与分享",
        "伤官": "代表创造力、叛逆、表现。喜伤官时，可以勇于创新与表达自我",
        "正财": "代表财富、责任、配偶。喜正财时，宜脚踏实地、注重理财和责任",
        "偏财": "代表机会、变通、人脉。喜偏财时，应抓住机会、灵活变通，注重人脉关系",
        "正官": "代表事业、责任、纪律。喜正官时，守纪律、重责任，有助于事业发展",
        "七杀": "代表挑战、竞争、魄力。喜七杀时，敢于挑战、果断有魄力，有助于开拓事业"
    }

    unfavorable_map = {
        "比肩": "忌比肩时，容易固执，与人对抗，需避免争强好胜",
        "劫财": "忌劫财时，易生竞争与冲突，需要学会分享与设立界限",
        "正印": "忌正印时，过于依赖他人，缺乏独立，需保持自主",
        "偏印": "忌偏印时，容易不切实际或精神不安定，应脚踏实地",
        "食神": "忌食神时，易懒散、贪图享乐，应自律",
        "伤官": "忌伤官时，易冲动叛逆，与权威对抗，需控制情绪",
        "正财": "忌正财时，可能过于物质或劳累，应适度理财并平衡生活",
        "偏财": "忌偏财时，易投机取巧、感情不稳，应谨慎理财与感情",
        "正官": "忌正官时，容易受束缚或压力过大，应学会调适与放松",
        "七杀": "忌七杀时，过度压力或冲动冒险，需谨慎行事"
    }

    advice = []

    # 喜神部分
    for elem in favored_elems:
        for gan in elem_to_stem(elem):
            tg = get_ten_god(dayMaster, gan)
            if tg and tg in favorable_map:
                advice.append(f"喜{tg}：{favorable_map[tg]}")

    # 忌神部分
    for elem in unfavored_elems:
        for gan in elem_to_stem(elem):
            tg = get_ten_god(dayMaster, gan)
            if tg and tg in unfavorable_map:
                advice.append(f"忌{tg}：{unfavorable_map[tg]}")

    result = ";\n".join(advice) + "。"
    return result






def dataframe_to_json(df: pd.DataFrame):
    # headers = column names
    headers = df.columns.tolist()
    
    # extract rows: each index (like 天干/地支) -> list of values
    rows = {}
    for idx in df.index:
        rows[idx] = df.loc[idx].tolist()
    
    return {
        "headers": headers,
        "rows": rows
    }
def generate_summary(data):
    """
    生成八字综合分析的自然语言段落
    输入: data (包含出生信息)
    输出: 段落总结 (str) + 打印十神分布表
    """


    # Step 1: 计算八字、五行、十神
    bazi = calc_bazi(data)
    fe = five_elements(bazi["fourPillars"], bazi["dayMaster"])
    strength = judge_strength(
        bazi["dayMaster"],
        fe["fiveElementsScore_adjusted"],
        fe["fiveElementsState"]
    )
    ten_gods_result = ten_gods(bazi["fourPillars"], bazi["dayMaster"], data["gender"])
    element_suggestion = suggest_five_elem(
        bazi["dayMaster"],
        strength["strength"],
        strength["stars_strength"],
        fe["fiveElementsScore_adjusted"]
    )
    ten_gods_advice_result = ten_god_advice(
        bazi["dayMaster"],
        element_suggestion["favored"],
        element_suggestion["unfavored"]
    )

    # Step 2: 组装自然语言段落 可以考虑AI引擎
    """ 
    你是一位专业八字命理分析师。请根据以下输入，生成一份约200字的八字综合分析总结，
    要求逻辑清晰、语言自然，先分析八字结构、五行强弱与日主格局，再说明喜用神与忌用神的推荐，
    最后结合十神做简要人事启示。

    输出格式必须为 JSON，包含两个字段：
    1. "analysis_paragraph" : 一段自然语言总结（约200字）
    2. "recommendation" : 一个对象，包含 "favored" 和 "unfavored"，其值为五行列表
    【输入信息】:
    - 八字: {bazi['bazi_explanation']}
    - 五行分布: {fe['fiveElement_explanation']}
    - 日主强弱: {strength['strength']} ({strength['strength_explanation']})
    - 喜用神分析: {element_suggestion['suggestion']}
    - 十神分布与启示: {ten_gods_advice_result}

    【输出示例】:
    {
    "analysis_paragraph": "在此命局中，日主为己土，处于休囚状态，自身偏弱。五行分布显示木火较旺，水几乎全无，金虽有但受木所制，难以助土。综合来看，此命局需以火土为主来增强根基，同时适度引入金以制木，若行运得水，则有润泽之功。忌再增木与过多之火，以免进一步削弱己土。十神方面，伤官与七杀较多，显示个性独立，有才华表达与突破精神，但易与权威冲突。宜借助印星学习与成长，同时发挥比肩劫财的伙伴协助力量。总体而言，此命局需平衡木火之势，稳固土性，以利发展。",
    "recommendation": {
    "favored": ["火", "土", "金", "水"],
    "unfavored": ["木", "过旺的火"]}
    } """


    tenGods_table = dataframe_to_json(ten_gods_result["tenGodsTable"])

    # 出生与八字结构
    result = {
        "bazi": bazi["fourPillars"],
        #"bazi_info": bazi['bazi_explanation'],
        "fiveElement_explanation": fe['fiveElement_explanation'], 
        "fiveElement_score_explanation": fe['fiveElement_score_explanation'],
        "dayElement": strength["dayElement"],
        "dayElement_state":strength["dayElement_state"],
        "strength" : strength['strength'], 
        "element_suggestion": element_suggestion['suggestion'], 
        "tenGods_table": tenGods_table,
        "tenGods_advice": ten_gods_advice_result
    }



    #ten_god_score = "\n" + " ".join([f"{k} = {round(v, 2)}" for k, v in ten_gods_result["tenGodsSummary"].items()]) + "。"

    return result



