#!/usr/bin/env python3
"""Number Guessing Game - a CLI game with difficulty levels, hints, a timer,
high scores and multiple rounds.

Run:  python3 number_guessing_game.py
"""

import json
import random
import sys
import time
from pathlib import Path

LOW, HIGH = 1, 100
SCORE_FILE = Path.home() / ".number_guessing_scores.json"

# name: (chances, hints allowed)
DIFFICULTIES = {
    "1": ("Easy", 10, 3),
    "2": ("Medium", 5, 2),
    "3": ("Hard", 3, 1),
}

# ---------- tiny colour helper (auto-disabled when not a terminal) ----------
USE_COLOR = sys.stdout.isatty()


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c(t, "92")
def red(t): return c(t, "91")
def yellow(t): return c(t, "93")
def cyan(t): return c(t, "96")
def bold(t): return c(t, "1")
def dim(t): return c(t, "2")


# ---------- high score storage ----------
def load_scores():
    try:
        return json.loads(SCORE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def save_scores(scores):
    try:
        SCORE_FILE.write_text(json.dumps(scores, indent=2))
    except OSError:
        print(dim("(Couldn't save high scores to disk.)"))


def update_high_score(scores, level, attempts, seconds):
    """Return a list of messages about any records broken."""
    record = scores.get(level, {})
    messages = []
    if "attempts" not in record or attempts < record["attempts"]:
        record["attempts"] = attempts
        messages.append(f"New {level} record for fewest attempts: {attempts}!")
    if "time" not in record or seconds < record["time"]:
        record["time"] = round(seconds, 2)
        messages.append(f"New {level} record for fastest time: {seconds:.2f}s!")
    scores[level] = record
    save_scores(scores)
    return messages


def show_scores(scores):
    print(bold("\n🏆 High Scores"))
    for key in sorted(DIFFICULTIES):
        level = DIFFICULTIES[key][0]
        rec = scores.get(level)
        if rec:
            print(f"  {level:<7} {rec['attempts']} attempts | {rec['time']:.2f}s")
        else:
            print(f"  {level:<7} {dim('no record yet')}")


# ---------- input helpers ----------
def ask(prompt):
    """input() that exits cleanly on Ctrl+C / Ctrl+D."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print(cyan("\n\nThanks for playing. Goodbye! 👋"))
        sys.exit(0)


def choose_difficulty():
    print(bold("Please select the difficulty level:"))
    for key, (name, chances, hints) in DIFFICULTIES.items():
        print(f"{key}. {name} ({chances} chances, {hints} hint{'s' if hints > 1 else ''})")
    while True:
        choice = ask("\nEnter your choice: ")
        if choice in DIFFICULTIES:
            return DIFFICULTIES[choice]
        print(red("Please enter 1, 2 or 3."))


# ---------- hints ----------
def build_hints(secret):
    """Return a shuffled-in-quality list of hints; best ones come first."""
    hints = [f"The number is {'even' if secret % 2 == 0 else 'odd'}."]

    start = max(LOW, min(secret - random.randint(0, 19), HIGH - 19))
    hints.append(f"The number is between {start} and {start + 19}.")

    divisors = [d for d in (3, 5, 7) if secret % d == 0]
    if divisors:
        hints.append(f"The number is divisible by {random.choice(divisors)}.")
    else:
        hints.append("The number is not divisible by 3, 5 or 7.")

    digit_sum = sum(int(d) for d in str(secret))
    hints.append(f"The digits of the number add up to {digit_sum}.")
    return hints


def closeness(diff):
    if diff <= 3:
        return red("🔥 Burning hot!")
    if diff <= 10:
        return yellow("♨️  Warm.")
    if diff <= 25:
        return cyan("🌤  Cool.")
    return cyan("❄️  Cold.")


# ---------- a single round ----------
def play_round(scores):
    level, max_chances, max_hints = choose_difficulty()
    secret = random.randint(LOW, HIGH)
    hints = build_hints(secret)

    print(f"\nGreat! You have selected the {bold(level)} difficulty level.")
    print(f"You have {bold(str(max_chances))} chances. Type {cyan('hint')} for a clue "
          f"(costs 1 chance, {max_hints} allowed) or {cyan('q')} to give up.")
    print("Let's start the game!\n")

    attempts = 0
    hints_used = 0
    chances_left = max_chances
    previous = []
    start = time.perf_counter()

    while chances_left > 0:
        raw = ask(f"[{chances_left} left] Enter your guess: ").lower()

        if raw in ("q", "quit"):
            print(yellow(f"You gave up! The number was {secret}."))
            return

        if raw in ("h", "hint"):
            if hints_used >= max_hints:
                print(red("No hints left this round."))
            elif chances_left <= 1:
                print(red("You can't spend your last chance on a hint!"))
            else:
                print(yellow(f"💡 Hint: {hints[hints_used]}"))
                hints_used += 1
                chances_left -= 1
            continue

        try:
            guess = int(raw)
        except ValueError:
            print(red(f"Please enter a whole number between {LOW} and {HIGH}."))
            continue

        if not LOW <= guess <= HIGH:
            print(red(f"Out of range! Pick a number between {LOW} and {HIGH}."))
            continue
        if guess in previous:
            print(yellow("You already tried that number. (No chance used.)"))
            continue

        previous.append(guess)
        attempts += 1
        chances_left -= 1

        if guess == secret:
            elapsed = time.perf_counter() - start
            word = "attempt" if attempts == 1 else "attempts"
            print(green(f"\n🎉 Congratulations! You guessed the correct number in "
                        f"{attempts} {word}."))
            print(f"⏱  Time taken: {elapsed:.2f} seconds")
            for msg in update_high_score(scores, level, attempts, elapsed):
                print(green(f"⭐ {msg}"))
            return

        direction = "less" if secret < guess else "greater"
        print(red(f"Incorrect! The number is {direction} than {guess}.") +
              f"  {closeness(abs(secret - guess))}")

    print(red(f"\n💀 Out of chances! The number was {secret}."))
    print(f"⏱  You played for {time.perf_counter() - start:.2f} seconds.")


# ---------- main loop ----------
def main():
    scores = load_scores()

    print(bold(cyan("=" * 46)))
    print(bold(cyan("   Welcome to the Number Guessing Game!")))
    print(bold(cyan("=" * 46)))
    print(f"I'm thinking of a number between {LOW} and {HIGH}.")
    print("Guess it before you run out of chances!")
    print(dim("Rules: pick a difficulty, then guess. I'll tell you if the\n"
              "number is higher or lower. Ask for a hint if you're stuck.\n"))
    show_scores(scores)
    print()

    while True:
        play_round(scores)
        again = ask("\nPlay again? (y/n): ").lower()
        while again not in ("y", "yes", "n", "no"):
            again = ask("Please answer y or n: ").lower()
        if again in ("n", "no"):
            show_scores(scores)
            print(cyan("\nThanks for playing. Goodbye! 👋"))
            break
        print()


if __name__ == "__main__":
    main()