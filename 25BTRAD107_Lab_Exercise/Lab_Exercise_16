import random
from collections import Counter

random.seed(2026)


def roll_dice(n_dice=1, sides=6):
    return [random.randint(1, sides) for _ in range(n_dice)]


def show_roll(roll_no, faces):
    print(f"Roll {roll_no:>2}: {faces} total = {sum(faces)}")


def frequency_table(results, sides=6):
    counts = Counter(results)
    total = len(results)

    print(f"{'Face':<6}{'Count':<8}{'Observed %':<12}{'Expected %':<12}Histogram")

    for face in range(1, sides + 1):
        c = counts.get(face, 0)

        print(
            f"{face:<6}{c:<8}{c / total * 100:<12.2f}"
            f"{100 / sides:<12.2f}{'#' * (c * 50 // total)}"
        )


def sum_table(sums):
    counts = Counter(sums)
    total = len(sums)

    theory = {
        s: (6 - abs(s - 7)) / 36 * 100
        for s in range(2, 13)
    }

    print(f"{'Sum':<6}{'Count':<8}{'Observed %':<12}{'Theory %':<10}")

    for s in range(2, 13):
        print(
            f"{s:<6}{counts.get(s, 0):<8}"
            f"{counts.get(s, 0) / total * 100:<12.2f}"
            f"{theory[s]:<10.2f}"
        )


if __name__ == "__main__":

    print("== Part 1: single die, 10 rolls ==")

    for i in range(1, 11):
        show_roll(i, roll_dice(1))

    print("\n== Part 2: two dice, 8 rolls (board-game style) ==")

    for i in range(1, 9):
        faces = roll_dice(2)
        show_roll(i, faces)

        if faces[0] == faces[1]:
            print("          -> Double! Roll again (as in Monopoly/Ludo rules)")

    for trials in (60, 600, 60000):
        print(f"\n== Part 3: single die, {trials} trials ==")

        frequency_table([roll_dice(1)[0] for _ in range(trials)])

    print("\n== Part 4: sum of two dice, 36000 trials ==")

    sum_table([sum(roll_dice(2)) for _ in range(36000)])

    print("\n== Part 5: how many rolls to get the first six? (5000 games) ==")

    waits = []

    for _ in range(5000):
        n = 1

        while roll_dice(1)[0] != 6:
            n += 1

        waits.append(n)

    print(
        f"Average rolls needed = {sum(waits) / len(waits):.2f} "
        "(theory = 6.00)"
    )
