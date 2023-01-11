# internal key to emoji
EMOJI_FORWARD = {
    1: "\U00000031\U000020E3",
    2: "\U00000032\U000020E3",
    3: "\U00000033\U000020E3",
    4: "\U00000034\U000020E3",
    5: "\U00000035\U000020E3",
    6: "\U00000036\U000020E3",
    7: "\U00000037\U000020E3",
    8: "\U00000038\U000020E3",
    9: "\U00000039\U000020E3",
    "checkmark": "\U00002611",
    "up-arrow": "\U00002B06",
    "down-arrow": "\U00002B07",
    "temperature": "\U0001F912",
    "busts-in-silhouette": "\U0001F465",
    "stop-sign": "\U0001F601",
}

# reverse
EMOJI_BACKWARD = {v: k for k, v in EMOJI_FORWARD.items()}
