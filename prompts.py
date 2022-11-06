SEP = "\n<|asep|>\n"
COMMAND_SEP = "\n<|csep|>\n"
STOP_SEQ = "\n<|aeot|>"


def stringify_actor(actor: dict):
    # Name (Race/creature type; class if available) <X/Y HP> [Effects]
    short_parts = [actor["name"]]
    race_and_class_parts = []
    if actor["race"]:
        race_and_class_parts.append(actor["race"])
    if actor["class"]:
        race_and_class_parts.append(actor["class"])
    race_and_class = "; ".join(race_and_class_parts)

    if race_and_class:
        short_parts.append(f"({race_and_class})")
    short_parts.append(actor["hp"])
    if actor["effects"]:
        short_parts.append(f"[{actor['effects']}]")

    # Description: ...
    #
    # ---
    description = ""
    if actor["description"]:
        description = f"Description: {actor['description']}\n---\n"

    # Name: NAME
    # Class:
    # Race:
    # Attacks:
    # Spells:
    # Actions:
    # Effects:
    long_parts = [f"Name: {actor['name']}"]
    if actor["class"]:
        long_parts.append(f"Class: {actor['class']}")
    if actor["race"]:
        long_parts.append(f"Race: {actor['race']}")
    if actor["attacks"]:
        long_parts.append(f"Attacks: {actor['attacks']}")
    if actor["spells"]:
        long_parts.append(f"Spells: {actor['spells']}")
    if actor["actions"]:
        long_parts.append(f"Actions: {actor['actions']}")
    if actor["effects"]:
        long_parts.append(f"Effects: {actor['effects']}")

    return {"short": " ".join(short_parts), "long": "\n".join(long_parts), "description": description}


def utt_cmd_prompt(data, include_sep=True) -> str | None:
    before = data["before_utterances"]
    state_before = data["combat_state_before"]
    current = data["current_actor"]

    # if no before utterances, skip
    if not before:
        return

    # prompt:
    # Actors:
    # - Name (Race/creature type; class if available) <X/Y HP> [Effects]
    # - ...
    #
    # Current:
    # Name: NAME
    # Class:
    # Race:
    # Attacks:
    # Spells:
    # Actions:
    # Effects:
    #
    # RP
    # <|asep|>

    # completion:
    # command
    # <|aeot|>
    prompt_parts = []
    actors = [f"- {stringify_actor(a)['short']}" for a in state_before]
    actors_prompt = f"Actors:\n" + "\n".join(actors)
    if actors:
        prompt_parts.append(actors_prompt)

    if current is not None:
        prompt_parts.append(f"Current:\n{stringify_actor(current)['long']}")
    else:
        prompt_parts.append("Current:\nNone")

    rp = "\n".join(before)
    prompt_parts.append(rp)

    # TODO: run ablation by removing parts of the prompt

    return "\n\n".join(prompt_parts) + (SEP if include_sep else "")


def utt_cmd_completion(data, include_sep=True, command_sep=COMMAND_SEP) -> str | None:
    commands = data["commands_norm"]
    return command_sep.join(commands) + (STOP_SEQ if include_sep else "")


def sta_nar_prompt(data, include_sep=True) -> str | None:
    state_after = data["combat_state_after"]
    caster = data["caster_after"]
    targets = data["targets_after"]
    automation_results = data["automation_results"]

    # prompt:
    # Actors: (state after)
    # - Name (Race/creature type; class if available) <X/Y HP> [Effects]
    # - ...
    #
    # Targets: (pulled from after)
    # - Name (Race/creature type; class if available) <X/Y HP>
    # - ...
    #
    # Description: ... (pulled from after)
    #
    # ---
    # Name: NAME
    # Class:
    # Race:
    # Attacks:
    # Spells:
    # Actions:
    # Effects:
    #
    # AUTOMATION_STRINGIFY
    # <|asep|>

    # completion:
    # after
    # <|aeot|>

    prompt_parts = []

    actors = [f"- {stringify_actor(a)['short']}" for a in state_after]
    actors_prompt = f"Actors:\n" + "\n".join(actors)
    if actors:
        prompt_parts.append(actors_prompt)

    targets_str = [f"- {stringify_actor(a)['short']}" for a in targets]
    targets_prompt = f"Targets:\n" + "\n".join(targets_str)
    if targets:
        prompt_parts.append(targets_prompt)

    caster_strs = stringify_actor(caster)
    prompt_parts.append(f"{caster_strs['description']}{caster_strs['long']}")

    prompt_parts.append("\n".join(automation_results))

    # TODO: run ablation by removing parts of the prompt

    return "\n\n".join(prompt_parts) + (SEP if include_sep else "")


def sta_nar_completion(data, include_sep=True) -> str | None:
    after = data["after_utterances"]

    # skip if no after utterances
    if not after:
        return

    # completion:
    # after
    # <|aeot|>
    return "\n".join(after) + (STOP_SEQ if include_sep else "")