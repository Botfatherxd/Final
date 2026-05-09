import re

def rarity(username):
    score = 0
    reasons = []

    # длина
    if len(username) == 5:
        score += 4
        reasons.append("5 символов +4")

    if len(username) == 6:
        score += 2
        reasons.append("6 символов +2")

    # цифры
    digits = sum(c.isdigit() for c in username)

    if digits:
        score -= digits
        reasons.append(f"цифры -{digits}")

    # без цифр
    if digits == 0:
        score += 2
        reasons.append("без цифр +2")

    # уникальность
    unique = len(set(username))

    if unique <= 2:
        score += 5
        reasons.append("мало символов +5")

    elif unique <= 3:
        score += 3
        reasons.append("повторы +3")

    # двойные символы
    doubles = re.findall(r"(.)\1", username)

    if doubles:
        score += len(doubles) * 2
        reasons.append(f"двойные +{len(doubles)*2}")

    # палиндром
    if username == username[::-1]:
        score += 6
        reasons.append("палиндром +6")

    # одинаковое начало и конец
    if username[0] == username[-1]:
        score += 2
        reasons.append("одинаковый край +2")

    # читаемость
    vowels = "aeiou"

    vowel_count = sum(c in vowels for c in username)

    if vowel_count >= 2:
        score += 2
        reasons.append("читаемый +2")

    # рифма
    if username[:2] == username[-2:]:
        score += 4
        reasons.append("рифма +4")

    # редкие буквы
    rare = ["x", "z", "q", "v", "k"]

    if any(r in username for r in rare):
        score += 1
        reasons.append("редкие символы +1")

    # ранги
    if score <= 1:
        rank = "🪨 Обычный"

    elif score <= 4:
        rank = "✨ Нормальный"

    elif score <= 8:
        rank = "🔥 Редкий"

    else:
        rank = "💎 Легендарный"

    return (
        f"{rank} ({score}/10)\n"
        f"├ {' | '.join(reasons)}"
    )
