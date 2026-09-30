import json
from pathlib import Path

from colorama import Fore, Style, init

init(autoreset=True)

PERSONS_FILE = Path("persons.json")
QUESTIONS_FILE = Path("questions.json")

# How well does a stored answer match the player's answer?
MATCH = {
    "y": {"y": 0.90, "n": 0.10, "m": 0.55, "i": 0.50},
    "n": {"y": 0.10, "n": 0.90, "m": 0.55, "i": 0.50},
    "m": {"y": 0.45, "n": 0.45, "m": 0.75, "i": 0.50},
    "i": {"y": 0.50, "n": 0.50, "m": 0.50, "i": 0.50},
}


def load(file, key):
    if not file.exists():
        file.write_text(json.dumps({key: []}, indent=2, ensure_ascii=False))
    try:
        return json.loads(file.read_text(encoding="utf-8")).get(key, [])
    except json.JSONDecodeError:
        print(Fore.RED + f"Error in {file.name}.")
        return []


def save(file, key, data):
    file.write_text(
        json.dumps({key: data}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def answer():
    while True:
        value = input(
            Fore.YELLOW + "Answer [y/n/m/i]: " + Style.RESET_ALL
        ).lower().strip()
        if value in "ynmi":
            return value
        print(Fore.RED + "Please enter y, n, m or i.")


def weight():
    while True:
        try:
            value = float(input("Weight [0.5 - 5]: ").replace(",", "."))
            if 0.1 <= value <= 5:
                return value
        except ValueError:
            pass
        print(Fore.RED + "Please enter a number between 0.1 and 5.")


def calculate(persons, questions, given):
    scores = {}

    for person in persons:
        score = 1.0

        for question in questions:
            qid = question["id"]
            if qid not in given:
                continue

            game_answer = given[qid]
            person_answer = person.get("answers", {}).get(qid, "i")
            w = float(question.get("weight", 1))

            score *= MATCH[game_answer].get(person_answer, 0.5) ** w

        scores[person["id"]] = score

    total = sum(scores.values())
    if total:
        for person_id in scores:
            scores[person_id] /= total

    return scores


def next_question(persons, questions, scores, asked):
    best = None
    best_value = -1

    for question in questions:
        if question["id"] in asked:
            continue

        # How varied are the known answers?
        parts = {"y": 0, "n": 0, "m": 0}

        for person in persons:
            answer = person.get("answers", {}).get(question["id"])
            if answer in parts:
                parts[answer] += scores.get(person["id"], 0)

        total = sum(parts.values())
        if not total:
            continue

        diversity = 1 - sum((value / total) ** 2 for value in parts.values())
        value = diversity * float(question.get("weight", 1))

        if value > best_value:
            best_value = value
            best = question

    return best


def play(persons, questions):
    if not persons or not questions:
        print(Fore.RED + "You need at least one person and one question.")
        input("Press Enter...")
        return

    print(Fore.CYAN + "\nThink of a person or character.")
    print("y = Yes | n = No | m = Maybe | i = I don't know\n")

    given = {}
    asked = set()
    scores = {p["id"]: 1 / len(persons) for p in persons}

    for _ in range(min(20, len(questions))):
        question = next_question(persons, questions, scores, asked)
        if not question:
            break

        print(Fore.MAGENTA + "\nQuestion: " + question["text"])
        given[question["id"]] = answer()
        asked.add(question["id"])

        scores = calculate(persons, questions, given)

        best = max(persons, key=lambda p: scores[p["id"]])
        print(
            Fore.CYAN
            + f"My current guess: {best['name']} "
            f"({scores[best['id']] * 100:.1f}%)"
        )

    results = sorted(persons, key=lambda p: scores[p["id"]], reverse=True)
    best = results[0]

    print(Fore.GREEN + Style.BRIGHT + f"\nMy guess is: {best['name']}")
    print(f"Probability: {scores[best['id']] * 100:.1f}%")

    if input("Correct? [y/n]: ").lower().strip() == "n":
        print(Fore.YELLOW + "Then let's open learning mode.")
    input("Press Enter...")


def add_person(persons, questions):
    name = input("Name: ").strip()
    if not name:
        return

    person = {
        "id": f"p{len(persons) + 1}",
        "name": name,
        "description": input("Description (optional): ").strip(),
        "answers": {},
    }

    for question in questions:
        print("\n" + question["text"])
        person["answers"][question["id"]] = answer()

    persons.append(person)
    save(PERSONS_FILE, "persons", persons)
    print(Fore.GREEN + "Person added.")
    input("Press Enter...")


def add_question(persons, questions):
    text = input("Question: ").strip()
    if not text:
        return

    question = {
        "id": f"q{len(questions) + 1}",
        "text": text,
        "weight": weight(),
    }
    questions.append(question)

    for person in persons:
        person.setdefault("answers", {})[question["id"]] = "i"

    save(QUESTIONS_FILE, "questions", questions)
    save(PERSONS_FILE, "persons", persons)

    print(Fore.GREEN + "Question added.")
    input("Press Enter...")


def show_data(persons, questions):
    print(Fore.CYAN + "\nQUESTIONS")
    for q in questions:
        print(f"{q['id']}: {q['text']} (Weight: {q.get('weight', 1)})")

    print(Fore.CYAN + "\nPERSONS")
    for p in persons:
        print(f"{p['id']}: {p['name']}")

    input("\nPress Enter...")


def edit_person(persons, questions):
    for p in persons:
        print(f"{p['id']}: {p['name']}")

    pid = input("\nPerson ID: ").strip()
    person = next((p for p in persons if p["id"] == pid), None)

    if not person:
        print(Fore.RED + "Not found.")
        return

    for q in questions:
        print("\n" + q["text"])
        person.setdefault("answers", {})[q["id"]] = answer()

    save(PERSONS_FILE, "persons", persons)
    print(Fore.GREEN + "Person updated.")
    input("Press Enter...")


def learn(persons, questions):
    print(Fore.CYAN + "\nLearning mode")
    print("1 - Add new person")
    print("2 - Improve person")
    print("0 - Back")

    choice = input("Choice: ").strip()

    if choice == "1":
        add_person(persons, questions)
    elif choice == "2" and persons:
        edit_person(persons, questions)


def main():
    while True:
        persons = load(PERSONS_FILE, "persons")
        questions = load(QUESTIONS_FILE, "questions")

        print(Fore.CYAN + "\n" + "=" * 45)
        print("         AKINATOR-STYLE GUESSING GAME")
        print("=" * 45 + Style.RESET_ALL)
        print("y = Yes")
        print("n = No")
        print("m = Maybe / possibly")
        print("i = I don't know")
        print()
        print("1 - Start game")
        print("2 - Add person")
        print("3 - Add question")
        print("4 - Show data")
        print("5 - Learning mode")
        print("0 - Exit")

        choice = input(Fore.YELLOW + "\nChoice: " + Style.RESET_ALL).strip()

        if choice == "1":
            play(persons, questions)
        elif choice == "2":
            add_person(persons, questions)
        elif choice == "3":
            add_question(persons, questions)
        elif choice == "4":
            show_data(persons, questions)
        elif choice == "5":
            learn(persons, questions)
        elif choice == "0":
            print(Fore.GREEN + "Goodbye!")
            break


if __name__ == "__main__":
    main()
