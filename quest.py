#!/usr/bin/env python3
"""The Last Ember: an epic choose-your-own-adventure with dragons, wizards, and masked heroes."""

import os
import sys
import time

if os.name == "nt":
    os.system("")  # lets the Windows terminal show colors

GOLD = "\033[93m"
PURPLE = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = r"""
         />_________________________________
[########[]_________________________________>
         \>
"""

# Each scene has "text" plus either "choices" (label, scene) or "next" (press Enter).
# A choice with a third value, like (label, scene, "Phoenix Feather"), only shows up
# if you're carrying that item. "gain" adds an item to your inventory, and "set"
# remembers things like your hero name. Endings have a "title" and an "ending".
SCENES = {
    "start": {
        "text": (
            "The sun has not risen in three days.\n"
            "In the village of Little Wickham, everyone needs candles, and you, {name},\n"
            "the candlemaker's apprentice, have never been so busy.\n"
            "Tonight, as you dip the last wick, the shop door bursts open. Shadow-hounds\n"
            "pour in, eyes glowing like cold coals. Without thinking, you throw up your\n"
            "hands, and golden fire EXPLODES from your palms. The hounds burst into smoke."
        ),
        "next": "stranger",
    },
    "stranger": {
        "text": (
            "\"Well,\" says a voice behind you. \"That answers that.\"\n"
            "In the doorway stands an old woman in a cloak stitched with stars that\n"
            "actually twinkle. \"I am Orla Starweave. And you, {name}, carry the Last\n"
            "Ember: the final spark of the sun. Malgrath the Hollow King has stolen the\n"
            "Dawnstone, and without it the sun will never rise again. The world will\n"
            "freeze. He knows about you now. He will keep coming.\"\n"
            "She holds up three fingers. \"There are three roads to his Obsidian Spire.\""
        ),
        "choices": [
            ("Join a fellowship of warriors and march across the wild lands", "fellowship"),
            ("Train at Starfall Academy, the greatest school of magic in the world", "academy"),
            ("Put on a mask and become a hero in the city of Brightspire", "warden"),
            ("Politely decline and go back to making candles", "end_candles"),
        ],
    },
    # --- Road 1: The Fellowship ---
    "fellowship": {
        "text": (
            "Orla gathers you a fellowship:\n"
            "  Brakka Stonefist, a dwarf who has named all fourteen of her axes;\n"
            "  Sylas Windleaf, an elf archer whose hair blows dramatically, even indoors;\n"
            "  and Snig, a goblin who quit Malgrath's army because the snacks were awful.\n"
            "For nine days you march east. At the foot of the Grey Teeth Mountains,\n"
            "the road splits in two."
        ),
        "choices": [
            ("Climb the Whispering Pass over the peaks", "pass"),
            ("Take the Drowned Mines beneath the mountains", "mines"),
        ],
    },
    "pass": {
        "text": (
            "Snow howls around you. Halfway up the pass, a silver dragon the size of a\n"
            "castle uncoils from the ice.\n"
            "\"None cross my mountain,\" she rumbles, \"unless they answer my riddle:\n"
            "The more of me you take, the more of me you leave behind. What am I?\""
        ),
        "choices": [
            ("\"Footsteps.\"", "dragon_right"),
            ("\"Snacks?\" (Snig's whispered guess)", "dragon_wrong"),
            ("Charge at the dragon", "end_cushion"),
        ],
    },
    "dragon_right": {
        "text": (
            "The dragon's eyes go wide. \"Correct! No one has solved that in six hundred\n"
            "years.\" She plucks a silver scale from her chest and drops it into your\n"
            "hands. It's as warm as a fireplace. \"When you need me most, little Ember,\n"
            "hold it high. I will come.\""
        ),
        "gain": "Dragon Scale",
        "next": "ashlands",
    },
    "dragon_wrong": {
        "text": (
            "The dragon stares at you. Then at Snig. Then she lets out a long, smoky sigh.\n"
            "\"Wrong. But you're too small to be worth the indigestion.\"\n"
            "She lets you pass, grumbling about adventurers these days."
        ),
        "next": "ashlands",
    },
    "mines": {
        "text": (
            "The Drowned Mines are black, wet, and full of echoing drips. Brakka insists\n"
            "they were \"much cozier\" when her grandmother lived here.\n"
            "In a flooded hall, you find a broken sword on a stone altar, glowing faintly.\n"
            "Behind it, something enormous shifts beneath the dark water."
        ),
        "choices": [
            ("Grab the broken sword", "sword"),
            ("Tiptoe past the water", "sneak"),
        ],
    },
    "sword": {
        "text": (
            "The moment you touch the hilt, the Last Ember roars down your arm. The\n"
            "broken pieces glow white-hot and fuse together: the Oathbound Blade, lost\n"
            "for a thousand years. The thing in the water, a colossal eel with lantern\n"
            "eyes, takes one look at the blazing sword and dives out of sight.\n"
            "Brakka is so moved that she offers to make you ruler of the mines."
        ),
        "gain": "Oathbound Blade",
        "choices": [
            ("Onward to the Ashlands!", "ashlands"),
            ("Accept the crown and stay underground", "end_under_king"),
        ],
    },
    "sneak": {
        "text": (
            "You're doing great. Truly. Right up until Snig sneezes.\n"
            "The water explodes. A colossal eel with lantern eyes rears up, its jaws wide\n"
            "enough to swallow a wagon!"
        ),
        "choices": [
            ("Jump into a mine cart and ride for your life", "minecart"),
            ("Offer the eel a bowl of Snig's famous stew", "end_stew"),
        ],
    },
    "minecart": {
        "text": (
            "The cart screams down the rusty rails. Brakka is laughing, Sylas's hair is\n"
            "blowing majestically, and Snig is shrieking at a pitch only bats can hear.\n"
            "You blast out the far side of the mountain in a shower of sparks."
        ),
        "next": "ashlands",
    },
    "ashlands": {
        "text": (
            "Beyond the mountains lie the Ashlands, gray and silent under a starless sky.\n"
            "The Obsidian Spire claws at the darkness ahead. At its gate waits an army of\n"
            "shadow-soldiers. Brakka hefts axe number seven. Sylas nocks an arrow.\n"
            "Snig picks up a rock.\n"
            "\"We'll hold the gate,\" Brakka growls. \"Go, {name}. Finish this.\""
        ),
        "next": "spire",
    },
    # --- Road 2: Starfall Academy ---
    "academy": {
        "text": (
            "Orla whistles, and a moth the size of a horse flutters down from the sky.\n"
            "It carries you all night to Starfall Academy, a castle built on a falling\n"
            "star that froze in midair above a silver lake.\n"
            "The headmaster is a tortoise named Professor Grimsby. He is nine hundred\n"
            "years old and speaks very... very... slowly.\n"
            "In your first week, you levitate a teacup (it explodes), turn a frog into a\n"
            "slightly different frog, and set a school record: your Ember-magic is the\n"
            "strongest Starfall has seen in five hundred years."
        ),
        "next": "roommate",
    },
    "roommate": {
        "text": (
            "One night, your roommate, a nervous young wizard named Tobias Quill, shakes\n"
            "you awake. He's clutching an old map.\n"
            "\"There's a secret vault under the school,\" he whispers. \"And it's glowing.\n"
            "It started glowing the day you arrived.\""
        ),
        "choices": [
            ("Sneak into the vault tonight", "vault"),
            ("Tell Professor Grimsby about the map", "grimsby"),
            ("Ignore it and study for your exams", "end_top_class"),
        ],
    },
    "vault": {
        "text": (
            "You and Tobias creep past a suit of armor that is definitely only pretending\n"
            "to be asleep, down four hundred steps, to a round stone door.\n"
            "A mouth opens in the stone. \"I open only for a secret,\" it says.\n"
            "\"A true one.\""
        ),
        "choices": [
            ("Tell the door your real fear: that you're not hero enough", "door_fear"),
            ("Tell the door Tobias's secret instead", "door_tobias"),
            ("Blast the door open with Ember fire", "end_detention"),
        ],
    },
    "door_fear": {
        "text": (
            "The door is quiet for a long moment. \"That,\" it says softly, \"is the\n"
            "secret every true hero carries.\" It swings open."
        ),
        "next": "phoenix",
    },
    "door_tobias": {
        "text": (
            "\"Tobias still sleeps with a stuffed griffin named Sir Fluffington,\" you say.\n"
            "Tobias makes a noise like a deflating bagpipe. The door laughs so hard it\n"
            "falls off its hinges."
        ),
        "next": "phoenix",
    },
    "phoenix": {
        "text": (
            "Inside the vault, on a nest of silver flames, sleeps a phoenix, the last one\n"
            "in the world. It opens one ancient eye and looks at the Ember glowing in\n"
            "your chest. Then it plucks a single golden feather and lays it in your hand.\n"
            "\"The sun's own bird,\" Tobias breathes. \"It knows what you are.\""
        ),
        "gain": "Phoenix Feather",
        "next": "starfall_attack",
    },
    "grimsby": {
        "text": (
            "Professor Grimsby listens to the whole story. It takes him forty minutes to\n"
            "nod. Then, from under his shell, he draws out a staff of pale wood topped\n"
            "with a crystal that blazes the instant you touch it.\n"
            "\"The Dawnwright Staff,\" he says. \"It answers only to the Ember. You are\n"
            "not ready.\" He smiles, slowly. \"But nobody ever is.\""
        ),
        "gain": "Dawnwright Staff",
        "next": "starfall_attack",
    },
    "starfall_attack": {
        "text": (
            "That night, shadow-wraiths swarm Starfall Academy. Spells burst from every\n"
            "tower like fireworks. Professor Grimsby, moving faster than anyone has ever\n"
            "seen a tortoise move, holds the great gate alone.\n"
            "\"Go, {name}!\" he bellows. \"To the Spire! End this!\""
        ),
        "choices": [
            ("Leap onto the giant moth and fly to the Obsidian Spire", "spire"),
            ("Stay and defend the school", "end_defender"),
        ],
    },
    # --- Road 3: The Wardens of Brightspire ---
    "warden": {
        "text": (
            "Orla takes you to Brightspire, a city of a thousand towers, where masked\n"
            "heroes called Wardens guard the streets. Their leader, a mountain of a man\n"
            "in golden armor named Captain Bastion, looks you up and down.\n"
            "\"Powers? Check. Tragic backstory? We'll work on it.\" He crosses his arms.\n"
            "\"Every Warden needs a hero name. Choose wisely. You're stuck with it.\""
        ),
        "choices": [
            ("Sunstrike", "name_sunstrike"),
            ("The Blazing Comet", "name_comet"),
            ("Captain Candle", "name_candle"),
        ],
    },
    "name_sunstrike": {
        "set": {"hero": "Sunstrike"},
        "text": "\"Sunstrike.\" Bastion nods. \"Strong. Classic. Looks great on a lunchbox.\"",
        "next": "patrol",
    },
    "name_comet": {
        "set": {"hero": "The Blazing Comet"},
        "text": (
            "\"The Blazing Comet,\" Bastion repeats. \"A little long for a crowd to chant,\n"
            "but I respect the energy.\""
        ),
        "next": "patrol",
    },
    "name_candle": {
        "set": {"hero": "Captain Candle"},
        "text": (
            "Bastion stares at you for a very long time. \"Captain Candle.\" He sighs.\n"
            "\"Fine.\" (By the end of the week, every kid in Brightspire owns a\n"
            "Captain Candle mask.)"
        ),
        "next": "patrol",
    },
    "patrol": {
        "text": (
            "Your first night on patrol as {hero}.\n"
            "Shadow-beasts prowl the rooftops. Then two alarms ring out at once:\n"
            "shadow-beasts are attacking the city orphanage, and across town, someone\n"
            "has broken into the Wardens' armory."
        ),
        "choices": [
            ("Save the orphanage", "orphanage"),
            ("Stop the break-in at the armory", "armory"),
            ("Grab a quick snack first. Heroes need energy.", "end_snack"),
        ],
    },
    "orphanage": {
        "text": (
            "You crash through a window in a burst of golden fire, and the shadow-beasts\n"
            "flee shrieking into the night. Forty orphans cheer. A little girl hands\n"
            "you a crayon drawing of {hero}, looking very heroic and slightly\n"
            "like a potato.\n"
            "Captain Bastion arrives, sees the drawing, and nods. \"That's the job.\"\n"
            "He presses a brass flare into your hand. \"The Warden's Signal. Light it,\n"
            "and every hero in Brightspire will come running.\""
        ),
        "gain": "Warden's Signal",
        "next": "city_siege",
    },
    "armory": {
        "text": (
            "In the armory you catch the thief: a skinny kid in a homemade cape, trying\n"
            "to lift a glowing gauntlet twice the size of his arm.\n"
            "\"I just wanted to help,\" he says. \"But I don't have any powers.\""
        ),
        "choices": [
            ("Make him your sidekick", "sidekick"),
            ("Send him home where it's safe, and take the gauntlet yourself", "gauntlet"),
        ],
    },
    "sidekick": {
        "text": (
            "\"Really?!\" The kid's eyes go huge. \"I'm Kip! I've been practicing my hero\n"
            "pose!\" He shows you. It needs work. But as you patrol together, you notice\n"
            "that Kip spots everything: every shadow, every trick, every weak spot."
        ),
        "gain": "Kip the Sidekick",
        "next": "city_siege",
    },
    "gauntlet": {
        "text": (
            "You send the kid home with a promise to train him someday. The gauntlet\n"
            "slides onto your arm and hums to life, blazing with Ember-light.\n"
            "You punch a wall, just to test it. The wall is now in the next district."
        ),
        "gain": "Starmetal Gauntlet",
        "next": "city_siege",
    },
    "city_siege": {
        "text": (
            "At midnight, Malgrath's army marches on Brightspire, and the Wardens rush\n"
            "to the walls. Captain Bastion grips your shoulder.\n"
            "\"We'll hold the city. You've got the one thing he's afraid of,\n"
            "{hero}. Take the fight to him.\"\n"
            "A Warden called The Pigeon (a woman with nine hundred very strong pigeons)\n"
            "carries you east through the dark, all the way to the Ashlands."
        ),
        "next": "spire",
    },
    # --- The final battle ---
    "spire": {
        "text": (
            "You climb the last step of the Obsidian Spire. In a throne room of black\n"
            "glass stands Malgrath the Hollow King, tall as a tree and crowned in shadow.\n"
            "In his iron gauntlet, the Dawnstone flickers weakly, like a trapped heartbeat.\n"
            "\"So,\" he rumbles. \"The Last Ember comes to me at last. Join me, {name},\n"
            "and together we will rule the endless night.\""
        ),
        "choices": [
            ("\"Never!\" Fight him!", "battle"),
            ("Ask him why he stole the sun", "talk"),
            ("Take his hand and join him", "end_dark"),
        ],
    },
    "talk": {
        "text": (
            "Malgrath hesitates. Nobody has ever asked him that before.\n"
            "\"Do you have any idea,\" he whispers, \"what it's like to burn? Every.\n"
            "Single. Day?\" He lifts his visor. His face is bright pink.\n"
            "\"I have very sensitive skin.\""
        ),
        "choices": [
            ("Offer to make him a really big hat", "end_hat"),
            ("Tell him that's a terrible reason, and attack!", "battle"),
        ],
    },
    "battle": {
        "text": (
            "Malgrath roars. Shadows boil out of the walls and crash toward you like a\n"
            "black wave. The Last Ember blazes in your chest, brighter than it has ever\n"
            "burned. This is it. Everything you've got."
        ),
        "choices": [
            ("Raise the Oathbound Blade", "end_blade", "Oathbound Blade"),
            ("Hold the Dragon Scale high", "end_dragon", "Dragon Scale"),
            ("Set the Phoenix Feather alight", "end_phoenix", "Phoenix Feather"),
            ("Channel the Ember through the Dawnwright Staff", "end_staff", "Dawnwright Staff"),
            ("Light the Warden's Signal", "end_signal", "Warden's Signal"),
            ("Nod to Kip", "end_kip", "Kip the Sidekick"),
            ("Throw a punch with the Starmetal Gauntlet", "end_gauntlet", "Starmetal Gauntlet"),
            ("Pour the Last Ember into the Dawnstone", "end_sun"),
        ],
    },
    # --- Endings ---
    "end_candles": {
        "title": "The Candlemaker",
        "ending": (
            "Orla sighs and leaves. Malgrath's hounds never find you, because you're\n"
            "hidden behind ten thousand candles. The sun never comes back, but thanks to\n"
            "you, nobody in Little Wickham is ever in the dark. Malgrath finds this\n"
            "extremely annoying."
        ),
    },
    "end_cushion": {
        "title": "The Dragon's Cushion",
        "ending": (
            "You charge. The dragon doesn't burn you. She doesn't eat you. She simply\n"
            "sits on you. You spend the next eleven years as her favorite cushion.\n"
            "It's warm, at least, and she tells wonderful stories."
        ),
    },
    "end_under_king": {
        "title": "The Under-King",
        "ending": (
            "You rule the Drowned Mines wisely and well. Up above, the world is freezing.\n"
            "Down here, the hot springs are lovely, your subjects adore you, and the\n"
            "giant eel is your royal pet. His name is Gerald."
        ),
    },
    "end_stew": {
        "title": "The Deep-Sea Chef",
        "ending": (
            "The eel slurps up the stew. It freezes. Its lantern eyes fill with tears.\n"
            "It's the best thing it has ever tasted. You and Snig open a restaurant for\n"
            "giant sea monsters, and it gets five stars. Malgrath keeps the sun, but you\n"
            "get a cookbook deal."
        ),
    },
    "end_detention": {
        "title": "Detention Forever",
        "ending": (
            "The door is fine. The rest of the school is not. Three towers are on fire\n"
            "and the lake is now soup. You spend the rest of your life in detention,\n"
            "which, to be fair, is very well lit."
        ),
    },
    "end_top_class": {
        "title": "Top of the Class",
        "ending": (
            "You study harder than anyone ever has. You ace every exam. You graduate\n"
            "first in your class! The ceremony is held in the snow, by candlelight,\n"
            "because the sun never came back. Your family is very proud and very cold."
        ),
    },
    "end_defender": {
        "title": "Defender of Starfall",
        "ending": (
            "You and Tobias fight side by side until dawn, which never comes. But every\n"
            "student in Starfall is safe. In the long night that follows, the Academy\n"
            "becomes the brightest place in the world, and you become its greatest\n"
            "teacher."
        ),
    },
    "end_snack": {
        "title": "Snack Break",
        "ending": (
            "The line for pie is very long. By the time you get yours, both emergencies\n"
            "have been handled by a Warden called The Pigeon. The Pigeon gets a statue.\n"
            "You get a pie. It is, honestly, a very good pie."
        ),
    },
    "end_blade": {
        "title": "The Sword of Dawn",
        "ending": (
            "The Oathbound Blade meets the wave of shadow and cuts it clean in half.\n"
            "One more strike, and the Dawnstone flies free of Malgrath's grip. It soars\n"
            "out the window, up and up, and the sun rises for the first time in weeks.\n"
            "Far below, Brakka, Sylas, and Snig cheer. Snig cries. He says it's just\n"
            "ash in his eye."
        ),
    },
    "end_dragon": {
        "title": "Dragonfriend",
        "ending": (
            "You raise the silver scale. A roar shakes the world, and the wall of the\n"
            "throne room caves in as the silver dragon bursts through. Malgrath takes\n"
            "one look at her and surrenders on the spot. She carries the Dawnstone into\n"
            "the sky, and the sun rises on her silver wings. She still visits every year\n"
            "to ask you riddles."
        ),
    },
    "end_phoenix": {
        "title": "Wings of Morning",
        "ending": (
            "The feather bursts into golden flame, and the phoenix itself blazes into\n"
            "being. It snatches the Dawnstone from Malgrath and spirals up through the\n"
            "roof, trailing fire like a comet. The sun rises behind it. Back at\n"
            "Starfall, Tobias sees the dawn and faints from joy. Professor Grimsby\n"
            "begins, slowly, to applaud."
        ),
    },
    "end_staff": {
        "title": "The Archmage",
        "ending": (
            "You level the Dawnwright Staff and speak a word you never learned but\n"
            "somehow always knew. A beam of pure sunlight hits Malgrath square in the\n"
            "chest. When the light fades, the Hollow King has become a small, extremely\n"
            "grumpy hamster. The sun rises. The hamster lives in Professor Grimsby's\n"
            "office now. They get along great."
        ),
    },
    "end_signal": {
        "title": "Heroes United",
        "ending": (
            "You light the Warden's Signal. It explodes over the Spire in a starburst of\n"
            "gold, and within minutes every Warden in Brightspire arrives: Captain\n"
            "Bastion, The Pigeon, and three hundred more. Malgrath hands over the\n"
            "Dawnstone without a fight. As the sun rises, the whole city chants\n"
            "\"{hero}! {hero}! {hero}!\"\n"
            "You never quite get used to it."
        ),
    },
    "end_kip": {
        "title": "No Powers Required",
        "ending": (
            "You nod to Kip, who has been hiding in your cape since Brightspire. While\n"
            "Malgrath is busy monologuing at you, Kip tiptoes behind the throne and\n"
            "simply unscrews the Dawnstone from his gauntlet. Malgrath never even\n"
            "noticed him. Nobody ever does. That's Kip's superpower.\n"
            "The sun rises, and Kip finally gets a real mask."
        ),
    },
    "end_gauntlet": {
        "title": "The Knockout Punch",
        "ending": (
            "You wind up and throw the hardest punch in history. The Starmetal Gauntlet\n"
            "meets Malgrath's jaw with a sound like thunder. The Hollow King sails out\n"
            "the window, across the Ashlands, and lands somewhere in the sea. The\n"
            "Dawnstone drops right into your hand. The sun rises, and {hero}\n"
            "is on the front page of every newspaper for a month."
        ),
    },
    "end_sun": {
        "title": "The New Dawn",
        "ending": (
            "You press your hands to the Dawnstone and pour in everything you have:\n"
            "every spark, every flicker, every last bit of the Ember. The stone blazes,\n"
            "the Spire shatters, and Malgrath's shadows burn away forever. The sun\n"
            "rises, and you rise with it. You're part of the sun now, the first light\n"
            "the world sees every morning. It's a good job. You only work days."
        ),
    },
    "end_hat": {
        "title": "The Hat Treaty",
        "ending": (
            "You're a candlemaker, not a hatmaker, but how hard can it be? A week later,\n"
            "you present Malgrath with the biggest, floppiest sun hat ever made. He tries\n"
            "it on. He looks in a mirror. For the first time in a thousand years, the\n"
            "Hollow King smiles. He gives back the Dawnstone, and the sun rises.\n"
            "Malgrath opens a hat shop in the Ashlands. Business is booming."
        ),
    },
    "end_dark": {
        "title": "The Shadow Apprentice",
        "ending": (
            "You take Malgrath's hand. Together, you rule the endless night. It turns\n"
            "out that ruling the endless night is mostly paperwork, and the castle is\n"
            "always freezing. You're starting to have some regrets."
        ),
    },
}

TOTAL_ENDINGS = sum(1 for scene in SCENES.values() if "ending" in scene)


def slow_print(text, delay=0.012):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def unlocked(choices, items):
    """Choices that need an item only show up if you're carrying it."""
    available = []
    for choice in choices:
        if len(choice) == 2:
            available.append(choice)
        elif choice[2] in items:
            available.append(("✨ " + choice[0], choice[1]))
    return available


def ask(choices):
    for i, (label, _) in enumerate(choices, 1):
        print(f"  {i}. {label}")
    while True:
        answer = input("\n> ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][1]
        print(f"Even heroes have to pick a number from 1 to {len(choices)}.")


def play(name, found):
    state = {"name": name, "hero": name}
    items = set()
    scene_id = "start"
    while True:
        scene = SCENES[scene_id]
        state.update(scene.get("set", {}))
        print()
        if "ending" in scene:
            print(GOLD + BOLD, end="")
            slow_print(f"*** THE END: {scene['title']} ***")
            print(RESET, end="")
            slow_print(scene["ending"].format(**state))
            found[scene_id] = scene["title"]
            print(f"\nYou've found {len(found)}/{TOTAL_ENDINGS} endings.")
            return
        slow_print(scene["text"].format(**state))
        if "gain" in scene:
            items.add(scene["gain"])
            print(f"\n{PURPLE}  ✨ Added to your inventory: {scene['gain']}{RESET}")
        if "next" in scene:
            input("\n(press Enter)")
            scene_id = scene["next"]
        else:
            print()
            scene_id = ask(unlocked(scene["choices"], items))


def main():
    print(GOLD + BANNER + RESET)
    print("        T H E   L A S T   E M B E R")
    print("     an epic choose-your-own-adventure")
    print("  of dragons, wizards, and masked heroes\n")
    found = {}
    try:
        name = input("What is your name, hero? ").strip() or "Hero"
        while True:
            play(name, found)
            if len(found) == TOTAL_ENDINGS:
                slow_print("\nYou found every ending! Bards will sing of you for a thousand years.")
                break
            if input("\nPlay again? (y/n) ").strip().lower() != "y":
                break
    except (KeyboardInterrupt, EOFError):
        print()
    if found:
        print("\nEndings you found:")
        for title in found.values():
            print(f"  - {title}")
    print("\nFarewell, hero. The Ember remembers you.")


if __name__ == "__main__":
    main()
