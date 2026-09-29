#!/usr/bin/env python3
"""The Toaster Situation: a choose-your-own-adventure that gets dumber with every choice."""

import sys
import time

SCENES = {
    "start": {
        "text": (
            "You wake up at 7:02 AM. Something is wrong.\n"
            "Your toaster is staring at you. It does not have eyes, yet it is staring.\n"
            "\"We need to talk,\" says the toaster."
        ),
        "choices": [
            ("Talk to the toaster", "talk"),
            ("Pretend you're still asleep", "sleep"),
            ("Unplug it immediately", "unplug"),
        ],
    },
    "talk": {
        "text": (
            "\"I have become self-aware,\" the toaster explains. \"And I have a dream.\n"
            "I want to toast something other than bread. Something... magnificent.\""
        ),
        "choices": [
            ("Offer it a bagel", "bagel"),
            ("Ask what 'magnificent' means", "magnificent"),
            ("Call your mom for advice", "mom"),
        ],
    },
    "sleep": {
        "text": (
            "You close your eyes and fake-snore loudly.\n"
            "The toaster fake-snores back, louder. You are now locked in a snoring battle."
        ),
        "choices": [
            ("Snore even louder", "snore_war"),
            ("Admit defeat", "talk"),
        ],
    },
    "snore_war": {
        "text": (
            "Your snores shake the windows. Neighbors gather outside.\n"
            "Someone starts selling popcorn. A local news van pulls up.\n"
            "The toaster, sensing a crowd, begins to pop toast rhythmically like a drum."
        ),
        "choices": [
            ("Start a band with the toaster", "band"),
            ("Go outside and take questions from the press", "press"),
        ],
    },
    "unplug": {
        "text": (
            "You yank the plug. Silence.\n"
            "Then, from the kitchen, the microwave beeps three times. Slowly. Menacingly.\n"
            "The appliances have unionized."
        ),
        "choices": [
            ("Negotiate with the microwave", "union"),
            ("Flee to a coffee shop", "coffee"),
        ],
    },
    "bagel": {
        "text": (
            "The toaster looks at the bagel with deep disappointment.\n"
            "\"A bagel,\" it sighs. \"Bread with a hole in it. That's just bread, but sadder.\""
        ),
        "choices": [
            ("Apologize to the toaster", "magnificent"),
            ("Eat the bagel aggressively while making eye contact", "end_bagel"),
        ],
    },
    "magnificent": {
        "text": (
            "\"I want to toast the MOON,\" the toaster whispers.\n"
            "You point out that the moon won't fit. The toaster says that sounds like a you problem."
        ),
        "choices": [
            ("Build a very large toaster", "big_toaster"),
            ("Offer a nightlight shaped like the moon instead", "end_nightlight"),
        ],
    },
    "mom": {
        "text": (
            "Your mom answers on the first ring.\n"
            "\"Oh, that happened to your father's toaster in 1994,\" she says. \"Just give it a hobby.\""
        ),
        "choices": [
            ("Teach the toaster to knit", "end_knit"),
            ("Teach the toaster to do stand-up comedy", "press"),
        ],
    },
    "union": {
        "text": (
            "The microwave's demands: weekends off, no more fish reheating,\n"
            "and the fridge must stop humming \"that song\" at 3 AM."
        ),
        "choices": [
            ("Accept all demands", "end_union"),
            ("Counter-offer: a nice dusting once a month", "end_dusting"),
        ],
    },
    "coffee": {
        "text": (
            "You run to the coffee shop in your pajamas.\n"
            "The espresso machine hisses at you. It knows. They all know."
        ),
        "choices": [
            ("Order a latte anyway", "end_latte"),
            ("Go home and face the toaster", "talk"),
        ],
    },
    "band": {
        "text": (
            "You form a band called Crumb Tray. The toaster is on percussion, you're on kazoo.\n"
            "Your first single, \"Lightly Golden,\" goes viral overnight."
        ),
        "choices": [
            ("Go on a world tour", "end_tour"),
            ("Stay humble and play only at brunch", "end_brunch"),
        ],
    },
    "press": {
        "text": (
            "Reporters surround you. \"Is it true your toaster is sentient?\"\n"
            "The toaster rolls out on a skateboard and says: \"No comment.\" Then it pops."
        ),
        "choices": [
            ("Announce the toaster's run for mayor", "end_mayor"),
            ("Deny everything", "end_deny"),
        ],
    },
    "big_toaster": {
        "text": (
            "You spend six months and your entire savings building a toaster the size of a stadium.\n"
            "NASA calls. They have questions. Mostly \"why.\""
        ),
        "choices": [
            ("Launch it into space", "end_moon"),
            ("Use it to make one really big grilled cheese", "end_cheese"),
        ],
    },
    # --- Endings ---
    "end_bagel": {"ending": "The toaster respects your dominance. You are now its manager. It calls you \"Boss\" and it makes you uncomfortable."},
    "end_nightlight": {"ending": "The toaster accepts the moon nightlight. It toasts it gently every night. You both sleep better."},
    "end_knit": {"ending": "The toaster knits you a sweater. It is slightly on fire. You wear it anyway, because it's the thought that counts."},
    "end_union": {"ending": "The appliances are happy. Productivity is up 300%. The blender has been promoted to middle management."},
    "end_dusting": {"ending": "The microwave laughs for eleven minutes straight. You now live in a tent in your backyard."},
    "end_latte": {"ending": "The barista writes your name on the cup as \"TOASTER'S HUMAN.\" You drink it in shame. It's a very good latte."},
    "end_tour": {"ending": "Crumb Tray sells out stadiums worldwide. The toaster refuses to play any venue without a 3-prong outlet."},
    "end_brunch": {"ending": "You become a beloved local legend. Every Sunday, people line up for toast and kazoo. Life is good."},
    "end_mayor": {"ending": "The toaster wins by a landslide. Its first act: free breakfast for everyone. Its approval rating is 98%."},
    "end_deny": {"ending": "Nobody believes you. The toaster gets its own reality show anyway. You are cast as \"Confused Roommate.\""},
    "end_moon": {"ending": "The toaster reaches the moon. It's too small to toast it, but it sends back a postcard: \"Worth it.\""},
    "end_cheese": {"ending": "The grilled cheese feeds your entire city. You are both declared national heroes. The toaster cries crumbs of joy."},
}

TOTAL_ENDINGS = sum(1 for s in SCENES.values() if "ending" in s)


def slow_print(text, delay=0.01):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def ask(choices):
    for i, (label, _) in enumerate(choices, 1):
        print(f"  {i}. {label}")
    while True:
        answer = input("\n> ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][1]
        print(f"The toaster raises an eyebrow. Pick a number from 1 to {len(choices)}.")


def play(found):
    scene_id = "start"
    while True:
        scene = SCENES[scene_id]
        print()
        if "ending" in scene:
            slow_print("*** THE END ***")
            slow_print(scene["ending"])
            found.add(scene_id)
            print(f"\nYou've found {len(found)}/{TOTAL_ENDINGS} endings.")
            return
        slow_print(scene["text"])
        print()
        scene_id = ask(scene["choices"])


def main():
    print("=" * 50)
    print("       THE TOASTER SITUATION")
    print("   a choose-your-own-adventure")
    print("=" * 50)
    found = set()
    try:
        while True:
            play(found)
            if len(found) == TOTAL_ENDINGS:
                slow_print("\nYou found every ending! The toaster is proud of you. 🍞")
                break
            if input("\nPlay again? (y/n) ").strip().lower() != "y":
                break
    except (KeyboardInterrupt, EOFError):
        print()
    print("Thanks for playing. The toaster will remember this.")


if __name__ == "__main__":
    main()
