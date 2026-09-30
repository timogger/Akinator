# Akinator-Style Guessing Game

A small, self-extensible Python guessing game with no external frameworks.

## Requirements

- Python 3.10 or newer
- `colorama`

Installation:

```bash
pip install -r requirements.txt
```

Start:

```bash
python main.py
```

## Your Own Data

The project ships with an example dataset of well-known real (and one fictional) people in `persons.json` and `questions.json` so you can try the game right away. Feel free to replace it with your own data.

The easiest way to add data is through the main menu.

### Adding a question

Via:

`3 - Add question`

a question is created with an ID and a weight.

Example of a single question in JSON:

```json
{
  "id": "q1",
  "text": "Is the person male?",
  "weight": 2.0
}
```

The weight can be interpreted like this, for example:

- `0.5` = rather unimportant / subjective
- `1.0` = normal
- `2.0` = important
- `3.0` or higher = very important

### Adding a person

Via:

`2 - Add person`

you can create your own person or character.

A person looks roughly like this in the JSON file:

```json
{
  "id": "p1",
  "name": "Albert Einstein",
  "description": "Short description",
  "answers": {
    "q1": "y"
  }
}
```

The following are used for answers:

- `y` = Yes
- `n` = No
- `m` = Maybe
- `i` = unknown

`i` is especially useful when a piece of information isn't known yet.

## How the probability calculation works

The game starts with all persons being equally likely.

After each answer, it's checked for every person how well their stored answer matches the answer given in the current game.

Example:

- Game answer `y`
- Person has `y` stored for this question
- strong match → high factor, e.g. `0.90`

If the stored answer is `n` instead, the match is low, e.g. `0.10`.

The question's weight is used as an exponent:

```text
Factor = base probability ^ weight
```

This makes an important question count more than a normal question.

The individual factors are multiplied together and then normalized across all persons. The result is relative probabilities that together add up to roughly 100%.

This is intentionally a simple, loosely Bayesian approximation, not a complete statistical model.

## Choosing the next question

The game looks at the persons who are currently still likely.

A good next question is one where the known answers are distributed as evenly as possible across `y`, `n` and `m`. A question where almost all candidates have the same answer, on the other hand, doesn't help much.

The question's weight is also taken into account.

This favors clear discriminating questions without needing a complicated decision-tree or machine-learning architecture.

## Learning mode

If the guess was wrong, learning mode lets you:

1. create a new person, or
2. select an existing person and add better answers.

New questions are initially set to `i` for existing persons, so the unknown information stays neutral.

This lets the system grow gradually with your own data.
