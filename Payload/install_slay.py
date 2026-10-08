











from __future__ import annotations



import argparse

import html

import json

import os

import pathlib

import re

import shutil

import sys

import urllib.parse

import urllib.request

import xml.etree.ElementTree as ET



V02_BACKUP_SUFFIX = ".slaystarcraft_v02.bak"

OLD_BACKUP_SUFFIX = ".aprogue_poc.bak"

GAME_DATA_CATALOG_PATH = "GameData/APRogueData.xml"























LEGACY_SLAY_CAMPAIGN_DEPENDENCIES = (

    r"file:Campaigns\Swarm.SC2Campaign",

    r"file:Campaigns\SwarmStory.SC2Campaign",

    r"file:Campaigns\Void.SC2Campaign",

)

ARCHIPELAGO_TRIGGER_DEPENDENCIES = (

    r"file:Mods\ArchipelagoCore.SC2Mod",

    r"file:Mods\ArchipelagoTradeSystem.SC2Mod",

    r"file:Mods\ArchipelagoPatches.SC2Mod",

)



PY_CONSTANTS = '''\n# ----- APRogue POC: effect selection -----\nAPR_ROGUE_POC_EFFECTS = {\n    "low_quality_minerals": 1 << 0,\n    "conga_line": 1 << 1,\n    "ten_minutes_until_destruction": 1 << 2,\n    "golden_armada": 1 << 3,\n    "investors": 1 << 4,\n    "multi_class": 1 << 5,\n}\n# ----- end APRogue POC -----\n'''



PY_COMMAND = '''    # ----- APRogue POC -----\n    @mark_raw\n    def _cmd_rogue_poc(self, effects: str = "") -> bool:\n        """Debug override for APRogue effects when no Slay run is active."""\n        raw = effects.strip().lower().replace("-", "_")\n        aliases = {\n            "low_quality": "low_quality_minerals",\n            "low_quality_minerals": "low_quality_minerals",\n            "conga": "conga_line",\n            "conga_line": "conga_line",\n            "destruction": "ten_minutes_until_destruction",\n            "10_minutes_until_destruction": "ten_minutes_until_destruction",\n            "ten_minutes_until_destruction": "ten_minutes_until_destruction",\n            "golden": "golden_armada",\n            "golden_armada": "golden_armada",\n            "investors": "investors",\n            "multi_class": "multi_class",\n            "multiclass": "multi_class",\n        }\n        if not raw:\n            active = [name for name, bit in APR_ROGUE_POC_EFFECTS.items() if self.ctx.rogue_poc_mask & bit]\n            self.output("APRogue debug effects: " + (", ".join(active) if active else "none"))\n            self.output("Available: " + ", ".join(APR_ROGUE_POC_EFFECTS))\n            return True\n        if raw in {"none", "off", "0"}:\n            self.ctx.rogue_poc_mask = 0\n            self.output("APRogue debug effects disabled.")\n            return True\n        if raw == "all":\n            self.ctx.rogue_poc_mask = sum(APR_ROGUE_POC_EFFECTS.values())\n            self.output("APRogue debug: all POC effects enabled.")\n            return True\n        requested = [token for token in re.split(r"[\\s,]+", raw) if token]\n        normalized = []\n        unknown = []\n        for token in requested:\n            name = aliases.get(token)\n            if name is None:\n                unknown.append(token)\n            elif name not in normalized:\n                normalized.append(name)\n        if unknown:\n            self.output("Unknown APRogue effect(s): " + ", ".join(unknown))\n            return False\n        mask = 0\n        for name in normalized:\n            mask |= APR_ROGUE_POC_EFFECTS[name]\n        self.ctx.rogue_poc_mask = mask\n        self.output("APRogue debug effects: " + ", ".join(normalized))\n        return True\n    # ----- end APRogue POC -----\n'''





PY_TEST_COMMANDS = r'''    # ----- Slay one-mission test overrides -----
    @mark_raw
    def _cmd_addtest(self, effect: str = "") -> bool:
        """Force an effect onto the current unfinished mission, or the next selected mission."""
        ok, message = slay.queue_test_effect(self.ctx, effect)
        self.output(message)
        return ok

    def _cmd_cleartest(self) -> bool:
        """Clear effects from the current unfinished mission, or the next selected mission."""
        ok, message = slay.queue_test_clear(self.ctx)
        self.output(message)
        return ok

    def _cmd_canceltest(self) -> bool:
        """Cancel pending /addtest and /cleartest overrides."""
        ok, message = slay.cancel_test_overrides(self.ctx)
        self.output(message)
        return ok

    def _cmd_victory(self) -> bool:
        """Auto-complete the next selected Slay mission and check all its locations."""
        ok, message = slay.queue_auto_victory(self.ctx)
        self.output(message)
        return ok

    @mark_raw
    def _cmd_boon(self, boon: str = "") -> bool:
        """Grant a permanent Slay boon for testing without spending credits."""
        ok, message = slay.grant_test_boon(self.ctx, boon)
        self.output(message)
        return ok

    @mark_raw
    def _cmd_credits(self, amount: str = "") -> bool:
        """Add test credits to the current Slay run."""
        ok, message = slay.grant_test_credits(self.ctx, amount)
        self.output(message)
        return ok

    def _cmd_godmode(self) -> bool:
        """Give the next selected Slay mission unlimited testing resources and production speed."""
        ok, message = slay.queue_godmode(self.ctx)
        self.output(message)
        return ok
    # ----- end Slay one-mission test overrides -----
'''





AP_CONTENT_DOCS_URL = "https://archipelago-sc2.github.io/content-docs/"



def _parse_ap_content_docs_html(source: str) -> dict[str, dict[str, str]]:



    blocks = re.split(r'(?=<h2\b)', source, flags=re.I)

    docs: dict[str, dict[str, str]] = {}

    for block in blocks:

        title_match = re.match(r'<h2[^>]*>(.*?)</h2>', block, flags=re.I | re.S)

        if not title_match:

            continue

        title = html.unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()

        if not title:

            continue









        text_block = re.sub(r'<br\s*/?>', '\n', block, flags=re.I)

        text_block = re.sub(r'</(?:li|p|div|section|h[1-6])\s*>', '\n', text_block, flags=re.I)

        text_block = html.unescape(re.sub(r'<[^>]+>', '', text_block))

        desc_match = re.search(r'(?im)^\s*(?:[-*•]\s*)?Description:\s*(.*?)\s*$', text_block)

        description = desc_match.group(1).strip() if desc_match else ""



        icon_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', block, flags=re.I | re.S)

        icon_url = ""

        if icon_match:

            icon_url = urllib.parse.urljoin(

                AP_CONTENT_DOCS_URL,

                html.unescape(icon_match.group(1)).strip(),

            )

        if description or icon_url:

            docs[title] = {"description": description, "icon": icon_url}

    return docs





def refresh_ap_content_docs_cache(target: pathlib.Path) -> int:











    try:

        request = urllib.request.Request(

            AP_CONTENT_DOCS_URL,

            headers={"User-Agent": "SlayTheStarCraft/1.0.2.17"},

        )

        with urllib.request.urlopen(request, timeout=15) as response:

            source = response.read().decode("utf-8", errors="replace")

        docs = _parse_ap_content_docs_html(source)







        if len(docs) < 100:

            raise RuntimeError(f"content-doc parse returned only {len(docs)} items")

        for sanity_name in ("Marine", "Blood Hunter"):

            sanity = docs.get(sanity_name, {})

            if not sanity.get("description") or not sanity.get("icon"):

                raise RuntimeError(f"content-doc parse missed {sanity_name!r} metadata")



        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(json.dumps(docs, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

        return len(docs)

    except Exception as exc:

        print(f"WARNING: could not refresh Archipelago content-doc metadata: {exc}")

        return 0





def backup_path(path: pathlib.Path, suffix: str = V02_BACKUP_SUFFIX) -> pathlib.Path:

    return pathlib.Path(str(path) + suffix)





def patch_trigger_document_info(text: str) -> str:













    open_tag = "<Dependencies>"

    close_tag = "</Dependencies>"

    if text.count(open_tag) != 1 or text.count(close_tag) != 1:

        raise RuntimeError("Could not uniquely locate ArchipelagoTriggers DocumentInfo dependency block")

    start = text.index(open_tag) + len(open_tag)

    end = text.index(close_tag, start)

    block = text[start:end]

    for dep in LEGACY_SLAY_CAMPAIGN_DEPENDENCIES:





        pattern = re.compile(r"[ \t]*<Value>" + re.escape(dep) + r"</Value>[ \t]*(?:\r?\n)?")

        block = pattern.sub("", block)

    return text[:start] + block + text[end:]



def _parse_header_dependency_block(blob: bytes) -> tuple[int, int, list[bytes]]:



    known = tuple(dep.encode("utf-8") for dep in ARCHIPELAGO_TRIGGER_DEPENDENCIES)

    core = known[0]

    core_at = blob.find(core)

    if core_at < 0:

        raise RuntimeError("DocumentHeader does not contain ArchipelagoCore dependency anchor")



    candidates: list[tuple[int, int, list[bytes]]] = []

    lower = max(4, core_at - 512)

    for start in range(lower, core_at + 1):

        count = int.from_bytes(blob[start - 4:start], "little")

        if count < 1 or count > 32:

            continue

        deps: list[bytes] = []

        starts: list[int] = []

        pos = start

        ok = True

        try:

            for _ in range(count):

                end = blob.index(b"\x00", pos, min(len(blob), pos + 1024))

                value = blob[pos:end]

                if not value or not (value.startswith(b"file:") or value.startswith(b"bnet:")):

                    ok = False

                    break

                deps.append(value)

                starts.append(pos)

                pos = end + 1

        except ValueError:

            ok = False

        if not ok:

            continue

        if all(dep in deps for dep in known) and core_at in starts:

            candidates.append((start, pos, deps))



    unique: list[tuple[int, int, list[bytes]]] = []

    for candidate in candidates:

        if not any(candidate[0] == old[0] and candidate[1] == old[1] and candidate[2] == old[2] for old in unique):

            unique.append(candidate)

    if len(unique) != 1:

        raise RuntimeError(

            f"Could not uniquely locate DocumentHeader dependency block (candidates={len(unique)})"

        )

    return unique[0]





def patch_trigger_document_header(blob: bytes) -> bytes:



    start, end, deps = _parse_header_dependency_block(blob)

    legacy = {dep.encode("utf-8") for dep in LEGACY_SLAY_CAMPAIGN_DEPENDENCIES}

    new_deps = [dep for dep in deps if dep not in legacy]

    if new_deps == deps:

        return blob

    return (

        blob[:start - 4]

        + len(new_deps).to_bytes(4, "little")

        + b"".join(dep + b"\x00" for dep in new_deps)

        + blob[end:]

    )



def validate_trigger_dependency_metadata(doc_info: str, doc_header: bytes) -> None:







    for dep in LEGACY_SLAY_CAMPAIGN_DEPENDENCIES:

        short = dep.removeprefix("file:")

        if short in doc_info or dep in doc_info:

            raise RuntimeError(f"ArchipelagoTriggers DocumentInfo still contains legacy Slay dependency: {dep}")

        if short.encode("utf-8") in doc_header or dep.encode("utf-8") in doc_header:

            raise RuntimeError(f"ArchipelagoTriggers DocumentHeader still contains legacy Slay dependency: {dep}")

    for dep in ARCHIPELAGO_TRIGGER_DEPENDENCIES:

        if dep not in doc_info:

            raise RuntimeError(f"DocumentInfo lost existing dependency: {dep}")

        if dep.encode("utf-8") not in doc_header:

            raise RuntimeError(f"DocumentHeader lost existing dependency: {dep}")



def add_trigger_document_info_dependencies(text: str, dependencies: tuple[str, ...]) -> str:



    open_tag = "<Dependencies>"

    close_tag = "</Dependencies>"

    if text.count(open_tag) != 1 or text.count(close_tag) != 1:

        raise RuntimeError("Could not uniquely locate DocumentInfo dependencies while building Slay variant")

    insert_at = text.index(close_tag)

    newline = "\r\n" if "\r\n" in text else "\n"

    additions = ""

    for dep in dependencies:

        if dep not in text:

            additions += f"    <Value>{dep}</Value>{newline}"

    return text[:insert_at] + additions + text[insert_at:]





def add_trigger_document_header_dependencies(blob: bytes, dependencies: tuple[str, ...]) -> bytes:



    start, end, deps = _parse_header_dependency_block(blob)

    wanted = [dep.encode("utf-8") for dep in dependencies]

    new_deps = list(deps)

    for dep in wanted:

        if dep not in new_deps:

            new_deps.append(dep)

    return (

        blob[:start - 4]

        + len(new_deps).to_bytes(4, "little")

        + b"".join(dep + b"\x00" for dep in new_deps)

        + blob[end:]

    )





def validate_trigger_dependency_variant(doc_info: str, doc_header: bytes, expected_extra: tuple[str, ...]) -> None:

    for dep in ARCHIPELAGO_TRIGGER_DEPENDENCIES:

        if dep not in doc_info or dep.encode("utf-8") not in doc_header:

            raise RuntimeError(f"Slay dependency variant lost base dependency: {dep}")

    expected = set(expected_extra)

    for dep in LEGACY_SLAY_CAMPAIGN_DEPENDENCIES:

        info_has = dep in doc_info or dep.removeprefix("file:") in doc_info

        header_has = dep.encode("utf-8") in doc_header or dep.removeprefix("file:").encode("utf-8") in doc_header

        if dep in expected:

            if not info_has or not header_has:

                raise RuntimeError(f"Slay dependency variant is missing required dependency: {dep}")

        elif info_has or header_has:

            raise RuntimeError(f"Slay dependency variant contains unexpected dependency: {dep}")





def insert_after_unique_line(text: str, anchor: str, addition: str, description: str) -> str:

    if addition.strip() in text:

        return text

    count = text.count(anchor)

    if count != 1:

        raise RuntimeError(f"Expected exactly one {description} anchor, found {count}; refusing to guess")

    pos = text.index(anchor)

    end = text.find("\n", pos)

    if end < 0:

        raise RuntimeError(f"{description} anchor had no terminating newline")

    return text[:end + 1] + addition + text[end + 1:]





def insert_before_unique(text: str, anchor: str, addition: str, description: str) -> str:

    if addition.strip() in text:

        return text

    count = text.count(anchor)

    if count != 1:

        raise RuntimeError(f"Expected exactly one {description} anchor, found {count}; refusing to guess")

    pos = text.index(anchor)

    return text[:pos] + addition + text[pos:]





def ensure_debug_poc(text: str) -> str:

    if "APR_ROGUE_POC_EFFECTS" not in text:

        text = insert_after_unique_line(text, "MAX_BONUS: int = 28", PY_CONSTANTS, "MAX_BONUS")

    if "def _cmd_rogue_poc" not in text:

        class_anchor = "class StarcraftClientProcessor(ClientCommandProcessor):"

        if text.count(class_anchor) != 1:

            raise RuntimeError("Could not uniquely locate StarcraftClientProcessor")

        class_start = text.index(class_anchor)

        next_class = text.find("\nclass ", class_start + len(class_anchor))

        class_end = len(text) if next_class < 0 else next_class

        formatted = text.find("    def formatted_print(", class_start, class_end)

        if formatted < 0 or text.find("    def formatted_print(", formatted + 1, class_end) >= 0:

            raise RuntimeError("Could not uniquely locate StarcraftClientProcessor.formatted_print")

        text = text[:formatted] + PY_COMMAND + text[formatted:]

    if "def _cmd_addtest" in text and "def _cmd_victory" not in text:

        old_cancel = '''    def _cmd_canceltest(self) -> bool:
        """Cancel pending /addtest and /cleartest overrides."""
        ok, message = slay.cancel_test_overrides(self.ctx)
        self.output(message)
        return ok
'''

        victory_command = '''
    def _cmd_victory(self) -> bool:
        """Auto-complete the next selected Slay mission and check all its locations."""
        ok, message = slay.queue_auto_victory(self.ctx)
        self.output(message)
        return ok
'''

        if old_cancel not in text:

            raise RuntimeError("Could not locate existing Slay test command block for /victory migration")

        text = text.replace(old_cancel, old_cancel + victory_command, 1)

    if "def _cmd_victory" in text and "def _cmd_boon" not in text:

        old_victory = '''    def _cmd_victory(self) -> bool:
        """Auto-complete the next selected Slay mission and check all its locations."""
        ok, message = slay.queue_auto_victory(self.ctx)
        self.output(message)
        return ok
'''

        boon_command = '''
    @mark_raw
    def _cmd_boon(self, boon: str = "") -> bool:
        """Grant a permanent Slay boon for testing without spending credits."""
        ok, message = slay.grant_test_boon(self.ctx, boon)
        self.output(message)
        return ok
'''

        if old_victory not in text:

            raise RuntimeError("Could not locate existing /victory command block for /boon migration")

        text = text.replace(old_victory, old_victory + boon_command, 1)

    if "def _cmd_boon" in text and "def _cmd_credits" not in text:

        old_boon = '''    @mark_raw
    def _cmd_boon(self, boon: str = "") -> bool:
        """Grant a permanent Slay boon for testing without spending credits."""
        ok, message = slay.grant_test_boon(self.ctx, boon)
        self.output(message)
        return ok
'''

        credits_command = '''
    @mark_raw
    def _cmd_credits(self, amount: str = "") -> bool:
        """Add test credits to the current Slay run."""
        ok, message = slay.grant_test_credits(self.ctx, amount)
        self.output(message)
        return ok
'''

        if old_boon not in text:

            raise RuntimeError("Could not locate existing /boon command block for /credits migration")

        text = text.replace(old_boon, old_boon + credits_command, 1)

    if "def _cmd_credits" in text and "def _cmd_godmode" not in text:

        old_credits = '''    @mark_raw
    def _cmd_credits(self, amount: str = "") -> bool:
        """Add test credits to the current Slay run."""
        ok, message = slay.grant_test_credits(self.ctx, amount)
        self.output(message)
        return ok
'''

        godmode_command = '''
    def _cmd_godmode(self) -> bool:
        """Give the next selected Slay mission unlimited testing resources and production speed."""
        ok, message = slay.queue_godmode(self.ctx)
        self.output(message)
        return ok
'''

        if old_credits not in text:

            raise RuntimeError("Could not locate existing /credits command block for /godmode migration")

        text = text.replace(old_credits, old_credits + godmode_command, 1)

    if "def _cmd_addtest" not in text:

        class_anchor = "class StarcraftClientProcessor(ClientCommandProcessor):"

        if text.count(class_anchor) != 1:

            raise RuntimeError("Could not uniquely locate StarcraftClientProcessor for Slay test commands")

        class_start = text.index(class_anchor)

        next_class = text.find("\nclass ", class_start + len(class_anchor))

        class_end = len(text) if next_class < 0 else next_class

        formatted = text.find("    def formatted_print(", class_start, class_end)

        if formatted < 0 or text.find("    def formatted_print(", formatted + 1, class_end) >= 0:

            raise RuntimeError("Could not uniquely locate StarcraftClientProcessor.formatted_print for Slay test commands")

        text = text[:formatted] + PY_TEST_COMMANDS + text[formatted:]

    if "self.rogue_poc_mask" not in text:

        text = insert_after_unique_line(

            text, "        self.war_council_nerfs: bool = False",

            "        # APRogue debug bitmask when no Slay run is active.\n        self.rogue_poc_mask: int = 0\n",

            "SC2Context.war_council_nerfs",

        )

    return text





def patch_client(text: str) -> str:

    text = ensure_debug_poc(text)



    if "from . import slay_the_starcraft as slay" not in text:

        text = insert_after_unique_line(text, "from . import SC2World", "from . import slay_the_starcraft as slay\n", "SC2World import")











    stock_update_guard = re.compile(

        r'^(?P<indent>[ \t]*)if is_mod_update_available\(DATA_REPO_OWNER, DATA_REPO_NAME, DATA_API_VERSION, current_ver\):$',

        re.MULTILINE,

    )

    update_guard_matches = list(stock_update_guard.finditer(text))

    if len(update_guard_matches) > 1:

        raise RuntimeError("Could not uniquely guard the SC2 data update check for the Slay launcher")

    if update_guard_matches:

        text = stock_update_guard.sub(

            r'\g<indent>if os.environ.get("SLAY_MANAGED_SC2_DATA") != "1" and is_mod_update_available(DATA_REPO_OWNER, DATA_REPO_NAME, DATA_API_VERSION, current_ver):',

            text,

            count=1,

        )



    init_line = "            slay.initialize_context(self)  # Slay the StarCraft v0.2\n"

    if "slay.initialize_context(self)" not in text:

        text = insert_after_unique_line(text, "            self.build_location_to_mission_mapping()", init_line, "mission mapping")









    if "slay.prepare_dependency_variant(ctx, mission_id)" not in text:

        pattern = re.compile(r"^(async def starcraft_launch\([^\n]+\):\n)", re.MULTILINE)

        match = pattern.search(text)

        if match is not None:

            dependency_line = "    slay.prepare_dependency_variant(ctx, mission_id)  # Slay dependency variant\n"

            text = text[:match.end()] + dependency_line + text[match.end():]

        elif "starcraft_launch" in text:

            raise RuntimeError("Found starcraft_launch but could not patch Slay dependency selection")













    legacy_print_override = re.compile(

        r"\n    def on_print_json\(self, args: dict\) -> None:\n"

        r"        super\(\)\.on_print_json\(slay\.rewrite_print_json_for_effective_rewards\(self, args\)\)  # Slay the StarCraft v[0-9]+\.[0-9]+\.[0-9]+\n\n"

    )

    text = legacy_print_override.sub("\n", text)

    rewrite_line = "        args = slay.rewrite_print_json_for_effective_rewards(self, args)  # Slay the StarCraft v1.0.2.17\n"

    existing_rewrite = re.compile(

        r"        args = slay\.rewrite_print_json_for_effective_rewards\(self, args\)  # Slay the StarCraft v[0-9]+\.[0-9]+\.[0-9]+\n"

    )

    rewrite_matches = list(existing_rewrite.finditer(text))

    if len(rewrite_matches) > 1:

        raise RuntimeError("Multiple active Slay PrintJSON reward rewrites found")

    if len(rewrite_matches) == 1:

        text = existing_rewrite.sub(rewrite_line, text, count=1)

    else:

        class_anchor = "class SC2Context"

        class_start = text.find(class_anchor)

        if class_start < 0:

            raise RuntimeError("Could not locate SC2Context for Slay PrintJSON reward rewriting")

        class_end = text.find("\nclass ", class_start + len(class_anchor))

        if class_end < 0:

            class_end = len(text)

        method_anchor = "    def on_print_json(self, args: dict) -> None:\n"

        method_at = text.find(method_anchor, class_start, class_end)

        if method_at >= 0:

            if text.find(method_anchor, method_at + 1, class_end) >= 0:

                raise RuntimeError("Multiple SC2Context.on_print_json methods remain after legacy cleanup")

            insert_at = method_at + len(method_anchor)

            text = text[:insert_at] + rewrite_line + text[insert_at:]

        else:





            method = (

                "    def on_print_json(self, args: dict) -> None:\n"

                + rewrite_line

                + "        super().on_print_json(args)\n\n"

            )

            server_auth_anchor = "    async def server_auth(self, password_requested: bool = False) -> None:"

            connected_anchor = "    def connected(self):"

            if server_auth_anchor in text[class_start:class_end]:

                absolute = text.find(server_auth_anchor, class_start, class_end)

                text = text[:absolute] + method + text[absolute:]

            elif connected_anchor in text[class_start:class_end]:

                absolute = text.find(connected_anchor, class_start, class_end)

                text = text[:absolute] + method + text[absolute:]

            else:

                raise RuntimeError("Could not locate an SC2Context method anchor for Slay PrintJSON reward rewriting")



    play_marker = "        # Slay the StarCraft v0.2: branch commitment / completed-node lockout.\n"

    legacy_play_block = (

        play_marker

        + "        if slay.enabled(self) and (self.missions_unlocked or is_mission_available(self, mission_id)) and not slay.commit_mission(self, mission_id):\n"

        + "            sc2_logger.info(\"Slay the StarCraft: that mission is not on the current route.\")\n"

        + "            return False\n"

    )

    current_play_block = (

        play_marker

        + "        if slay.enabled(self) and (self.missions_unlocked or is_mission_available(self, mission_id)):\n"

        + "            if not slay.commit_mission(self, mission_id):\n"

        + "                sc2_logger.info(\"Slay the StarCraft: that mission is not on the current route.\")\n"

        + "                return False\n"

        + "            if slay.consume_auto_victory_skip(self, mission_id):\n"

        + "                sc2_logger.info(\"Slay the StarCraft: /victory completed the selected mission without launching SC2.\")\n"

        + "                return False\n"

    )

    if legacy_play_block in text:

        text = text.replace(legacy_play_block, current_play_block, 1)

    elif play_marker.strip() not in text:

        anchor = "    def play_mission(self, mission_id: int) -> bool:\n"

        text = insert_after_unique_line(text, anchor.rstrip("\n"), current_play_block, "play_mission definition")

    elif "slay.consume_auto_victory_skip(self, mission_id)" not in text:

        raise RuntimeError("Found an unfamiliar Slay play_mission patch; refusing to guess while adding /victory")



    augment_line = "    slay.augment_network_items(ctx, items, item_list)  # Slay the StarCraft v0.2\n"

    if "slay.augment_network_items(ctx, items, item_list)" not in text:

        text = insert_after_unique_line(text, "    item_list = get_full_item_list()", augment_line, "calculate_items item list")









    bank_send = (

        '            mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay.effect_masks_for_mission(self.ctx, self.mission_id)  # Slay the StarCraft v1.0.2.17\n'

        '            auto_repair_stacks = slay.auto_repair_stacks(self.ctx)\n'

        '            progression_flags = slay.progression_flags(self.ctx)\n'

        '            spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)\n'

        '            mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)\n'

        '            mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n'

        '            test_potion_run_token = slay.test_potion_run_token(self.ctx)\n'

        '            spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)\n'

        '            kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)\n'

        '            deadly_weapons_stacks = slay.deadly_weapons_stacks(self.ctx)\n'

        '            commander_hero_index = slay.commander_hero_index(self.ctx, self.mission_id)\n'

        '            godmode = slay.godmode_for_mission(self.ctx, self.mission_id)\n'

        '            mission_layer = slay.mission_layer_for_mission(self.ctx, self.mission_id)\n'

        '            mission_flags = slay.mission_flags_for_mission(self.ctx, self.mission_id)\n'

        '            sc2_logger.info(slay.mission_launch_summary(self.ctx, self.mission_id))\n'

        '            slay.announce_mission_effects(self.ctx, self.mission_id)\n'

        '            await self.chat_send(f"?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}")\n'

    )

    current_send = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}'

    previous_send_with_merc2 = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2}'

    previous_send_with_mission_flags = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags}'

    previous_send_with_mission_layer = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer}'

    previous_send_with_deadly = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks}'

    previous_send = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed}'

    legacy_previous_send = '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks}'

    old_slay_send = '            await self.chat_send(f"?APRogue {slay.effect_mask_for_mission(self.ctx, self.mission_id)}")  # Slay the StarCraft v0.2\n'

    old_debug_send = '            await self.chat_send(f"?APRogue {self.ctx.rogue_poc_mask}")\n'

    if old_slay_send in text:

        text = text.replace(old_slay_send, bank_send, 1)

    elif old_debug_send in text:

        text = text.replace(old_debug_send, bank_send, 1)

    elif "slay.effect_masks_for_mission(self.ctx, self.mission_id)" not in text:

        text = insert_before_unique(text, '            await self.chat_send("?LoadFinished")', bank_send, "LoadFinished")

    elif '?APRogueA' in text or '?APRogueB' in text:

        pattern = re.compile(

            r'\s*mask_a, mask_b(?:, mask_c)?(?:, mask_d)?(?:, mask_e)?(?:, mask_f)? = slay\.effect_masks_for_mission\(self\.ctx, self\.mission_id\)[^\n]*\n'

            r'(?:\s*auto_repair_stacks = slay\.auto_repair_stacks\(self\.ctx\)\n)?'

            r'(?:\s*sc2_logger\.info\(slay\.mission_launch_summary\(self\.ctx, self\.mission_id\)\)\n)?'

            r'\s*await self\.chat_send\(f"\?APRogueA \{mask_a\}"\)\n'

            r'\s*await self\.chat_send\(f"\?APRogueB \{mask_b\}"\)\n'

        )

        text, count = pattern.subn("\n" + bank_send.rstrip("\n") + "\n", text, count=1)

        if count != 1:

            raise RuntimeError(f"Could not uniquely upgrade old dual-bank APRogue send; replaced {count}")

    elif current_send not in text:

        if previous_send_with_merc2 in text or previous_send_with_mission_flags in text or previous_send_with_mission_layer in text or previous_send_with_deadly in text or previous_send in text or legacy_previous_send in text:

            if previous_send_with_merc2 in text:

                source_send = previous_send_with_merc2

            elif previous_send_with_mission_flags in text:

                source_send = previous_send_with_mission_flags

            elif previous_send_with_mission_layer in text:

                source_send = previous_send_with_mission_layer

            elif previous_send_with_deadly in text:

                source_send = previous_send_with_deadly

            else:

                source_send = previous_send if previous_send in text else legacy_previous_send

            assignment = re.compile(

                r'^(?P<indent>\s*)mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay\.effect_masks_for_mission\(self\.ctx, self\.mission_id\)[^\n]*\n'

                r'(?P=indent)auto_repair_stacks = slay\.auto_repair_stacks\(self\.ctx\)\n'

                r'(?:(?P=indent)progression_flags = slay\.progression_flags\(self\.ctx\)\n)?'

                r'(?:(?P=indent)spear_energy_regen_stacks = slay\.spear_energy_regen_stacks\(self\.ctx\)\n)?'

                r'(?:(?P=indent)mercenary_upgrade_packed = slay\.mercenary_upgrade_packed\(self\.ctx\)\n)?'

                r'(?:(?P=indent)mercenary_upgrade_packed2 = slay\.mercenary_upgrade_packed2\(self\.ctx\)\n)?'

                r'(?:(?P=indent)spear_cooldown_reduction_stacks = slay\.spear_cooldown_reduction_stacks\(self\.ctx\)\n)?'

                r'(?:(?P=indent)kerrigan_upgrade_flags = slay\.kerrigan_upgrade_flags\(self\.ctx\)\n)?'

                r'(?:(?P=indent)deadly_weapons_stacks = slay\.deadly_weapons_stacks\(self\.ctx\)\n)?'

                r'(?:(?P=indent)commander_hero_index = slay\.commander_hero_index\(self\.ctx, self\.mission_id\)\n)?'

                r'(?:(?P=indent)godmode = slay\.godmode_for_mission\(self\.ctx, self\.mission_id\)\n)?'

                r'(?:(?P=indent)mission_layer = slay\.mission_layer_for_mission\(self\.ctx, self\.mission_id\)\n)?'

                r'(?:(?P=indent)mission_flags = slay\.mission_flags_for_mission\(self\.ctx, self\.mission_id\)\n)?',

                re.MULTILINE,

            )

            match = assignment.search(text)

            if match is None:

                raise RuntimeError("Could not locate v0.2.78 six-bank APRogue assignment while adding progression scalars")

            indent = match.group("indent")

            replacement = (

                indent + 'mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay.effect_masks_for_mission(self.ctx, self.mission_id)  # Slay the StarCraft v1.0.2.17\n'

                + indent + 'auto_repair_stacks = slay.auto_repair_stacks(self.ctx)\n'

                + indent + 'progression_flags = slay.progression_flags(self.ctx)\n'

                + indent + 'spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)\n'

                + indent + 'mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)\n'

                + indent + 'mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n'

                + indent + 'spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)\n'

                + indent + 'kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)\n'

                + indent + 'deadly_weapons_stacks = slay.deadly_weapons_stacks(self.ctx)\n'

                + indent + 'commander_hero_index = slay.commander_hero_index(self.ctx, self.mission_id)\n'

                + indent + 'godmode = slay.godmode_for_mission(self.ctx, self.mission_id)\n'

                + indent + 'mission_layer = slay.mission_layer_for_mission(self.ctx, self.mission_id)\n'

                + indent + 'mission_flags = slay.mission_flags_for_mission(self.ctx, self.mission_id)\n'

            )

            text = text[:match.start()] + replacement + text[match.end():]

            text = text.replace(source_send, current_send, 1)

        else:

            old_formats = (

                (5, 'mask_a, mask_b, mask_c, mask_d, mask_e', '?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e}'),

                (4, 'mask_a, mask_b, mask_c, mask_d', '?APRogue {mask_a} {mask_b} {mask_c} {mask_d}'),

                (3, 'mask_a, mask_b, mask_c', '?APRogue {mask_a} {mask_b} {mask_c}'),

                (2, 'mask_a, mask_b', '?APRogue {mask_a} {mask_b}'),

            )

            upgraded = False

            for bank_count, assignment_vars, send_fmt in old_formats:

                if send_fmt not in text:

                    continue

                assignment_pattern = re.compile(

                    rf'^(?P<indent>\s*){re.escape(assignment_vars)} = slay\.effect_masks_for_mission\(self\.ctx, self\.mission_id\)[^\n]*$',

                    re.MULTILINE,

                )

                text, assignment_count = assignment_pattern.subn(

                    r'\g<indent>mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay.effect_masks_for_mission(self.ctx, self.mission_id)  # Slay the StarCraft v1.0.2.17\n'

                    r'\g<indent>auto_repair_stacks = slay.auto_repair_stacks(self.ctx)\n'

                    r'\g<indent>progression_flags = slay.progression_flags(self.ctx)\n'

                    r'\g<indent>spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)\n'

                    r'\g<indent>mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)\n'

                    r'\g<indent>mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n'

                    r'\g<indent>spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)\n'

                    r'\g<indent>kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)',

                    text,

                    count=1,

                )

                if assignment_count != 1:

                    raise RuntimeError(f"Could not uniquely upgrade {bank_count}-bank APRogue assignment; replaced {assignment_count}")

                text = text.replace(

                    f'            await self.chat_send(f"{send_fmt}")\n',

                    '            await self.chat_send(f"?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}")\n',

                    1,

                )

                upgraded = True

                break

            if not upgraded:

                raise RuntimeError("Existing Slay mask code found but no recognized APRogue send format")





    text = re.sub(

        r'^(?P<indent>\s*)mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay\.effect_masks_for_mission\(self\.ctx, self\.mission_id\)[^\n]*$',

        r'\g<indent>mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay.effect_masks_for_mission(self.ctx, self.mission_id)  # Slay the StarCraft v1.0.2.17',

        text, count=1, flags=re.MULTILINE,

    )

    if "auto_repair_stacks = slay.auto_repair_stacks(self.ctx)" not in text:

        six_assignment = '            mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = slay.effect_masks_for_mission(self.ctx, self.mission_id)  # Slay the StarCraft v1.0.2.17\n'

        if six_assignment not in text:

            raise RuntimeError("Could not locate six-bank assignment while adding Auto-repair stack scalar")

        text = text.replace(six_assignment, six_assignment + '            auto_repair_stacks = slay.auto_repair_stacks(self.ctx)\n', 1)

    auto_line = '            auto_repair_stacks = slay.auto_repair_stacks(self.ctx)\n'

    if "progression_flags = slay.progression_flags(self.ctx)" not in text:

        if auto_line not in text:

            raise RuntimeError("Could not locate Auto-repair scalar while adding Slay progression flags")

        text = text.replace(auto_line, auto_line + '            progression_flags = slay.progression_flags(self.ctx)\n', 1)

    progression_line = '            progression_flags = slay.progression_flags(self.ctx)\n'

    if "spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)" not in text:

        if progression_line not in text:

            raise RuntimeError("Could not locate progression scalar while adding Spear energy regeneration")

        text = text.replace(progression_line, progression_line + '            spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)\n', 1)

    spear_line = '            spear_energy_regen_stacks = slay.spear_energy_regen_stacks(self.ctx)\n'

    if "mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)" not in text:

        if spear_line not in text:

            raise RuntimeError("Could not locate Spear scalar while adding mercenary upgrade state")

        text = text.replace(spear_line, spear_line + '            mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)\n', 1)

    merc_line = '            mercenary_upgrade_packed = slay.mercenary_upgrade_packed(self.ctx)\n'

    if "mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)" not in text:

        if merc_line not in text:

            raise RuntimeError("Could not locate mercenary scalar while adding newer mercenary upgrade state")

        text = text.replace(merc_line, merc_line + '            mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n', 1)

    merc2_line = '            mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n'

    if "spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)" not in text:

        if merc2_line not in text:

            raise RuntimeError("Could not locate newer mercenary scalar while adding Spear cooldown-reduction state")

        text = text.replace(merc2_line, merc2_line + '            spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)\n', 1)

    spear_cooldown_line = '            spear_cooldown_reduction_stacks = slay.spear_cooldown_reduction_stacks(self.ctx)\n'

    if "kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)" not in text:

        if spear_cooldown_line not in text:

            raise RuntimeError("Could not locate Spear cooldown scalar while adding Kerrigan shop-upgrade flags")

        text = text.replace(spear_cooldown_line, spear_cooldown_line + '            kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)\n', 1)



    kerrigan_flags_line = '            kerrigan_upgrade_flags = slay.kerrigan_upgrade_flags(self.ctx)\n'

    if "deadly_weapons_stacks = slay.deadly_weapons_stacks(self.ctx)" not in text:

        if kerrigan_flags_line not in text:

            raise RuntimeError("Could not locate Kerrigan flags while adding Deadly Weapons stack scalar")

        text = text.replace(kerrigan_flags_line, kerrigan_flags_line + '            deadly_weapons_stacks = slay.deadly_weapons_stacks(self.ctx)\n', 1)



    deadly_weapons_line = '            deadly_weapons_stacks = slay.deadly_weapons_stacks(self.ctx)\n'

    if "commander_hero_index = slay.commander_hero_index(self.ctx, self.mission_id)" not in text:

        if deadly_weapons_line not in text:

            raise RuntimeError("Could not locate Deadly Weapons scalar while adding Commander hero index")

        text = text.replace(deadly_weapons_line, deadly_weapons_line + '            commander_hero_index = slay.commander_hero_index(self.ctx, self.mission_id)\n', 1)



    commander_line = '            commander_hero_index = slay.commander_hero_index(self.ctx, self.mission_id)\n'

    if "godmode = slay.godmode_for_mission(self.ctx, self.mission_id)" not in text:

        if commander_line not in text:

            raise RuntimeError("Could not locate Commander hero index while adding /godmode mission scalar")

        text = text.replace(commander_line, commander_line + '            godmode = slay.godmode_for_mission(self.ctx, self.mission_id)\n', 1)



    godmode_line = '            godmode = slay.godmode_for_mission(self.ctx, self.mission_id)\n'

    if "mission_layer = slay.mission_layer_for_mission(self.ctx, self.mission_id)" not in text:

        if godmode_line not in text:

            raise RuntimeError("Could not locate /godmode scalar while adding mission-layer scalar")

        text = text.replace(godmode_line, godmode_line + '            mission_layer = slay.mission_layer_for_mission(self.ctx, self.mission_id)\n', 1)



    mission_layer_line = '            mission_layer = slay.mission_layer_for_mission(self.ctx, self.mission_id)\n'

    if "mission_flags = slay.mission_flags_for_mission(self.ctx, self.mission_id)" not in text:

        if mission_layer_line not in text:

            raise RuntimeError("Could not locate mission-layer scalar while adding mission flags")

        text = text.replace(mission_layer_line, mission_layer_line + '            mission_flags = slay.mission_flags_for_mission(self.ctx, self.mission_id)\n', 1)





    potion_assignment_line = '            test_potion_run_token = slay.test_potion_run_token(self.ctx)\n'
    if potion_assignment_line not in text:
        merc2_line = '            mercenary_upgrade_packed2 = slay.mercenary_upgrade_packed2(self.ctx)\n'
        if merc2_line in text:
            text = text.replace(merc2_line, merc2_line + potion_assignment_line, 1)

    if previous_send_with_merc2 in text and current_send not in text:
        text = text.replace(previous_send_with_merc2, current_send, 1)

    if previous_send_with_mission_layer in text and current_send not in text:

        text = text.replace(previous_send_with_mission_layer, current_send, 1)







    if previous_send_with_deadly in text and current_send not in text:

        text = text.replace(previous_send_with_deadly, current_send, 1)



    if "slay.announce_mission_effects(self.ctx, self.mission_id)" not in text:

        summary_line = '            sc2_logger.info(slay.mission_launch_summary(self.ctx, self.mission_id))\n'

        announce_line = '            slay.announce_mission_effects(self.ctx, self.mission_id)\n'

        if summary_line in text:

            text = text.replace(summary_line, summary_line + announce_line, 1)

        else:

            send_line = '            await self.chat_send(f"?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}")\n'

            if send_line not in text:

                raise RuntimeError("Could not locate current APRogue send while adding mission announcement")

            text = text.replace(send_line, announce_line + send_line, 1)









    # Normalize Kerrigan before Archipelago calculates the packed mission options.
    # This is required in addition to the post-pack availability bit override.
    if "slay.prepare_kerrigan_options(self.ctx)" not in text:

        pattern = re.compile(

            r'^(?P<indent>\s*)kerrigan_options = calculate_kerrigan_options\(self\.ctx\)(?P<tail>[^\n]*)$',

            re.MULTILINE,

        )

        match = pattern.search(text)

        if match is not None:

            prepare_line = (

                match.group("indent")

                + "slay.prepare_kerrigan_options(self.ctx)  # Slay the StarCraft v1.0.2.17\n"

            )

            text = text[:match.start()] + prepare_line + text[match.start():]



    if "slay.apply_kerrigan_options(self.ctx, self.mission_id, kerrigan_options)" not in text:

        pattern = re.compile(

            r'^(?P<indent>\s*)kerrigan_options = calculate_kerrigan_options\(self\.ctx\)(?P<tail>[^\n]*)$',

            re.MULTILINE,

        )

        match = pattern.search(text)

        if match is not None:

            replacement = (

                match.group(0) + "\n" + match.group("indent")

                + "kerrigan_options = slay.apply_kerrigan_options(self.ctx, self.mission_id, kerrigan_options)  # Slay the StarCraft v1.0.2.17"

            )

            text = text[:match.start()] + replacement + text[match.end():]









    if "slay.apply_spear_options(self.ctx, self.mission_id, soa_options)" not in text:

        pattern = re.compile(

            r'^(?P<indent>\s*)soa_options = caclulate_soa_options\(self\.ctx, mission\)(?P<tail>[^\n]*)$',

            re.MULTILINE,

        )

        match = pattern.search(text)

        if match is not None:

            replacement = (

                match.group(0) + "\n" + match.group("indent")

                + "soa_options = slay.apply_spear_options(self.ctx, self.mission_id, soa_options)  # Slay the StarCraft v1.0.2.17"

            )

            text = text[:match.start()] + replacement + text[match.end():]









    if "slay.apply_purchased_kerrigan_tech(self.ctx, zerg_items)" not in text:

        pattern = re.compile(

            r'^(?P<indent>\s*)zerg_items = current_items\[SC2Race\.ZERG\](?P<tail>[^\n]*)$',

            re.MULTILINE,

        )

        match = pattern.search(text)

        if match is None:

            raise RuntimeError("Could not locate updateZergTech zerg_items assignment for Slay Kerrigan tech")

        replacement = (

            match.group(0) + "\n" + match.group("indent")

            + "zerg_items = slay.apply_purchased_kerrigan_tech(self.ctx, zerg_items)  # Slay the StarCraft v1.0.2.17"

        )

        text = text[:match.start()] + replacement + text[match.end():]



    return text





def patch_gui(text: str) -> str:

    if "from . import slay_the_starcraft as slay" not in text:

        text = insert_after_unique_line(text, "from . import SC2World", "from . import slay_the_starcraft as slay\n", "GUI SC2World import")

    if "from . import slay_launcher" not in text:

        text = insert_after_unique_line(text, "from . import slay_the_starcraft as slay", "from . import slay_launcher\n", "GUI Slay runtime import")

    if "from kivy.uix.boxlayout import BoxLayout" not in text:

        text = insert_after_unique_line(text, "from kivy.uix.gridlayout import GridLayout", "from kivy.uix.boxlayout import BoxLayout\n", "GridLayout import")

    if "from kivy.uix.popup import Popup" not in text:

        text = insert_after_unique_line(text, "from kivy.uix.scrollview import ScrollView", "from kivy.uix.popup import Popup\n", "ScrollView import")

    if "from kivy.uix.image import AsyncImage" not in text:

        text = insert_after_unique_line(text, "from kivy.uix.popup import Popup", "from kivy.uix.image import AsyncImage\n", "Popup import")

    if "from kivy.loader import Loader" not in text:

        text = insert_after_unique_line(text, "from kivy.uix.image import AsyncImage", "from kivy.loader import Loader\n", "AsyncImage import")

    if "from kivy.graphics import Color, Line, Rectangle" not in text:

        if "from kivy.graphics import Color, Line" in text:

            if text.count("from kivy.graphics import Color, Line") != 1:

                raise RuntimeError("Found multiple Kivy Color/Line imports; refusing to guess")

            text = text.replace("from kivy.graphics import Color, Line", "from kivy.graphics import Color, Line, Rectangle", 1)

        else:

            text = insert_after_unique_line(text, "from kivy.properties import StringProperty, BooleanProperty, NumericProperty", "from kivy.graphics import Color, Line, Rectangle\n", "Kivy properties import")

    if "from kivy.graphics.instructions import InstructionGroup" not in text:

        text = insert_after_unique_line(text, "from kivy.graphics import Color, Line, Rectangle", "from kivy.graphics.instructions import InstructionGroup\n", "Kivy graphics import")



    init_add = (

        "        # Slay the StarCraft v0.2 UI state.\n"

        "        self.last_slay_signature = ()\n"

        "        self.slay_edge_group = None\n"

        "        self.slay_edge_retry_count = 0\n"

        "        self.slay_edge_last_geometry = None\n"

        "        self.slay_edge_stable_passes = 0\n"

        "        self.slay_modal_open = False\n"

        "        self.slay_modal_button_state = []\n"

        "        self.slay_header = None\n"

        "        self.slay_map_summary = None\n"

        "        self.slay_credit_label = None\n"

        "        self.slay_inventory_button = None\n"

        "        self.slay_shop_button = None\n"

        "        # v0.2.107 shop prewarm state. Keep the cache keyed by every\n"

        "        # input that can change stock, prices, ownership, or metadata.\n"

        "        self.slay_shop_cache_signature = None\n"

        "        self.slay_shop_cache = None\n"

        "        self.slay_shop_prewarm_event = None\n"

        "        self.slay_shop_popup = None\n"

        "        self.slay_shop_reopen_pending = False\n"

        "        self.slay_initial_map_scroll_done = False\n"

    )

    init_marker = "        # Slay the StarCraft v0.2 UI state.\n"

    if init_marker in text:

        if text.count(init_marker) != 1:

            raise RuntimeError("Found multiple Slay UI state blocks; refusing to guess")

        istart = text.index(init_marker)



        if "self.slay_initial_map_scroll_done = False" in text[istart:istart + 1500]:

            iend_line = "        self.slay_initial_map_scroll_done = False\n"

        elif "self.slay_shop_reopen_pending = False" in text[istart:istart + 1400]:

            iend_line = "        self.slay_shop_reopen_pending = False\n"

        elif "self.slay_shop_prewarm_event = None" in text[istart:istart + 1200]:

            iend_line = "        self.slay_shop_prewarm_event = None\n"

        elif "self.slay_shop_button = None" in text[istart:istart + 1200]:

            iend_line = "        self.slay_shop_button = None\n"

        elif "self.slay_modal_button_state = []" in text[istart:istart + 800]:

            iend_line = "        self.slay_modal_button_state = []\n"

        else:

            iend_line = "        self.slay_edge_group = None\n"

        iend = text.find(iend_line, istart)

        if iend < 0:

            raise RuntimeError("Could not find end of Slay UI state block")

        iend += len(iend_line)

        text = text[:istart] + init_add + text[iend:]

    else:

        text = insert_after_unique_line(text, "        self.minimized = False", init_add, "SC2Manager minimized")



    sig_line = "        slay_signature = slay.ui_signature(self.ctx)  # Slay the StarCraft v0.2\n"

    if "slay_signature = slay.ui_signature" not in text:

        text = insert_after_unique_line(text, "        sorted_items_received = sorted([item.item for item in self.ctx.items_received])", sig_line, "sorted_items_received")



    old_changed = '''        data_changed = (
            self.last_checked_locations != self.ctx.checked_locations
            or self.last_items_received != sorted_items_received
        )'''

    new_changed = '''        data_changed = (
            self.last_checked_locations != self.ctx.checked_locations
            or self.last_items_received != sorted_items_received
            or self.last_slay_signature != slay_signature
        )'''

    if "or self.last_slay_signature != slay_signature" not in text:

        if text.count(old_changed) != 1:

            raise RuntimeError("Could not uniquely patch SC2 GUI data_changed expression")

        text = text.replace(old_changed, new_changed, 1)



    if "self.last_slay_signature = slay_signature" not in text:

        text = insert_after_unique_line(text, "        self.last_items_received = sorted_items_received", "        self.last_slay_signature = slay_signature\n", "last_items_received")









    header_marker = "        # Slay the StarCraft v0.2 header.\n"

    header_end = "            multi_campaign_layout_height += 52\n"

    if header_marker in text:

        if text.count(header_marker) != 1:

            raise RuntimeError("Found multiple Slay header blocks; refusing to guess")

        hs = text.index(header_marker)

        he = text.find(header_end, hs)

        if he < 0:

            raise RuntimeError("Could not find end of existing Slay header block")

        he += len(header_end)

        text = text[:hs] + text[he:]







    text = text.replace(

        "        # Slay the StarCraft v0.2.88 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.100 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.101 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.104 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.105 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.102 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    text = text.replace(

        "        # Slay the StarCraft v0.2.103 fixed launcher header.\n",

        "        # Slay the StarCraft v0.2.106 fixed launcher header.\n",

        1,

    )

    fixed_header_marker = "        # Slay the StarCraft v0.2.106 fixed launcher header.\n"

    if fixed_header_marker not in text:









        launcher_pattern = re.compile(

            r'(?m)^(?P<i>        )panel = self\.add_client_tab\(["\']Starcraft 2 Launcher["\'], CampaignScroll\(\)\)\n'

            r'(?P=i)self\.campaign_scroll_panel = panel\.content\n'

            r'(?P=i)self\.campaign_panel = MultiCampaignLayout\(\)\n'

            r'(?P=i)panel\.content\.add_widget\(self\.campaign_panel\)\n'

        )

        launcher_replacement = '''        # Slay the StarCraft v0.2.106 fixed launcher header.
        campaign_root = BoxLayout(orientation="vertical")
        panel = self.add_client_tab("Starcraft 2 Launcher", campaign_root)
        self.slay_header = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=0,
            spacing=dp(8), padding=[dp(8), dp(4), dp(8), dp(4)], opacity=0,
        )
        self.slay_header.add_widget(Label(
            text="[b]SLAY THE STARCRAFT[/b]", markup=True,
            halign="left", size_hint_x=0.30,
        ))
        self.slay_credit_label = Label(text="", markup=True, size_hint_x=0.24)
        self.slay_header.add_widget(self.slay_credit_label)
        self.slay_inventory_button = Button(text="INVENTORY", size_hint_x=0.22, disabled=True)
        self.slay_inventory_button.bind(on_release=self.open_slay_inventory)
        self.slay_header.add_widget(self.slay_inventory_button)
        self.slay_shop_button = Button(text="SHOP", size_hint_x=0.24, disabled=True)
        self.slay_shop_button.bind(on_release=self.open_slay_shop)
        self.slay_header.add_widget(self.slay_shop_button)
        campaign_root.add_widget(self.slay_header)

        self.slay_mission_shell = BoxLayout(orientation="horizontal")
        self.slay_mission_shell.add_widget(Label(text="", size_hint_x=0.10))
        self.campaign_scroll_panel = CampaignScroll(size_hint_x=0.80)
        self.slay_mission_shell.add_widget(self.campaign_scroll_panel)
        self.slay_mission_shell.add_widget(Label(text="", size_hint_x=0.10))
        campaign_root.add_widget(self.slay_mission_shell)
        self.campaign_panel = MultiCampaignLayout()
        self.campaign_scroll_panel.add_widget(self.campaign_panel)
'''

        text, launcher_count = launcher_pattern.subn(launcher_replacement, text, count=1)

        if launcher_count == 0 and ('add_client_tab("Starcraft 2 Launcher"' in text or "add_client_tab('Starcraft 2 Launcher'" in text):

            raise RuntimeError("Found Starcraft 2 Launcher build path but could not install fixed Slay header")









    old_map_width = """        self.campaign_scroll_panel = CampaignScroll()
        campaign_root.add_widget(self.campaign_scroll_panel)
        self.campaign_panel = MultiCampaignLayout()
        self.campaign_scroll_panel.add_widget(self.campaign_panel)
"""

    new_map_width = """        self.slay_mission_shell = BoxLayout(orientation="horizontal")
        self.slay_mission_shell.add_widget(Label(text="", size_hint_x=0.10))
        self.campaign_scroll_panel = CampaignScroll(size_hint_x=0.80)
        self.slay_mission_shell.add_widget(self.campaign_scroll_panel)
        self.slay_mission_shell.add_widget(Label(text="", size_hint_x=0.10))
        campaign_root.add_widget(self.slay_mission_shell)
        self.campaign_panel = MultiCampaignLayout()
        self.campaign_scroll_panel.add_widget(self.campaign_panel)
"""

    if old_map_width in text:

        text = text.replace(old_map_width, new_map_width, 1)











    legacy_summary_re = re.compile(

        r'        # Slay the StarCraft v0\.3\.(?:45|46) route-map summary footer\.\n'

        r'.*?        campaign_root\.add_widget\(self\.slay_map_summary\)\n',

        flags=re.DOTALL,

    )

    text, _legacy_summary_count = legacy_summary_re.subn('', text, count=1)



    scrolled_summary_marker = '        # Slay the StarCraft v1.0.2.17 scrollable route-map summary.\n'

    if scrolled_summary_marker not in text:

        summary_anchor = '        self.campaign_panel.height = multi_campaign_layout_height\n'

        if text.count(summary_anchor) != 1:

            raise RuntimeError(

                f"Could not uniquely add scrollable Slay route-map summary (anchors={text.count(summary_anchor)})"

            )

        scrolled_summary_block = '''        # Slay the StarCraft v1.0.2.17 scrollable route-map summary.
        if slay.enabled(self.ctx):
            self.slay_map_summary = GridLayout(
                cols=3, size_hint_y=None, height=dp(190),
                spacing=dp(18), padding=[dp(10), dp(10), dp(10), dp(8)],
            )
            slay_map_summary_paragraphs = (
                "Once you choose a mission, you cannot change your path. Once you complete a mission, you cannot return to it. Mission credit rewards are adjusted based on number of mutations, number of blessings, and how difficult of a mission it is. Hover over each mission to see what rewards it has to plan your route.",
                "Don’t forget to click on the shop button to buy units and upgrades. You can also click on the inventory button to view what units and upgrades you already have.",
                "The missions with the light blue border are available to select. The missions with red borders are considered to be more difficult but yield higher credit rewards. The missions with check marks are the ones you have completed. The missions with “X” are missions that are no longer accessible from the path you are on.",
            )
            for paragraph in slay_map_summary_paragraphs:
                summary_box = BoxLayout(
                    orientation="vertical", padding=[dp(10), dp(8), dp(10), dp(8)],
                )
                with summary_box.canvas.before:
                    summary_box._slay_summary_bg_color = Color(0.055, 0.090, 0.145, 0.96)
                    summary_box._slay_summary_bg = Rectangle(pos=summary_box.pos, size=summary_box.size)
                    summary_box._slay_summary_border_color = Color(0.52, 0.55, 0.60, 1.0)
                    summary_box._slay_summary_border = Line(
                        rectangle=(summary_box.x, summary_box.y, summary_box.width, summary_box.height),
                        width=1.1,
                    )

                def _sync_summary_box(widget, _value, rect=summary_box._slay_summary_bg, line=summary_box._slay_summary_border) -> None:
                    rect.pos = widget.pos
                    rect.size = widget.size
                    line.rectangle = (widget.x, widget.y, widget.width, widget.height)

                summary_box.bind(pos=_sync_summary_box, size=_sync_summary_box)
                summary_label = Label(
                    text=paragraph, halign="left", valign="top", font_size="16sp",
                )
                summary_label.bind(
                    size=lambda label, size: setattr(
                        label, "text_size", (max(0, size[0] - dp(2)), max(0, size[1] - dp(2)))
                    )
                )
                summary_box.add_widget(summary_label)
                self.slay_map_summary.add_widget(summary_box)
            self.campaign_panel.add_widget(self.slay_map_summary)
            multi_campaign_layout_height += dp(190)
        else:
            self.slay_map_summary = None
'''

        text = text.replace(summary_anchor, scrolled_summary_block + summary_anchor, 1)







    if "self.slay_mission_tab = panel  # Slay portable launcher" not in text:

        text = insert_after_unique_line(

            text,

            '        panel = self.add_client_tab("Starcraft 2 Launcher", campaign_root)',

            '        self.slay_mission_tab = panel  # Slay portable launcher\n',

            "fixed Starcraft 2 Launcher tab",

        )

    if "slay_launcher.install_launcher_tab(self)  # Slay portable launcher" not in text:

        text = insert_after_unique_line(

            text,

            "        self.campaign_scroll_panel.add_widget(self.campaign_panel)",

            "        slay_launcher.install_launcher_tab(self)  # Slay portable launcher\n",

            "Slay mission canvas install",

        )



    route_overlay_call = """                        # Slay route-state overlays and difficulty warning.\n                        self._slay_add_route_state_overlay(mission_button, slay.node_status(self.ctx, mission_id))\n                        if slay.mission_is_difficulty_outlier(self.ctx, mission_id):\n                            self._slay_add_difficulty_outline(mission_button)\n"""

    if "# Slay route-state overlays and difficulty warning." not in text:

        legacy = """                        # Slay difficulty-outlier route-map outline.\n                        if slay.mission_is_difficulty_outlier(self.ctx, mission_id):\n                            self._slay_add_difficulty_outline(mission_button)\n"""

        if legacy in text:

            text = text.replace(legacy, route_overlay_call, 1)

        elif "                        mission_button.tooltip_text = tooltip\n" in text:

            text = text.replace(

                "                        mission_button.tooltip_text = tooltip\n",

                route_overlay_call + "                        mission_button.tooltip_text = tooltip\n",

                1,

            )





    refresh_call_marker = "        self._slay_refresh_header()  # Slay fixed header\n"

    if refresh_call_marker not in text:

        build_table_match = re.search(r"^(    def build_mission_table\(self, dt\)(?: -> None)?\:\n)", text, flags=re.MULTILINE)

        if build_table_match:

            insert_at = build_table_match.end()

            text = text[:insert_at] + refresh_call_marker + text[insert_at:]









    hover_guard_marker = "        # Slay modal hover guard.\n"

    if hover_guard_marker not in text:

        on_enter = "    def on_enter(self):\n"

        if on_enter in text:

            guard = (

                "        # Slay modal hover guard.\n"

                "        if getattr(getattr(self.ctx, 'ui', None), 'slay_modal_open', False):\n"

                "            self.remove_tooltip()\n"

                "            return\n"

            )

            text = text.replace(on_enter, on_enter + guard, 1)







    gap_line = "        SLAY_MISSION_GAP = 36 if slay.enabled(self.ctx) else 0\n"

    gap_pattern = r"^\s*SLAY_MISSION_GAP = \d+ if slay\.enabled\(self\.ctx\) else 0$"

    if re.search(gap_pattern, text, flags=re.MULTILINE):

        text = re.sub(gap_pattern, gap_line.rstrip("\n"), text, count=1, flags=re.MULTILINE)

    else:

        text = insert_after_unique_line(text, "        MISSION_BUTTON_PADDING = 6", gap_line, "mission button padding")

    original_height = "                campaign_layout_height = (longest_column + 2) * (MISSION_BUTTON_HEIGHT + MISSION_BUTTON_PADDING)"

    spaced_height = "                campaign_layout_height = (longest_column + 2) * (MISSION_BUTTON_HEIGHT + MISSION_BUTTON_PADDING) + max(0, longest_column - 1) * SLAY_MISSION_GAP"

    if spaced_height not in text:

        if text.count(original_height) != 1:

            raise RuntimeError("Could not uniquely patch Slay mission layer height")

        text = text.replace(original_height, spaced_height, 1)

    original_category = "                    category_panel = MissionCategory(padding=[3,MISSION_BUTTON_PADDING,3,MISSION_BUTTON_PADDING])"

    old_spaced_category = "                    category_panel = MissionCategory(padding=[3,MISSION_BUTTON_PADDING,3,MISSION_BUTTON_PADDING], spacing=[0, SLAY_MISSION_GAP])"

    spaced_category = "                    category_panel = MissionCategory(padding=[2,MISSION_BUTTON_PADDING,2,MISSION_BUTTON_PADDING], spacing=[0, SLAY_MISSION_GAP])"

    if old_spaced_category in text:

        text = text.replace(old_spaced_category, spaced_category, 1)

    elif spaced_category not in text:

        if text.count(original_category) != 1:

            raise RuntimeError("Could not uniquely patch Slay mission layer spacing")

        text = text.replace(original_category, spaced_category, 1)









    tooltip_add = '''        # Slay the StarCraft v0.2 adds deterministic mission effects and exact scouted rewards.
        slay_section = slay.mission_tooltip_section(ctx, mission_id, mission_remaining_locations)
        if slay_section:
            tooltip = slay_section
            text = slay.decorate_mission_text(ctx, mission_id, text)
'''

    tooltip_marker = "        # Slay the StarCraft v0.2 adds deterministic mission effects and exact scouted rewards.\n"

    tooltip_end = "            text = slay.decorate_mission_text(ctx, mission_id, text)\n"

    if tooltip_marker in text:

        if text.count(tooltip_marker) != 1:

            raise RuntimeError("Found multiple Slay tooltip blocks; refusing to guess")

        ts = text.index(tooltip_marker)

        te = text.find(tooltip_end, ts)

        if te < 0:

            raise RuntimeError("Could not find end of existing Slay tooltip block")

        te += len(tooltip_end)

        text = text[:ts] + tooltip_add + text[te:]

    else:

        text = insert_after_unique_line(text, '        tooltip = f"[b]{text}[/b]\\n" + tooltip', tooltip_add, "mission tooltip assembly")



    schedule = '''        if slay.enabled(self.ctx):
            # The Slay route is bottom-to-top. Once real mission buttons exist,
            # force the first map view to the opening layer and then leave the
            # player's scroll position alone for the rest of the session.
            if self.mission_buttons and not getattr(self, "slay_initial_map_scroll_done", False):
                self.campaign_scroll_panel.scroll_y = 0.0
                Clock.schedule_once(lambda _dt: setattr(self.campaign_scroll_panel, "scroll_y", 0.0), 0)
                Clock.schedule_once(lambda _dt: setattr(self.campaign_scroll_panel, "scroll_y", 0.0), 0.20)
                self.slay_initial_map_scroll_done = True
            # Kivy can perform a late layout pass after the original bounded
            # startup samples. Bind route redraws directly to mission-button
            # geometry so connectors follow that final layout without waiting
            # for an unrelated Shop purchase to trigger another refresh.
            if not hasattr(self, "slay_edge_geometry_trigger"):
                self.slay_edge_geometry_trigger = Clock.create_trigger(self.draw_slay_edges, 0.08)
            for button in self.mission_buttons:
                try:
                    if not getattr(button, "slay_edge_geometry_bound", False):
                        button.bind(pos=lambda *_args: self.slay_edge_geometry_trigger())
                        button.bind(size=lambda *_args: self.slay_edge_geometry_trigger())
                        button.slay_edge_geometry_bound = True
                except Exception:
                    pass
            Clock.schedule_once(self.draw_slay_edges, 0.10)
            Clock.schedule_once(self.draw_slay_edges, 0.35)
            Clock.schedule_once(self.draw_slay_edges, 0.75)
            Clock.schedule_once(self.draw_slay_edges, 1.50)
            Clock.schedule_once(self.draw_slay_edges, 3.00)
            Clock.schedule_once(self.draw_slay_edges, 5.00)
            Clock.schedule_once(self.draw_slay_edges, 8.00)
'''

    old_schedule_start = "        if slay.enabled(self.ctx):\n            # Mission layouts can move for several frames while Kivy sizes the\n"

    old_schedule_end = "            Clock.schedule_once(self.draw_slay_edges, 3.00)\n"

    if old_schedule_start in text and "slay_edge_geometry_trigger" not in text:

        ss = text.index(old_schedule_start)

        se = text.find(old_schedule_end, ss)

        if se < 0:

            raise RuntimeError("Could not find end of existing Slay edge startup schedule")

        se += len(old_schedule_end)

        text = text[:ss] + schedule + text[se:]

    elif "Clock.schedule_once(self.draw_slay_edges" not in text:

        text = insert_after_unique_line(text, "        self.campaign_panel.height = multi_campaign_layout_height", schedule, "campaign panel height")



    methods = '''    # ----- Slay the StarCraft v0.2 UI -----
    def _slay_update_route_state_overlay(self, button, *_args) -> None:
        status = getattr(button, "slay_route_status", "")
        blue = getattr(button, "slay_available_outline", None)
        if blue is not None:
            inset = dp(5.0)
            blue.rectangle = (
                button.x + inset, button.y + inset,
                max(0, button.width - 2 * inset), max(0, button.height - 2 * inset),
            )
        x1 = getattr(button, "slay_abandoned_x1", None)
        x2 = getattr(button, "slay_abandoned_x2", None)
        check = getattr(button, "slay_completed_check", None)
        # Completed/abandoned markers sit on the left side of the mission box,
        # vertically centered and inset enough that the full stroke remains inside
        # both the outer danger border and the mission button itself.
        inset = dp(11.0)
        icon = min(dp(14.0), max(dp(10.0), button.height * 0.24))
        left = button.x + inset
        right = left + icon
        bottom = button.center_y - (icon * 0.5)
        top = button.center_y + (icon * 0.5)
        if x1 is not None:
            x1.points = [left, bottom, right, top]
        if x2 is not None:
            x2.points = [left, top, right, bottom]
        if check is not None:
            check.points = [
                left, bottom + icon * 0.48,
                left + icon * 0.35, bottom + icon * 0.18,
                right, top - icon * 0.12,
            ]

    def _slay_add_route_state_overlay(self, button, status: str) -> None:
        button.slay_route_status = str(status)
        if status in {"available", "selected"} and getattr(button, "slay_available_outline", None) is None:
            with button.canvas.after:
                # Inset farther than the red danger outline so both remain visible.
                button.slay_available_outline_color = Color(0.35, 0.76, 1.0, 0.95)
                button.slay_available_outline = Line(rectangle=(0, 0, 0, 0), width=1.8)
        elif status == "abandoned" and getattr(button, "slay_abandoned_x1", None) is None:
            with button.canvas.after:
                button.slay_abandoned_x_color = Color(0.95, 0.12, 0.12, 0.90)
                button.slay_abandoned_x1 = Line(points=[0, 0, 0, 0], width=2.0)
                button.slay_abandoned_x2 = Line(points=[0, 0, 0, 0], width=2.0)
        elif status == "completed" and getattr(button, "slay_completed_check", None) is None:
            with button.canvas.after:
                button.slay_completed_check_color = Color(0.20, 0.92, 0.34, 0.95)
                button.slay_completed_check = Line(points=[0, 0, 0, 0, 0, 0], width=2.2)
        self._slay_update_route_state_overlay(button)
        if not getattr(button, "slay_route_overlay_bound", False):
            button.bind(pos=self._slay_update_route_state_overlay, size=self._slay_update_route_state_overlay)
            button.slay_route_overlay_bound = True

    def _slay_update_difficulty_outline(self, button, *_args) -> None:
        line = getattr(button, "slay_difficulty_outline", None)
        if line is None:
            return
        inset = dp(1.5)
        line.rectangle = (
            button.x + inset, button.y + inset,
            max(0, button.width - 2 * inset), max(0, button.height - 2 * inset),
        )

    def _slay_add_difficulty_outline(self, button) -> None:
        if getattr(button, "slay_difficulty_outline", None) is not None:
            return
        with button.canvas.after:
            # A bright-but-not-neon red remains legible against all race button
            # colors and does not replace AP's normal background/status colors.
            button.slay_difficulty_outline_color = Color(0.93, 0.12, 0.12, 1.0)
            button.slay_difficulty_outline = Line(rectangle=(0, 0, 0, 0), width=2.2)
        self._slay_update_difficulty_outline(button)
        button.bind(pos=self._slay_update_difficulty_outline, size=self._slay_update_difficulty_outline)

    def _slay_refresh_header(self) -> None:
        header = getattr(self, "slay_header", None)
        if header is None:
            return
        active = slay.enabled(self.ctx)
        header.height = dp(48) if active else 0
        header.opacity = 1 if active else 0
        credit_label = getattr(self, "slay_credit_label", None)
        inventory_button = getattr(self, "slay_inventory_button", None)
        shop_button = getattr(self, "slay_shop_button", None)
        if inventory_button is not None:
            inventory_button.disabled = not active
        if shop_button is not None:
            shop_button.disabled = not active
        if not active:
            if credit_label is not None:
                credit_label.text = ""
            if shop_button is not None:
                shop_button.text = "SHOP"
            return
        if slay.state_ready(self.ctx):
            if credit_label is not None:
                credit_label.text = f"[b]Credits: {slay.credits(self.ctx)}[/b]"
            if shop_button is not None:
                shop_button.text = "SHOP"
            self._slay_schedule_shop_prewarm()
        else:
            if credit_label is not None:
                credit_label.text = "[b]Credits: loading...[/b]"
            if shop_button is not None:
                shop_button.text = "SHOP"

    def _slay_shop_cache_signature(self):
        """Hashable snapshot of every input used to paint the shop.

        State persistence can replace ctx.slay_state, so this deliberately reads
        the current state object each time rather than retaining a dictionary.
        """
        if not slay.enabled(self.ctx) or not slay.state_ready(self.ctx):
            return None
        state = slay.state(self.ctx)
        received = tuple(sorted(
            (int(getattr(item, "item", 0)), int(getattr(item, "location", 0)), int(getattr(item, "player", 0)))
            for item in getattr(self.ctx, "items_received", ())
        ))
        return (
            slay.victory_count(self.ctx),
            int(state.get("shop_cycle", -1)),
            int(state.get("shop_reroll_nonce", 0)),
            int(state.get("shop_expansion", 0)),
            int(state.get("shop_rerolls_this_cycle", 0)),
            int(state.get("spent", 0)),
            slay.credits(self.ctx),
            tuple(state.get("shop_stock", ())),
            tuple(state.get("shop_sale_items", ())),
            tuple(sorted(state.get("shop_cycle_purchases", {}).items())),
            tuple(sorted(state.get("purchases", {}).items())),
            tuple(state.get("permanent_blessings", ())),
            tuple(state.get("permanent_boons", ())),
            tuple(sorted(state.get("duplicate_replacements", {}).items())),
            received,
        )

    def _slay_prewarm_shop(self, *_args) -> None:
        self.slay_shop_prewarm_event = None
        if not slay.enabled(self.ctx) or not slay.state_ready(self.ctx):
            self.slay_shop_cache_signature = None
            self.slay_shop_cache = None
            return
        # SALE identities are persisted here, before price/render-state lookup.
        # This also avoids the old detached-state bug where UI and wallet could
        # disagree after a state-persisting helper replaced ctx.slay_state.
        sale_items = set(slay.shop_sale_items(self.ctx, preserve=True))
        sections = slay.shop_sections(self.ctx)
        names = [item for _category, entries in sections for item in entries]
        render_states = slay.shop_render_states(self.ctx, names)
        entry_data = {}
        for item_name in names:
            description = slay.shop_entry_description(item_name)
            display_name = slay.shop_entry_display_name(item_name)
            icon_url = slay.shop_entry_icon(item_name)
            entry_data[item_name] = (description, display_name, icon_url)
            if icon_url:
                try:
                    # Start Kivy's remote image fetch while the player is still
                    # looking at the route map; AsyncImage then hits Loader cache.
                    Loader.image(icon_url)
                except Exception:
                    pass

        # Precompute the *next* deterministic Reroll Shop stock as well. A reroll
        # can then promote this data immediately instead of doing category rolls,
        # descriptions, and remote icon fetches in the button-click handler.
        next_reroll_stock = slay.preview_next_shop_reroll(self.ctx)
        next_reroll_sections = slay.shop_sections(self.ctx, next_reroll_stock) if next_reroll_stock else []
        next_names = [item for _category, entries in next_reroll_sections for item in entries]
        next_reroll_nonce = int(slay.state(self.ctx).get("shop_reroll_nonce", 0)) + 1
        next_reroll_sale_items = set(
            slay.preview_shop_sales(self.ctx, next_reroll_stock, reroll_nonce=next_reroll_nonce)
        ) if next_reroll_stock else set()
        next_reroll_render_states = slay.shop_render_states(
            self.ctx, next_names, sale_items_override=next_reroll_sale_items
        ) if next_names else {}
        next_entry_data = {}
        for item_name in next_names:
            if item_name in entry_data:
                next_entry_data[item_name] = entry_data[item_name]
                continue
            description = slay.shop_entry_description(item_name)
            display_name = slay.shop_entry_display_name(item_name)
            icon_url = slay.shop_entry_icon(item_name)
            next_entry_data[item_name] = (description, display_name, icon_url)
            if icon_url:
                try:
                    Loader.image(icon_url)
                except Exception:
                    pass

        inventory_rows = slay.inventory_rows(self.ctx)
        for inventory_item in inventory_rows:
            inventory_icon = str(inventory_item.get("icon", "") or "")
            if inventory_icon:
                try:
                    Loader.image(inventory_icon)
                except Exception:
                    pass

        signature = self._slay_shop_cache_signature()
        self.slay_shop_cache_signature = signature
        self.slay_shop_cache = {
            "signature": signature,
            "sale_items": sale_items,
            "sections": sections,
            "render_states": render_states,
            "entry_data": entry_data,
            "next_reroll_stock": list(next_reroll_stock),
            "next_reroll_sections": next_reroll_sections,
            "next_reroll_sale_items": next_reroll_sale_items,
            "next_reroll_render_states": next_reroll_render_states,
            "next_reroll_entry_data": next_entry_data,
            "inventory_rows": inventory_rows,
        }

    def _slay_schedule_shop_prewarm(self, delay=0.08) -> None:
        if not slay.enabled(self.ctx) or not slay.state_ready(self.ctx):
            return
        signature = self._slay_shop_cache_signature()
        cache = getattr(self, "slay_shop_cache", None)
        if cache is not None and self.slay_shop_cache_signature == signature:
            return
        old_event = getattr(self, "slay_shop_prewarm_event", None)
        if old_event is not None:
            try:
                old_event.cancel()
            except Exception:
                pass
        self.slay_shop_prewarm_event = Clock.schedule_once(self._slay_prewarm_shop, delay)

    def _slay_invalidate_shop_cache(self, delay=0.12) -> None:
        self.slay_shop_cache_signature = None
        self.slay_shop_cache = None
        # Do not make the purchase click compete with a full cache rebuild in the
        # same frame. Rewarm shortly after the UI has reacted to the purchase.
        self._slay_schedule_shop_prewarm(delay)

    def _slay_begin_modal(self) -> None:
        if self.slay_modal_open:
            return
        self.slay_modal_open = True
        self.clear_tooltip()
        old_event = getattr(self, "slay_modal_tooltip_event", None)
        if old_event is not None:
            try:
                old_event.cancel()
            except Exception:
                pass
        # HoverBehavior is driven by the global mouse even underneath Popups.
        # Keep clearing any late/scheduled mission tooltip while a Slay modal is
        # open so the map cannot paint hover text through the Shop/Inventory.
        self.slay_modal_tooltip_event = Clock.schedule_interval(
            lambda _dt: self.clear_tooltip(), 0.05
        )
        self.slay_modal_button_state = []
        self.slay_edge_retry_count = 0
        for button in self.mission_buttons:
            try:
                self.slay_modal_button_state.append((button, button.disabled, button.tooltip_text))
                button.tooltip_text = ""
                button.disabled = True
            except Exception:
                pass

    def _slay_end_modal(self, *_args) -> None:
        event = getattr(self, "slay_modal_tooltip_event", None)
        if event is not None:
            try:
                event.cancel()
            except Exception:
                pass
        self.slay_modal_tooltip_event = None
        saved = list(self.slay_modal_button_state)
        self.slay_modal_button_state = []
        self.slay_modal_open = False
        for button, was_disabled, tooltip_text in saved:
            try:
                button.disabled = was_disabled
                button.tooltip_text = tooltip_text
            except Exception:
                pass
        self.clear_tooltip()

    def _slay_shop_dismissed(self, popup: Popup, *_args) -> None:
        # Only one shop Popup may exist at a time. The old buy path dismissed and
        # scheduled a fresh Popup on every click, so rapid purchases/rerolls could
        # queue several windows and make Close appear to require repeated clicks.
        if getattr(self, "slay_shop_popup", None) is popup:
            self.slay_shop_popup = None
        reopen = bool(getattr(self, "slay_shop_reopen_pending", False))
        self.slay_shop_reopen_pending = False
        self._slay_end_modal()
        if reopen:
            Clock.schedule_once(lambda _dt: self.open_slay_shop(preserve_sale=True), 0)

    def _slay_refresh_shop_controls(self, popup: Popup) -> None:
        buttons = getattr(popup, "slay_purchase_buttons", {})
        names = list(buttons.keys())
        if not names:
            return
        render_states = slay.shop_render_states(self.ctx, names)
        balance = slay.credits(self.ctx)
        credit_label = getattr(popup, "slay_credit_label", None)
        if credit_label is not None:
            credit_label.text = f"[b]Credits: {balance}[/b]    Shop stock refreshes after every victory."
        for item_name, button in buttons.items():
            bought, can_buy, price = render_states[item_name]
            if bought and not can_buy:
                button.text = "PURCHASED"
                button.disabled = True
            else:
                button.text = f"Buy Again - {price} cr" if bought else f"Buy - {price} cr"
                button.disabled = (not can_buy) or balance < price

    def _slay_promote_reroll_cache(self, old_cache, new_stock) -> bool:
        if not old_cache:
            return False
        cached_stock = list(old_cache.get("next_reroll_stock", ()))
        if list(new_stock) != cached_stock:
            return False
        sections = old_cache.get("next_reroll_sections", ())
        entry_data = old_cache.get("next_reroll_entry_data", {})
        names = [item for _category, entries in sections for item in entries]
        # Stock/icons are safe to promote, but prices are stateful. The reroll
        # purchase has just incremented shop_rerolls_this_cycle; prewarmed render
        # states were priced before that increment and would therefore lag one
        # step (100 -> 150 -> still 150 until another rebuild). Recompute only
        # the cheap render states against the newly persisted purchase count.
        sale_items = set(slay.shop_sale_items(self.ctx, preserve=True))
        render_states = slay.shop_render_states(self.ctx, names)
        signature = self._slay_shop_cache_signature()
        self.slay_shop_cache_signature = signature
        self.slay_shop_cache = {
            "signature": signature,
            "sale_items": sale_items,
            "sections": sections,
            "render_states": render_states,
            "entry_data": entry_data,
            # The next-next roll can be prepared after this frame; the current
            # reroll opens immediately from the already-warm promoted cache.
            "next_reroll_stock": [],
            "next_reroll_sections": [],
            "next_reroll_sale_items": set(),
            "next_reroll_render_states": {},
            "next_reroll_entry_data": {},
        }
        self._slay_schedule_shop_prewarm(0.15)
        return True

    def _slay_show_purchase_reveal(self, reveal) -> None:
        if not isinstance(reveal, dict):
            return
        rows = list(reveal.get("rows", ()))
        if not rows:
            return
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        scroll = ScrollView()
        content = GridLayout(cols=1, size_hint_y=None, spacing=dp(7), padding=[dp(4), dp(4), dp(4), dp(4)])
        content.bind(minimum_height=content.setter("height"))
        for entry in rows:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(78), spacing=dp(8), padding=[dp(4), dp(4), dp(4), dp(4)])
            icon_url = str(entry.get("icon", "") or "")
            if icon_url:
                row.add_widget(AsyncImage(source=icon_url, size_hint_x=None, width=dp(64), allow_stretch=True, keep_ratio=True))
            label_text = f"[b]{entry.get('name', '')}[/b]"
            description = str(entry.get("description", "") or "").strip()
            if description:
                label_text += f"\\n[color=AAAAAA]{description}[/color]"
            label = Label(text=label_text, markup=True, halign="left", valign="middle")
            label.bind(size=lambda widget, size: setattr(widget, "text_size", (size[0], None)))
            label.bind(texture_size=lambda widget, size, target=row: setattr(target, "height", max(dp(78), size[1] + dp(18))))
            row.add_widget(label)
            content.add_widget(row)
        scroll.add_widget(content)
        root.add_widget(scroll)
        close = Button(text="Close", size_hint_y=None, height=dp(44))
        reward_popup = Popup(
            title=str(reveal.get("title", "Shop Reward")),
            content=root,
            size_hint=(0.72, min(0.82, 0.34 + 0.13 * len(rows))),
        )
        close.bind(on_release=reward_popup.dismiss)
        root.add_widget(close)
        reward_popup.open()

    def _slay_buy(self, item_name: str, popup: Popup) -> None:
        try:
            self.slay_shop_scroll_y = popup.slay_scroll.scroll_y
        except Exception:
            pass
        structural_purchase = slay.shop_purchase_changes_stock(item_name)
        old_stock = tuple(slay.shop_stock(self.ctx)) if structural_purchase else ()
        old_cache = getattr(self, "slay_shop_cache", None)
        preview = None
        if (
            slay.is_reroll_shop_item(item_name)
            and old_cache is not None
            and self.slay_shop_cache_signature == self._slay_shop_cache_signature()
        ):
            preview = old_cache.get("next_reroll_stock") or None
        success, message = slay.purchase(
            self.ctx, item_name, precomputed_reroll_stock=preview
        )
        logging.getLogger("Starcraft2").info(message)
        if not success:
            return
        reveal = slay.consume_shop_purchase_reveal(self.ctx)
        self.refresh_from_launching = False
        new_stock = tuple(slay.shop_stock(self.ctx)) if structural_purchase else old_stock

        promoted = False
        if preview is not None and slay.is_reroll_shop_item(item_name):
            promoted = self._slay_promote_reroll_cache(old_cache, new_stock)
        if not promoted:
            self._slay_invalidate_shop_cache()

        if not structural_purchase or new_stock == old_stock:
            # Ordinary purchases never tear down/rebuild the whole shop anymore.
            # Updating just the credit label and buy buttons avoids the old lag
            # and eliminates the disorienting scroll-to-top / restore flash.
            self._slay_refresh_shop_controls(popup)
            if reveal:
                Clock.schedule_once(lambda _dt, data=reveal: self._slay_show_purchase_reveal(data), 0)
            return

        # Rerolls, contracts/unlocks, and Shop Expansion genuinely change which
        # rows exist. Rebuild exactly once, after the current Popup has dismissed.
        self.slay_shop_reopen_pending = True
        popup.dismiss()
        if reveal:
            Clock.schedule_once(lambda _dt, data=reveal: self._slay_show_purchase_reveal(data), 0)

    def open_slay_shop(self, *_args, preserve_sale=False) -> None:
        if not slay.enabled(self.ctx):
            logging.getLogger("Starcraft2").info("No Slay the StarCraft run is active.")
            return
        if getattr(self, "slay_shop_popup", None) is not None:
            return
        self._slay_begin_modal()
        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        if not slay.state_ready(self.ctx):
            root.add_widget(Label(text="Run state is loading. Try again in a moment."))
            popup = Popup(title="Slay the StarCraft Shop", content=root, size_hint=(0.80, 0.50))
            self.slay_shop_popup = popup
            popup.bind(on_dismiss=lambda pop: self._slay_shop_dismissed(pop))
            popup.open()
            return

        # Resolve/persist the current SALE set before trusting any cache. This is
        # cheap and prevents first-open frames where an old prewarm had stock but
        # not the newly persisted sale identities/prices; reopening used to fix it.
        live_sale_items = set(slay.shop_sale_items(self.ctx, preserve=True))
        # Normally everything below is already computed while the route map was
        # open. Fall back synchronously if state or SALE identity changed.
        signature = self._slay_shop_cache_signature()
        cache = getattr(self, "slay_shop_cache", None)
        if (
            cache is None
            or self.slay_shop_cache_signature != signature
            or set(cache.get("sale_items", ())) != live_sale_items
        ):
            self._slay_prewarm_shop()
            cache = getattr(self, "slay_shop_cache", None)
        if cache is None:
            sale_items = set(slay.shop_sale_items(self.ctx, preserve=True))
            sections = slay.shop_sections(self.ctx)
            names = [item for _category, entries in sections for item in entries]
            render_states = slay.shop_render_states(self.ctx, names)
            entry_data = {
                item: (slay.shop_entry_description(item), slay.shop_entry_display_name(item), slay.shop_entry_icon(item))
                for item in names
            }
        else:
            sale_items = set(cache["sale_items"])
            sections = cache["sections"]
            render_states = cache["render_states"]
            entry_data = cache["entry_data"]

        credit_label = Label(
            text=f"[b]Credits: {slay.credits(self.ctx)}[/b]    Shop stock refreshes after every victory.",
            markup=True, size_hint_y=None, height=dp(38),
        )
        root.add_widget(credit_label)
        scroll = ScrollView()

        # Four persistent columns keep each category together instead of allowing
        # a category to spill horizontally across columns. The three race columns
        # stay on the left; cross-race progression lives in the right column.
        shop_grid = GridLayout(cols=4, size_hint_y=None, spacing=dp(10), padding=[0, dp(4), 0, dp(4)])
        columns = []
        for _index in range(4):
            column = GridLayout(cols=1, size_hint_y=1, spacing=dp(10))
            columns.append(column)
            shop_grid.add_widget(column)

        def _sync_shop_grid_height(*_args) -> None:
            shop_grid.height = max((column.minimum_height for column in columns), default=0)

        for column in columns:
            column.bind(minimum_height=_sync_shop_grid_height)

        section_columns = {
            "Terran Units": 0,
            "Terran Upgrades": 0,
            "Defensive Structures & Detectors": 0,
            "Zerg Units": 1,
            "Zerg Upgrades": 1,
            "General Upgrades": 1,
            "Protoss Units": 2,
            "Protoss Upgrades": 2,
            "Mercenary Contracts": 3,
            "Mercenaries": 3,
            "Kerrigan": 3,
            "Spear of Adun": 3,
            "Boons": 2,
        }
        section_palette = {
            "Terran Units": (0.155, 0.178, 0.198, 1.0),
            "Terran Upgrades": (0.170, 0.191, 0.211, 1.0),
            "Defensive Structures & Detectors": (0.155, 0.190, 0.188, 1.0),
            "Zerg Units": (0.184, 0.158, 0.194, 1.0),
            "Zerg Upgrades": (0.198, 0.170, 0.206, 1.0),
            "General Upgrades": (0.184, 0.184, 0.184, 1.0),
            "Protoss Units": (0.199, 0.190, 0.158, 1.0),
            "Protoss Upgrades": (0.211, 0.201, 0.170, 1.0),
            "Mercenary Contracts": (0.145, 0.175, 0.215, 1.0),
            "Mercenaries": (0.160, 0.190, 0.168, 1.0),
            "Kerrigan": (0.198, 0.164, 0.181, 1.0),
            "Spear of Adun": (0.225, 0.195, 0.120, 1.0),
            "Boons": (0.215, 0.145, 0.150, 1.0),
        }

        popup = Popup(title="Slay the StarCraft Shop", size_hint=(0.98, 0.94))
        self.slay_shop_popup = popup
        popup.slay_purchase_buttons = {}
        popup.slay_credit_label = credit_label
        popup.bind(on_dismiss=lambda pop: self._slay_shop_dismissed(pop))
        if not sections:
            columns[0].add_widget(Label(text="No eligible shop items.", size_hint_y=None, height=dp(48)))

        for category, entries in sections:
            section = GridLayout(
                cols=1, size_hint_y=None, spacing=dp(4),
                padding=[dp(6), dp(5), dp(6), dp(7)],
            )
            section.bind(minimum_height=section.setter("height"))
            shade = section_palette.get(category, (0.18, 0.18, 0.18, 1.0))
            with section.canvas.before:
                section._slay_bg_color = Color(*shade)
                section._slay_bg_rect = Rectangle(pos=section.pos, size=section.size)

            def _sync_section_bg(widget, _value, rect=section._slay_bg_rect) -> None:
                rect.pos = widget.pos
                rect.size = widget.size

            section.bind(pos=_sync_section_bg, size=_sync_section_bg)
            section.add_widget(Label(
                text=f"[b]{category}[/b]", markup=True,
                size_hint_y=None, height=dp(30), halign="left", valign="middle",
            ))

            for item_name in entries:
                description, display_name, icon_url = entry_data[item_name]
                row = BoxLayout(
                    orientation="horizontal", size_hint_y=None, height=dp(62),
                    spacing=dp(6), padding=[dp(2), dp(3), dp(2), dp(3)],
                )
                on_sale = item_name in sale_items
                if on_sale:
                    with row.canvas.before:
                        row._slay_sale_color = Color(0.11, 0.27, 0.15, 0.90)
                        row._slay_sale_rect = Rectangle(pos=row.pos, size=row.size)
                    def _sync_sale_bg(widget, _value, rect=row._slay_sale_rect) -> None:
                        rect.pos = widget.pos
                        rect.size = widget.size
                    row.bind(pos=_sync_sale_bg, size=_sync_sale_bg)

                bought, can_buy, price = render_states[item_name]
                if bought and not can_buy:
                    buy_text = "PURCHASED"
                    buy_disabled = True
                else:
                    buy_text = f"Buy Again - {price} cr" if bought else f"Buy - {price} cr"
                    buy_disabled = (not can_buy) or slay.credits(self.ctx) < price
                purchase_widget = Button(
                    text=buy_text, size_hint_x=None, width=dp(96), disabled=buy_disabled,
                )
                if not buy_disabled:
                    purchase_widget.bind(
                        on_release=lambda _button, name=item_name, pop=popup: self._slay_buy(name, pop)
                    )
                popup.slay_purchase_buttons[item_name] = purchase_widget
                row.add_widget(purchase_widget)

                if icon_url:
                    row.add_widget(AsyncImage(
                        source=icon_url, size_hint_x=None, width=dp(52),
                        allow_stretch=True, keep_ratio=True,
                    ))

                label_text = display_name
                if on_sale:
                    label_text += "  [color=7CFF9B][b]SALE![/b][/color]"
                if description:
                    label_text += f"\\n[color=AAAAAA]{description}[/color]"
                item_label = Label(text=label_text, markup=True, halign="left", valign="middle")
                item_label.bind(size=lambda label, size: setattr(label, "text_size", (size[0], None)))
                item_label.bind(
                    texture_size=lambda label, size, target=row: setattr(target, "height", max(dp(62), size[1] + dp(14)))
                )
                row.add_widget(item_label)
                section.add_widget(row)

            columns[section_columns.get(category, 2)].add_widget(section)

        _sync_shop_grid_height()
        scroll.add_widget(shop_grid)
        root.add_widget(scroll)
        close = Button(text="Close", size_hint_y=None, height=dp(44))
        close.bind(on_release=popup.dismiss)
        root.add_widget(close)
        popup.content = root
        popup.slay_scroll = scroll
        saved_scroll_y = getattr(self, "slay_shop_scroll_y", 1.0)
        # Set before opening so the first painted frame is already at the saved
        # location; retain the scheduled assignment for Kivy's late layout pass.
        scroll.scroll_y = saved_scroll_y
        popup.open()
        Clock.schedule_once(lambda _dt, view=scroll, y=saved_scroll_y: setattr(view, "scroll_y", y), 0)

    def open_slay_inventory(self, *_args) -> None:
        if not slay.enabled(self.ctx):
            logging.getLogger("Starcraft2").info("No Slay the StarCraft run is active.")
            return
        self._slay_begin_modal()
        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        scroll = ScrollView()

        inventory_grid = GridLayout(cols=4, size_hint_y=None, spacing=dp(10), padding=[0, dp(4), 0, dp(4)])
        columns = []
        for _index in range(4):
            column = GridLayout(cols=1, size_hint_y=1, spacing=dp(10))
            columns.append(column)
            inventory_grid.add_widget(column)

        def _sync_inventory_grid_height(*_args) -> None:
            inventory_grid.height = max((column.minimum_height for column in columns), default=0)

        for column in columns:
            column.bind(minimum_height=_sync_inventory_grid_height)

        # Mirror the shop's stable category layout. Boons intentionally live
        # under Protoss in column three; global progression occupies column four.
        section_columns = {
            "Terran Units": 0,
            "Terran Upgrades": 0,
            "Defensive Structures & Detectors": 0,
            "Zerg Units": 1,
            "Zerg Upgrades": 1,
            "General Upgrades": 1,
            "Protoss Units": 2,
            "Protoss Upgrades": 2,
            "Boons": 2,
            "Blessings": 2,
            "Mutations": 2,
            "Mercenary Contracts": 3,
            "Mercenaries": 3,
            "Kerrigan": 3,
            "Spear of Adun": 3,
        }
        section_palette = {
            "Terran Units": (0.155, 0.178, 0.198, 1.0),
            "Terran Upgrades": (0.170, 0.191, 0.211, 1.0),
            "Defensive Structures & Detectors": (0.155, 0.190, 0.188, 1.0),
            "Zerg Units": (0.184, 0.158, 0.194, 1.0),
            "Zerg Upgrades": (0.198, 0.170, 0.206, 1.0),
            "General Upgrades": (0.184, 0.184, 0.184, 1.0),
            "Protoss Units": (0.199, 0.190, 0.158, 1.0),
            "Protoss Upgrades": (0.211, 0.201, 0.170, 1.0),
            "Boons": (0.215, 0.145, 0.150, 1.0),
            "Blessings": (0.180, 0.155, 0.205, 1.0),
            "Mutations": (0.205, 0.150, 0.160, 1.0),
            "Mercenary Contracts": (0.145, 0.175, 0.215, 1.0),
            "Mercenaries": (0.160, 0.190, 0.168, 1.0),
            "Kerrigan": (0.198, 0.164, 0.181, 1.0),
            "Spear of Adun": (0.225, 0.195, 0.120, 1.0),
        }
        section_order = tuple(section_columns)

        rows = []
        if slay.state_ready(self.ctx):
            signature = self._slay_shop_cache_signature()
            cache = getattr(self, "slay_shop_cache", None)
            if cache is not None and cache.get("signature") == signature:
                rows = list(cache.get("inventory_rows", ()))
            else:
                rows = slay.inventory_rows(self.ctx)
        if not slay.state_ready(self.ctx):
            columns[0].add_widget(Label(text="Run state is loading. Try again in a moment.", size_hint_y=None, height=dp(48)))
        elif not rows:
            columns[0].add_widget(Label(text="No items received or purchased yet.", size_hint_y=None, height=dp(48)))
        else:
            by_section = {name: [] for name in section_order}
            for item in rows:
                section_name = item.get("section", "General Upgrades")
                by_section.setdefault(section_name, []).append(item)

            for section_name in section_order:
                entries = by_section.get(section_name, [])
                if not entries:
                    continue
                section = GridLayout(
                    cols=1, size_hint_y=None, spacing=dp(4),
                    padding=[dp(6), dp(5), dp(6), dp(7)],
                )
                section.bind(minimum_height=section.setter("height"))
                shade = section_palette.get(section_name, (0.18, 0.18, 0.18, 1.0))
                with section.canvas.before:
                    section._slay_bg_color = Color(*shade)
                    section._slay_bg_rect = Rectangle(pos=section.pos, size=section.size)

                def _sync_inventory_section_bg(widget, _value, rect=section._slay_bg_rect) -> None:
                    rect.pos = widget.pos
                    rect.size = widget.size

                section.bind(pos=_sync_inventory_section_bg, size=_sync_inventory_section_bg)
                section.add_widget(Label(
                    text=f"[b]{section_name}[/b]", markup=True,
                    size_hint_y=None, height=dp(30), halign="left", valign="middle",
                ))

                for item in entries:
                    sources = []
                    if item["ap_count"]:
                        sources.append(f"AP {item['ap_count']}")
                    if item["shop_count"]:
                        sources.append(f"Shop {item['shop_count']}")
                    source_text = ", ".join(sources) or "Owned"
                    count_text = f"x{item['total']}"

                    row = BoxLayout(
                        orientation="horizontal", size_hint_y=None, height=dp(62),
                        spacing=dp(6), padding=[dp(2), dp(3), dp(2), dp(3)],
                    )
                    badge = Label(
                        text=f"[b]{count_text}[/b]\\n[color=AAAAAA]{source_text}[/color]", markup=True,
                        size_hint_x=None, width=dp(104), halign="center", valign="middle",
                    )
                    badge.bind(size=lambda label, size: setattr(label, "text_size", size))
                    row.add_widget(badge)

                    icon_url = str(item.get("icon", "") or "")
                    if icon_url:
                        row.add_widget(AsyncImage(
                            source=icon_url, size_hint_x=None, width=dp(52),
                            allow_stretch=True, keep_ratio=True,
                        ))

                    label_text = str(item["name"])
                    description = str(item.get("description", "") or "").strip()
                    if description:
                        label_text += f"\\n[color=AAAAAA]{description}[/color]"
                    item_label = Label(text=label_text, markup=True, halign="left", valign="middle")
                    item_label.bind(size=lambda label, size: setattr(label, "text_size", (size[0], None)))
                    item_label.bind(
                        texture_size=lambda label, size, target=row: setattr(target, "height", max(dp(62), size[1] + dp(14)))
                    )
                    row.add_widget(item_label)
                    section.add_widget(row)

                columns[section_columns.get(section_name, 1)].add_widget(section)

        _sync_inventory_grid_height()
        scroll.add_widget(inventory_grid)
        root.add_widget(scroll)
        close = Button(text="Close", size_hint_y=None, height=dp(44))
        popup = Popup(title="Slay the StarCraft Inventory", content=root, size_hint=(0.98, 0.94))
        popup.bind(on_dismiss=self._slay_end_modal)
        close.bind(on_release=popup.dismiss)
        root.add_widget(close)
        popup.open()

    def draw_slay_edges(self, *_args) -> None:
        if self.campaign_panel is None:
            return
        if self.slay_edge_group is not None:
            try:
                self.campaign_panel.canvas.after.remove(self.slay_edge_group)
            except Exception:
                pass
            self.slay_edge_group = None
        if not slay.enabled(self.ctx) or not self.mission_buttons:
            return

        by_id = {int(button.mission_id): button for button in self.mission_buttons}

        def panel_point(button, x, y):
            # x/y are BUTTON-PARENT coordinates (button.x/center_x/top/etc).
            # Kivy documents initial=True as parent -> window, which avoids the
            # previous mixture of local/relative transforms and all fixed scale
            # correction factors.
            wx, wy = button.to_window(x, y, initial=True)
            return self.campaign_panel.to_widget(wx, wy, relative=True)

        def button_rect(button):
            cx, cy = panel_point(button, button.center_x, button.center_y)
            lx, _ = panel_point(button, button.x, button.center_y)
            rx, _ = panel_point(button, button.right, button.center_y)
            _, by = panel_point(button, button.center_x, button.y)
            _, ty = panel_point(button, button.center_x, button.top)
            return (cx, cy, abs(rx - lx) / 2.0, abs(ty - by) / 2.0)

        # Smooth branch/merge geometry without changing the generated graph.
        # Once the first fully stable map has been drawn, its normalized mission
        # centers are persisted in slay_state.json and reused verbatim on later
        # tab rebuilds/mission returns. This prevents Kivy layout timing from
        # nudging the display-only merge smoothing after a run has started.
        saved_route_layout = {}
        try:
            panel_width = max(1.0, float(self.campaign_panel.width))
            saved_route_layout = slay.route_layout_x_fractions(self.ctx)
            if saved_route_layout and panel_width > dp(100):
                for mid, button in by_id.items():
                    fraction = saved_route_layout.get(mid)
                    if fraction is None:
                        continue
                    current_cx = button_rect(button)[0]
                    target_cx = float(fraction) * panel_width
                    delta = target_cx - current_cx
                    if abs(delta) > 0.05:
                        button.x += delta
                    # A saved layout is an absolute target, not another smoothing
                    # offset. Keep these attributes neutral for compatibility with
                    # buttons created before the layout was first persisted.
                    button.slay_route_x_offset = 0.0
                    button.slay_route_last_shifted_x = float(button.x)
            else:
                route_x = slay.route_horizontal_positions(self.ctx)
                samples = []
                sample_rows = []
                for mid, button in by_id.items():
                    data = slay.node(self.ctx, mid) or {}
                    lane = float(data.get("lane", 0))
                    current_cx = button_rect(button)[0]
                    previous_offset = float(getattr(button, "slay_route_x_offset", 0.0))
                    last_shifted_x = getattr(button, "slay_route_last_shifted_x", None)
                    # GridLayout may reset a child's x on a later resize/layout pass.
                    # If that happened, treat the current geometry as nominal instead
                    # of subtracting an offset that is no longer physically applied.
                    offset_is_applied = (
                        last_shifted_x is not None
                        and abs(float(button.x) - float(last_shifted_x)) <= 0.5
                    )
                    effective_offset = previous_offset if offset_is_applied else 0.0
                    nominal_cx = current_cx - effective_offset
                    samples.append((lane, nominal_cx))
                    sample_rows.append((mid, button, lane, effective_offset))

                unique_lanes = {lane for lane, _cx in samples}
                if len(unique_lanes) >= 2:
                    count = float(len(samples))
                    mean_lane = sum(lane for lane, _cx in samples) / count
                    mean_cx = sum(cx for _lane, cx in samples) / count
                    denominator = sum((lane - mean_lane) * (lane - mean_lane) for lane, _cx in samples)
                    if denominator > 0.0001:
                        lane_step = sum((lane - mean_lane) * (cx - mean_cx) for lane, cx in samples) / denominator
                        if abs(lane_step) > dp(8):
                            for mid, button, lane, effective_offset in sample_rows:
                                desired_offset = lane_step * (float(route_x.get(mid, lane)) - lane)
                                delta = desired_offset - effective_offset
                                if abs(delta) > 0.05:
                                    button.x += delta
                                button.slay_route_x_offset = desired_offset
                                button.slay_route_last_shifted_x = float(button.x)
        except Exception:
            # Position smoothing is cosmetic; never let it prevent the map from
            # rendering if an upstream Kivy geometry detail changes.
            pass

        # Do not draw against Kivy's transient startup layout. Require two
        # consecutive geometry samples to agree before painting connectors.
        try:
            rects = {mid: button_rect(button) for mid, button in by_id.items()}
            geometry = tuple(
                (mid,) + tuple(round(v, 1) for v in rects[mid])
                for mid in sorted(rects)
            )
            xs = [r[0] for r in rects.values()]
            widths = [max(1.0, r[2] * 2.0) for r in rects.values()]
            collapsed = (
                len(xs) >= 3
                and (max(xs) - min(xs)) < max(widths) * 1.5
            )

            if collapsed:
                self.slay_edge_last_geometry = geometry
                self.slay_edge_stable_passes = 0
                if self.slay_edge_retry_count < 24:
                    self.slay_edge_retry_count += 1
                    Clock.schedule_once(self.draw_slay_edges, 0.20)
                return

            if self.slay_edge_last_geometry != geometry:
                self.slay_edge_last_geometry = geometry
                self.slay_edge_stable_passes = 0
                if self.slay_edge_retry_count < 24:
                    self.slay_edge_retry_count += 1
                    Clock.schedule_once(self.draw_slay_edges, 0.15)
                return

            self.slay_edge_stable_passes += 1
            if self.slay_edge_stable_passes < 2:
                Clock.schedule_once(self.draw_slay_edges, 0.15)
                return
            self.slay_edge_retry_count = 0

            # Freeze the first stable display geometry. Save only after the same
            # full map geometry has survived the existing stability checks so a
            # transient startup layout can never become the permanent route map.
            if not saved_route_layout:
                panel_width = max(1.0, float(self.campaign_panel.width))
                if panel_width > dp(100):
                    remembered = slay.remember_route_layout_x_fractions(
                        self.ctx,
                        {mid: float(rects[mid][0]) / panel_width for mid in rects},
                    )
                    if remembered:
                        saved_route_layout = remembered
        except Exception:
            return

        group = InstructionGroup()
        lines = 0
        traversed_edges = slay.traversed_edge_pairs(self.ctx)

        for source_id, dest_id in slay.edge_pairs(self.ctx):
            source = by_id.get(source_id)
            dest = by_id.get(dest_id)
            if source is None or dest is None:
                continue
            try:
                scx, scy, shw, shh = rects[source_id]
                dcx, dcy, dhw, dhh = rects[dest_id]

                vx = dcx - scx
                vy = dcy - scy
                length = (vx * vx + vy * vy) ** 0.5
                if length < 2.0:
                    continue

                # Intersect the center-to-center ray with each mission button's
                # rectangle. This means connectors dynamically begin/end on the
                # side of each button that actually faces the other mission,
                # including diagonal edges.
                avx = abs(vx)
                avy = abs(vy)
                source_t = min(
                    shw / avx if avx > 0.001 else 999999.0,
                    shh / avy if avy > 0.001 else 999999.0,
                )
                dest_t = min(
                    dhw / avx if avx > 0.001 else 999999.0,
                    dhh / avy if avy > 0.001 else 999999.0,
                )

                sx = scx + vx * source_t
                sy = scy + vy * source_t
                dx = dcx - vx * dest_t
                dy = dcy - vy * dest_t

                line_vx = dx - sx
                line_vy = dy - sy
                line_len = (line_vx * line_vx + line_vy * line_vy) ** 0.5
                if line_len < 2.0:
                    continue
                ux = line_vx / line_len
                uy = line_vy / line_len

                # Chosen route history is green; untraveled possible connections
                # retain the normal cyan/blue graph color.
                if (int(source_id), int(dest_id)) in traversed_edges:
                    group.add(Color(0.20, 0.92, 0.34, 1.00))
                else:
                    group.add(Color(0.30, 0.88, 1.00, 1.00))
                group.add(Line(points=[sx, sy, dx, dy], width=1.8))

                # Arrow head is aligned to the connector's real angle instead of
                # always pointing vertically.
                arrow_len = dp(10)
                arrow_half = dp(6)
                bx = dx - ux * arrow_len
                by = dy - uy * arrow_len
                px = -uy
                py = ux
                left_x = bx + px * arrow_half
                left_y = by + py * arrow_half
                right_x = bx - px * arrow_half
                right_y = by - py * arrow_half
                group.add(Line(
                    points=[left_x, left_y, dx, dy, right_x, right_y],
                    width=1.8,
                ))
                lines += 1
            except Exception:
                continue

        if lines:
            self.campaign_panel.canvas.after.add(group)
            self.slay_edge_group = group
        else:
            logging.getLogger("Starcraft2").warning(
                "Slay graph found no drawable route connectors; a later redraw will retry."
            )
    # ----- end Slay the StarCraft v0.2 UI -----

'''

    methods_start = "    # ----- Slay the StarCraft v0.2 UI -----\n"

    methods_end = "    # ----- end Slay the StarCraft v0.2 UI -----\n"

    if methods_start in text:

        if text.count(methods_start) != 1 or text.count(methods_end) != 1:

            raise RuntimeError("Could not uniquely replace existing Slay UI methods")

        ms = text.index(methods_start)

        me = text.index(methods_end, ms) + len(methods_end)

        if me < len(text) and text[me:me + 1] == "\n":

            me += 1

        text = text[:ms] + methods + text[me:]

    else:

        text = insert_before_unique(text, "    def mission_callback(self, button: MissionButton) -> None:", methods, "mission_callback")





    modal_guard = '''        # Slay the StarCraft v0.2 modal click-through guard.
        if getattr(self, "slay_modal_open", False):
            return
'''

    if "Slay the StarCraft v0.2 modal click-through guard" not in text:

        text = insert_after_unique_line(text, "    def mission_callback(self, button: MissionButton) -> None:", modal_guard, "mission_callback definition")



    return text



def patch_galaxy_library(text: str) -> str:

    if 'include "APRogue"' not in text:

        text = insert_after_unique_line(text, 'include "AP_Triggers_Util"', 'include "APRogue" // Slay the StarCraft\n', "AP_Triggers_Util include")









    text = re.sub(r'^[ \t]*APRogue_Init\(\);[^\n]*\n', '', text, flags=re.MULTILINE)

    init_triggers_line = '    libABFE498B_InitTriggers();'

    if text.count(init_triggers_line) != 1:

        raise RuntimeError(f"Expected exactly one InitTriggers call, found {text.count(init_triggers_line)}")

    text = insert_after_unique_line(

        text, init_triggers_line,

        '    APRogue_Init(); // Slay the StarCraft - AFTER AP trigger initialization\n',

        "libABFE498B_InitTriggers call",

    )

    return text





def validate_python(text: str, label: str) -> None:

    compile(text, label, "exec")





def validate_client(text: str) -> None:

    required = [

        "from . import slay_the_starcraft as slay",

        "slay.initialize_context(self)",

        "slay.commit_mission(self, mission_id)",

        "slay.consume_auto_victory_skip(self, mission_id)",

        "def _cmd_victory", "slay.queue_auto_victory(self.ctx)",

        "slay.augment_network_items(ctx, items, item_list)",

        "slay.effect_masks_for_mission(self.ctx, self.mission_id)",

        "?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}",

        "slay.test_potion_run_token(self.ctx)", "slay.progression_flags(self.ctx)", "slay.spear_energy_regen_stacks(self.ctx)", "slay.mercenary_upgrade_packed(self.ctx)", "slay.spear_cooldown_reduction_stacks(self.ctx)", "slay.kerrigan_upgrade_flags(self.ctx)",

        "slay.apply_kerrigan_options(self.ctx, self.mission_id, kerrigan_options)",

        "slay.apply_purchased_kerrigan_tech(self.ctx, zerg_items)",

        "slay.apply_spear_options(self.ctx, self.mission_id, soa_options)",

        "slay.announce_mission_effects(self.ctx, self.mission_id)",

        "def _cmd_rogue_poc",

    ]

    missing = [x for x in required if x not in text]

    if "    def build(self):" in text and "Starcraft 2 Launcher" in text:

        if "Slay the StarCraft v0.2.88 fixed launcher header" not in text:

            missing.append("fixed Shop/Inventory launcher header")

    if "    def on_enter(self):" in text and "class MissionButton" in text:

        if "Slay modal hover guard" not in text:

            missing.append("mission hover modal guard")

    if "is_mod_update_available(DATA_REPO_OWNER, DATA_REPO_NAME, DATA_API_VERSION, current_ver)" in text:

        if 'os.environ.get("SLAY_MANAGED_SC2_DATA") != "1"' not in text:

            missing.append("portable managed-SC2-data online-check guard")

    if missing:

        raise RuntimeError(f"client.py patch validation failed: {missing}")

    validate_python(text, "client.py")





def validate_gui(text: str) -> None:

    required = [

        "slay.ui_signature(self.ctx)", "def open_slay_shop", "def open_slay_inventory",

        "from kivy.loader import Loader", "def _slay_shop_cache_signature", "def _slay_prewarm_shop",

        "def _slay_schedule_shop_prewarm", "Loader.image(icon_url)",
        "def _slay_show_purchase_reveal", "consume_shop_purchase_reveal",

        "slay.mission_tooltip_section", "tooltip = slay_section",

        "def draw_slay_edges", "def _slay_refresh_header", "def _slay_add_difficulty_outline", "def _slay_add_route_state_overlay", "slay_map_summary_paragraphs",

        "SLAY_MISSION_GAP = 36", "spacing=[0, SLAY_MISSION_GAP]",

        "canvas.after.add(group)", "width=1.8", "button.to_window(x, y, initial=True)",

        "source_t = min(", "dest_t = min(", "Arrow head is aligned",

        "route_x = slay.route_horizontal_positions(self.ctx)", "button.slay_route_last_shifted_x",

        "slay_edge_last_geometry", "PURCHASED", "slay_modal_open", "modal click-through guard",

        "slay.shop_render_states",

        "from . import slay_launcher", "self.slay_mission_tab = panel",

        "slay_launcher.install_launcher_tab(self)",

    ]

    missing = [x for x in required if x not in text]

    if "mission_button.tooltip_text = tooltip" in text and "Slay route-state overlays and difficulty warning." not in text:

        missing.append("route-state/difficulty mission overlay hook")

    if missing:

        raise RuntimeError(f"client_gui.py patch validation failed: {missing}")

    validate_python(text, "client_gui.py")









def validate_galaxy_declaration_order(apr_text: str) -> None:



    function_re = re.compile(

        r"^\s*(?:bool|void|int|fixed|string|unit|unitgroup|point)\s+"

        r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*\{"

    )

    declaration_re = re.compile(

        r"^\s*(?:const\s+)?(?:int|fixed|bool|string|unit|unitgroup|point|trigger|revealer|order|playergroup|region)"

        r"(?:\s*\[[^\]]+\])?\s+[A-Za-z_][A-Za-z0-9_]*(?:\s*=.*)?;\s*$"

    )

    lines = apr_text.splitlines()

    for start, line in enumerate(lines):

        match = function_re.match(line)

        if not match:

            continue

        name = match.group(1)

        depth = 1

        executable_seen = False

        for index in range(start + 1, len(lines)):

            current = lines[index]

            stripped = current.strip()

            if stripped and not stripped.startswith(("//", "/*", "*")):

                if declaration_re.match(current):





                    if depth != 1 or executable_seen:

                        raise RuntimeError(

                            f"APRogue.galaxy local declaration outside initial function declaration block in {name} at line {index + 1}: {stripped}"

                        )

                elif depth == 1 and stripped not in {"{", "}"}:

                    executable_seen = True

            depth += current.count("{") - current.count("}")

            if depth == 0:

                break



def validate_galaxy_aprg_calls_declared(apr_text: str) -> None:



    signature_re = re.compile(

        r"^\s*(?:bool|void|int|fixed|string|unit|unitgroup|point)\s+"

        r"(APRG_[A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*(?:\{|;)"

    )

    call_re = re.compile(r"\b(APRG_[A-Za-z_][A-Za-z0-9_]*)\s*\(")

    declared = set()

    for line_no, line in enumerate(apr_text.splitlines(), 1):

        code = line.split("//", 1)[0]

        signature = signature_re.match(code)

        declared_here = signature.group(1) if signature else None

        for name in call_re.findall(code):

            if name == declared_here:

                continue

            if name not in declared:

                raise RuntimeError(

                    f"APRogue.galaxy calls {name} before declaration at line {line_no}"

                )

        if declared_here:

            declared.add(declared_here)





def validate_galaxy(lib_text: str, apr_text: str) -> None:

    if 'include "APRogue"' not in lib_text or "APRogue_Init();" not in lib_text:

        raise RuntimeError("Galaxy library does not initialize APRogue")

    custom_start = lib_text.find("void libABFE498B_InitCustomScript ()")

    init_trigger_call = lib_text.find("    libABFE498B_InitTriggers();")

    apr_init_call = lib_text.find("    APRogue_Init();", init_trigger_call)

    if custom_start < 0 or init_trigger_call < 0 or apr_init_call < 0 or apr_init_call < init_trigger_call:

        raise RuntimeError("APRogue must initialize only after Archipelago InitTriggers")

    custom_end = lib_text.find("}", custom_start)

    if "APRogue_Init();" in lib_text[custom_start:custom_end + 1]:

        raise RuntimeError("APRogue_Init must not run from InitCustomScript")

    if apr_text.count("{") != apr_text.count("}"):

        raise RuntimeError("APRogue.galaxy has unbalanced braces")

    validate_galaxy_declaration_order(apr_text)

    validate_galaxy_aprg_calls_declared(apr_text)

    reflective_damage_event = (

        "TriggerAddEventUnitDamaged(g_aprgReflectiveArmorTrigger, null, "

        "c_unitDamageTypeAny, c_unitDamageEither, null);"

    )

    if reflective_damage_event not in apr_text:

        raise RuntimeError(

            "APRogue.galaxy Reflective Armor damage event does not use the required 5-argument TriggerAddEventUnitDamaged signature"

        )

    if "TriggerAddEventUnitDamaged(g_aprgReflectiveArmorTrigger, null);" in apr_text:

        raise RuntimeError("APRogue.galaxy contains the broken v0.2.49 two-argument TriggerAddEventUnitDamaged call")

    if "while (true)" in apr_text or "for (;;)" in apr_text:

        raise RuntimeError("APRogue.galaxy contains an unbounded loop")





    if "UnitGroupAddUnit(" in apr_text:

        raise RuntimeError("APRogue.galaxy uses invalid Galaxy API UnitGroupAddUnit; use UnitGroupAdd")

    required = [

        'UnitCreate(2, "Carrier"', 'UnitCreate(4, "VoidRay"', 'UnitCreate(6, "Scout"',

         'APRG_CreatePlayerUnitsSafe(1, "SCV"', 'APRG_CreatePlayerUnitsSafe(1, "Probe"', 'APRG_CreatePlayerUnitsSafe(1, "Drone"',

        "APRG_MAX_POINT_ATTEMPTS", "RandomFixed(0.8, 1.2)", "missionTime - 120.0",

        "g_aprgNextDestructionTime = now + 20.0", "c_targetFilterWorker",

        "APRG_QueueRealDropPod", "APRG_WarfieldSoundId", "APRG_SpawnWarfieldOmegaCluster", "APRG_DROP_KIND_WARFIELD_OMEGA",

        "RandomInt(1, 4)", 'UnitCreate(1, "Firebat", c_unitCreateIgnorePlacement',

        "RandomInt(1, 100) > 50", "RandomFixed(20.0, 40.0)",

        "UnitSetPropertyFixed(u, c_unitPropLifeMax, 1.0)", "c_unitPropShieldsMax", "c_unitPropEnergyRegen", "APRG_BLESS_ENERGY_OVERLOAD", "GameGetMissionTime() < 30.0",

        "APRG_MUT_HEROES_OF_STORM", "APRG_MUT_TOO_MANY_WRAITHS", "APRG_MUT_NOT_ENOUGH_ENERGY",

        "APRG_MUT_VOID_THRASHERS", "APRG_TickVoidThrashers", "KaiserWormScourgeMissile", "MinimapPing(PlayerGroupSingle(player)", "APRG_MUT_VIKING_RAIDS", "APRG_MUT_NUCLEAR_ANNIHILATION",

        "APRG_TrySpawnHostileHero", "APRG_SpawnWraithRaid", "APRG_EnforceNotEnoughEnergy",

        "APRG_SpawnVoidThrasher", "APRG_SpawnVikingRaid", "APRG_TickNuclearAnnihilation",

        'AbilityCommand("AssaultMode", 0)', 'PlayerCreateEffectPoint(g_aprgPendingNukeOwner, "NukeDamage"',

        'libNtve_gf_CreateModelAtPoint("GhostNukeIndicator"',

        'CatalogEntryIsValid(c_gameCatalogUnit, "Archon")', 'UnitCreate(1, "Archon", c_unitCreateIgnorePlacement',

        "APRG_RetargetAlliedZombies", "APRG_RetargetHostilePatrollers", "APRG_SetTransportLife(created, 1000.0)", "APRG_EnsureDropperlordTransport",

        "c_unitStateUsingSupply", "APRG_MUT_DARKNESS", "APRG_MUT_ADRENALINE", "APRG_MUT_PICKY_EATERS",

        "APRG_BLESS_EXPLOSIVE_ARMOR", "APRG_BLESS_INSTANT_WORKERS",

        "APRG_MUT_ARMS_RACE", "APRG_AdvanceArmsRace", "APRG_MUT_RISING_GAS_PRICES", "APRG_ApplyRisingGasPrices",

        "CatalogEntryCount(c_gameCatalogUnit)", "libNtve_gf_CatalogFieldValueModifyBasedOnDefaultValue",

        "APRG_BLESS_JUGGERNAUT", "APRG_ApplyJuggernaut",

        "APRG_BLESS_ASSEMBLY_LINE", "APRG_ApplyAssemblyCatalog", "g_aprgAssemblyCatalogApplied", "BuildTime", "InfoArray",

        "APRG_BLESS_ELITE_SOLDIERS", "APRG_ApplyEliteSoldiers",

        "TriggerAddEventUnitTrainProgress", 'c_gameCatalogWeapon, weaponType, "Period"',

        "?APRogue", "StringWord(EventChatMessage(false), 3)", "StringWord(EventChatMessage(false), 4)", "StringWord(EventChatMessage(false), 5)", "g_aprgMaskC", "g_aprgMaskD", "APRG_HasExtension", "APRG_HasExtension2",

        "lib5BD4895D_gv_aP_Core_LOAD_FINISHED_EVENT", "APRG_UpdateMacroBaseReady",

        "APRG_PlayerMacroBaseReady(player)", "g_aprgActivationTime = now + 2.0",

        "APRG_LeviathanNextInterval", "g_aprgLeviathanRampStartTime", "maximum = MaxF(2.0, 20.0",

        "APRG_MUT_OCCASIONAL_THOR", "APRG_MUT_OCCASIONAL_ULTRALISK", "APRG_MUT_OCCASIONAL_COLOSSUS",

        "APRG_MUT_ENEMY_REGENERATION", "APRG_ApplyOccasionalEnemyReplacement", "UnitRemove(u)",

        "APRG_ApplyEnemyRegeneration", "APRG_BLESS_BLINDING_LIGHT", "APRG_ApplyBlindingLight",

        "APRG_BLESS_SPECIALISTS", "APRG_GiveSpecialistsIfReady", "APRG_BLESS_FORTIFICATIONS",

        "APRG_ApplyFortifications", "APRG_BLESS_BANELING_STREAM", "APRG_TickBanelingStream", "g_aprgNextBanelingStreamRetargetTime",

        "APRG_BLESS_TYCHUS", "TychusCommando", "APRG_BLESS_ZAGARAS_AID", "UnitCreate(100, \"Baneling\"",

        "APRG_BLESS_LOGISTICS", "400.0",

        "APRG_DisplayActiveEffects", "c_messageAreaChat", 'StringToText("[Slay] Mutations: "',

        'OrderSetAutoCast(AbilityCommand("CarrierHangar", 0), true)',

        "APRG_EXT_BLESS_OCCASIONAL_THOR", "APRG_EXT_BLESS_OCCASIONAL_ULTRALISK",

        "APRG_EXT_BLESS_OCCASIONAL_COLOSSUS", "APRG_OccasionalBlessing_Func",

        'CatalogEntryIsValid(c_gameCatalogUnit, "TerranDropPod")', 'CatalogEntryIsValid(c_gameCatalogUnit, "ZergDropPod")',

        "g_aprgPendingDropImpactTime[i] = GameGetMissionTime() + 2.6", "APRG_TickPendingDropPods",

        "APRG_EXT_BLESS_UNEXPECTED_EVOLUTION", "APRG_FindUnexpectedEvolutionReplacement",

        "APRG_EXT_BLESS_ANOTHER_GORGON", "APRG_EXT_MUT_ANOTHER_GORGON", '"GehennaCruiser"',

        "APRG_EXT_MUT_BURROWED_ZERGLINGS", '"ZerglingBurrowed"',

        "APRG_EXT_MUT_SNIPER_THOR", "APRG_TrySpawnSniperThor",

        "APRG_EXT_BLESS_HORDE_MODE", "APRG_HordeUnitTypeQualifies", "APRG_ApplyHordeCatalog", "Cost.Cooldown.TimeUse", "InfoArray[", "APRG_HordeTrain_Func", "APRG_HordeCreated_Func", "EventUnitProgressUnit()", "EventUnitCreatedUnit()", "TriggerAddEventUnitCreated", "APRG_HordeOriginalSupply_", "CatalogFieldValueCount(c_gameCatalogAbil", "APRG_ApplyHordeMode", "UnitSetScale(u, 75.0, 75.0, 75.0)",

        "g_aprgFarseersMacroRefreshGiven", "APRG_PlayerMacroBaseReady(player) && !g_aprgFarseersMacroRefreshGiven",

        "20.0 * UnitTypeGetProperty(unitType, c_unitPropSuppliesUsed)",

        'unitType = "DefilerMP"', "APRG_FindRaidOriginAirPoint", "APRG_FindRaidOriginGroundPoint",

        "APRG_FindStaticPatrolAirPoint", "APRG_FindStaticPatrolGroundPoint",

        "APRG_EXT_BLESS_POWER_OVERWHELMING", "APRG_CopyArchonWarpButton", 'TechTreeAbilityAllow(player, AbilityCommand("ArchonWarp", 0), true)', 'UnitAbilityAdd(u, "ArchonWarp")',

        "APRG_EXT_BLESS_DRAKKEN_DRILL", 'UnitAbilityAdd(u, "APRogueBuildDrakkenLaserDrill")', "TechTreeUpgradeAddLevel",

        "APRG_EXT_MUT_JETPACKS", "APRG_JetpacksShellForType", "APRG_ConvertJetpacksUnit", "libNtve_gf_ReplaceUnit", "APRG_TickJetpackAttackWaves", "g_aprgJetpacksProcessed",

        "APRG_RandomHostileBaseAnchor", "APRG_TowerDefenseFrontPoint", "APRG_TickTowerDefenseProbes", "g_aprgNextTowerDefenseTime = now + 30.0", "APRG_TowerDefenseBuildCommandString", "APRG_IssueTowerDefenseBuild", "StringToAbilCmd", "UnitOrderIsValid",

        "APRG_EXT_BLESS_STEALTH_TUNNELS", 'CatalogFieldValueGet(c_gameCatalogUnit, unitType, "FlagArray[Buried]", player)',

    ]

    retired_assembly = ("APRG_AssemblyTrain_Func", "APRG_AssemblyResearch_Func", "APRG_AssemblyConstruct_Func", "TriggerAddEventUnitResearchProgress", "TriggerAddEventUnitConstructProgress")

    stale_assembly = [x for x in retired_assembly if x in apr_text]

    if stale_assembly:

        raise RuntimeError(f"APRogue.galaxy still contains retired Assembly progress handlers: {stale_assembly}")

    missing = [x for x in required if x not in apr_text]

    if missing:

        raise RuntimeError(f"APRogue.galaxy validation failed: {missing}")





def patch_game_data_includes(text: str) -> str:



    catalog_line = f'    <Catalog path="{GAME_DATA_CATALOG_PATH}"/>\n'

    if GAME_DATA_CATALOG_PATH in text:

        ET.fromstring(text)

        return text

    if not text.strip():

        result = '<?xml version="1.0" encoding="utf-8"?>\n<Includes>\n' + catalog_line + '</Includes>\n'

        ET.fromstring(result)

        return result

    if text.count("</Includes>") != 1 or "<Includes" not in text:

        raise RuntimeError("Could not uniquely locate Base.SC2Data/GameData.xml Includes root")

    result = text.replace("</Includes>", catalog_line + "</Includes>", 1)

    ET.fromstring(result)

    return result





def remove_game_data_include(text: str) -> str:



    lines = [line for line in text.splitlines(keepends=True) if GAME_DATA_CATALOG_PATH not in line]

    result = "".join(lines)

    if result.strip():

        ET.fromstring(result)

    return result



def validate_aprogue_data_xml(text: str) -> None:

    root = ET.fromstring(text)

    if root.tag != "Catalog":

        raise RuntimeError("APRogueData.xml root must be <Catalog>")

    required = [

        'id="APRogueBlink"', 'id="APRogueBlinkEffect"',

        'id="ArchonWarp"',

        'DefaultButtonFace="AWrp"', 'id="APRogueBuildDrakkenLaserDrill"',

        'id="APRogueDrakkenUnlocked"', 'id="APRogueHaveDrakken"',

        'AbilCmd="ArchonWarp,SelectedUnits"',

        'AbilCmd="APRogueBuildDrakkenLaserDrill,Build1"',

        'id="APRogueBuildDrakkenLaserDrillButton"',

        'id="APRogueBlinkUnlocked"', 'id="APRogueHaveBlink"',

        'Requirements="APRogueHaveBlink"',

        'FlagArray index="IgnoreUnitBuildTime" value="0"', 'Time="30"', 'Flags index="CreateDefaultButton" value="1"', 'Flags index="UseDefaultButton" value="1"',

        'Name value="Button/Name/APRogueBuildDrakkenLaserDrillButton"',

        'Tooltip value="Button/Tooltip/APRogueBuildDrakkenLaserDrillButton"',

        'id="APRogueCorrosiveClaws"', 'LifeArmorBonus="-1"', 'ShieldArmorBonus="-1"',

    ]

    missing = [marker for marker in required if marker not in text]

    if missing:

        raise RuntimeError(f"APRogueData.xml validation failed: {missing}")

    if '<CUnit default="1">' in text:

        raise RuntimeError("APRogueData.xml must not globally preload Blink on every CUnit")

















BLINK_EXCLUDED_UNIT_IDS = {

    "AP_SoACaster", "AP_SoAAutonomousCaster", "SoACaster", "SOACaster",

    "SpearOfAdunCaster", "VoidSpearofAdun",

}





BLINK_KNOWN_UNIT_IDS = {



    "SCV", "Marine", "Marauder", "Reaper", "Firebat", "Medic", "Ghost", "Spectre", "HERC", "Trooper",

    "Hellion", "Hellbat", "Vulture", "Diamondback", "Goliath", "Warhound", "SiegeTank", "SiegeTankSieged",

    "Cyclone", "Thor", "VikingFighter", "VikingAssault", "Wraith", "Banshee", "Medivac", "ScienceVessel",

    "Raven", "Battlecruiser", "Liberator", "LiberatorAG", "Hercules", "Predator", "WidowMine", "WidowMineBurrowed",

    "DevilDog", "WarPig", "HammerSecurities", "SpartanCompany", "SiegeBreaker", "HelAngels", "DuskWing", "JacksonsRevenge",



    "Drone", "Zergling", "Baneling", "Roach", "Ravager", "Hydralisk", "LurkerMP", "LurkerBurrowed",

    "Queen", "SwarmQueen", "BroodQueen", "Infestor", "DefilerMP", "SwarmHostMP", "Aberration", "Ultralisk", "Torrasque",

    "Mutalisk", "Corruptor", "BroodLord", "Guardian", "Devourer", "Scourge", "Overlord", "Overseer", "Viper",

    "HunterKiller", "DevouringOne", "Tyrannozor",



    "Probe", "Zealot", "Centurion", "Sentinel", "Stalker", "Slayer", "Instigator", "Dragoon", "Adept",

    "Sentry", "Energizer", "Havoc", "HighTemplar", "Signifier", "DarkTemplar", "Avenger", "BloodHunter",

    "Archon", "DarkArchon", "Ascendant", "Supplicant", "Immortal", "Annihilator", "Vanguard", "Wrathwalker",

    "Colossus", "Reaver", "Disruptor", "Stalwart", "Phoenix", "Corsair", "Scout", "Mirage", "VoidRay", "Destroyer",

    "Oracle", "Arbiter", "Carrier", "Tempest", "Mothership", "MothershipCore", "WarpPrism",

}





def _blink_free_slot_from_cunit_body(body: str) -> tuple[int, int]:

    occupied: set[tuple[int, int]] = set()





    card_match = re.search(r'<CardLayouts\b[^>]*>(.*?)</CardLayouts>', body, re.I | re.S)

    card = card_match.group(1) if card_match else body

    for button in re.finditer(r'<LayoutButtons\b([^>]*)/?>', card, re.I | re.S):

        attrs = button.group(1)

        rm = re.search(r'\bRow=["\'](\d+)["\']', attrs, re.I)

        cm = re.search(r'\bColumn=["\'](\d+)["\']', attrs, re.I)

        if rm and cm:

            occupied.add((int(rm.group(1)), int(cm.group(1))))

    for row in range(2, -1, -1):

        for col in range(4, -1, -1):

            if (row, col) not in occupied:

                return row, col

    return 2, 4





def discover_blink_command_card_units(sc2_root: pathlib.Path) -> dict[str, tuple[int, int]]:

    discovered: dict[str, tuple[int, int]] = {}

    mods = sc2_root / "Mods"

    if mods.is_dir():

        for mod in mods.glob("Archipelago*.SC2Mod"):

            if not mod.is_dir():

                continue

            for xml_path in mod.rglob("*.xml"):

                try:

                    if xml_path.stat().st_size > 24 * 1024 * 1024:

                        continue

                    text = xml_path.read_text(encoding="utf-8", errors="ignore")

                except OSError:

                    continue

                if "<CUnit" not in text or "<CardLayouts" not in text:

                    continue

                for match in re.finditer(r'<CUnit\b([^>]*)>(.*?)</CUnit>', text, re.I | re.S):

                    attrs, body = match.group(1), match.group(2)

                    if "<CardLayouts" not in body:

                        continue

                    im = re.search(r'\bid=["\']([^"\']+)["\']', attrs, re.I)

                    if not im:

                        continue

                    unit_id = im.group(1).strip()

                    if unit_id:

                        discovered[unit_id] = _blink_free_slot_from_cunit_body(body)

    return discovered





def inject_blink_loadtime_overrides(text: str, sc2_root: pathlib.Path) -> tuple[str, int]:

    marker = "<!-- SLAY_BLINK_EXPLICIT_COMMAND_CARDS -->"

    if marker in text:

        return text, 0

    slots = discover_blink_command_card_units(sc2_root)

    excluded = {unit_id.casefold() for unit_id in BLINK_EXCLUDED_UNIT_IDS}

    slots = {unit_id: slot for unit_id, slot in slots.items() if unit_id.casefold() not in excluded}

    for unit_id in BLINK_KNOWN_UNIT_IDS:

        if unit_id.casefold() not in excluded:

            slots.setdefault(unit_id, (2, 4))

        ap_unit_id = "AP_" + unit_id

        if ap_unit_id.casefold() not in excluded:

            slots.setdefault(ap_unit_id, (2, 4))

    lines = [f"  {marker}"]

    for unit_id in sorted(slots):

        row, col = slots[unit_id]

        escaped = html.escape(unit_id, quote=True)

        lines.append(f'  <CUnit id="{escaped}">')

        lines.append('    <AbilArray Link="APRogueBlink"/>')

        lines.append('    <CardLayouts index="0">')





        lines.append(f'      <LayoutButtons Face="Blink" Type="AbilCmd" AbilCmd="APRogueBlink,Execute" Requirements="APRogueHaveBlink" Row="{row}" Column="{col}"/>')

        lines.append('    </CardLayouts>')

        lines.append('  </CUnit>')

    block = "\n".join(lines) + "\n"

    if text.count("</Catalog>") != 1:

        raise RuntimeError("Cannot inject Blink CUnit overrides: APRogueData.xml Catalog root is ambiguous")

    return text.replace("</Catalog>", block + "</Catalog>", 1), len(slots)





def patch_mod_game_hotkeys(text: str) -> str:











    lines = text.splitlines(keepends=True)

    found = False

    for i, line in enumerate(lines):

        if not re.match(r"^\s*UI/Hotkey/WarpIn\s*=", line, re.IGNORECASE):

            continue

        ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""

        lines[i] = f"UI/Hotkey/WarpIn=W{ending}"

        found = True

    if not found:

        if lines and not lines[-1].endswith(("\n", "\r")):

            lines[-1] += "\n"

        lines.append("UI/Hotkey/WarpIn=W\n")

    return "".join(lines)





def patch_mod_game_strings(text: str, slay_strings: str) -> str:



    wanted: dict[str, str] = {}

    for raw in slay_strings.splitlines():

        if not raw.strip() or raw.lstrip().startswith("//") or "=" not in raw:

            continue

        key, value = raw.split("=", 1)

        wanted[key.strip()] = value

    lines = text.splitlines()

    seen: set[str] = set()

    result: list[str] = []

    for line in lines:

        if "=" not in line:

            result.append(line)

            continue

        key = line.split("=", 1)[0].strip()

        if key in wanted:

            if key not in seen:

                result.append(f"{key}={wanted[key]}")

                seen.add(key)

            continue

        result.append(line)

    for key, value in wanted.items():

        if key not in seen:

            result.append(f"{key}={value}")

    return "\n".join(result).rstrip("\n") + "\n"





def patch_warpgate_hotkey() -> list[pathlib.Path]:











    homes = [pathlib.Path.home() / "Documents", pathlib.Path.home() / "OneDrive" / "Documents"]

    candidates: set[pathlib.Path] = set()

    for documents in homes:

        sc2 = documents / "StarCraft II"

        offline = sc2 / "Hotkeys"

        if offline.is_dir():

            candidates.update(offline.glob("*.SC2Hotkeys"))

        accounts = sc2 / "Accounts"

        if accounts.is_dir():

            candidates.update(accounts.glob("**/Hotkeys/*.SC2Hotkeys"))

    changed: list[pathlib.Path] = []

    for path in sorted(candidates):

        try:

            text = path.read_text(encoding="utf-8-sig")

        except (OSError, UnicodeError):

            continue

        lines = text.splitlines(keepends=True)

        in_hotkeys = False

        hotkeys_start = None

        hotkeys_end = None

        warp_index = None

        did_change = False

        for i, line in enumerate(lines):

            stripped = line.strip()

            if stripped.startswith("[") and stripped.endswith("]"):

                if in_hotkeys and hotkeys_end is None:

                    hotkeys_end = i

                in_hotkeys = stripped.casefold() == "[hotkeys]"

                if in_hotkeys:

                    hotkeys_start = i

                continue

            if in_hotkeys and re.match(r"^\s*WarpIn\s*=", line, re.IGNORECASE):

                warp_index = i

                ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""

                indent = line[:len(line)-len(line.lstrip())]

                replacement = f"{indent}WarpIn=W{ending}"

                if line != replacement:

                    lines[i] = replacement

                    did_change = True

        if in_hotkeys and hotkeys_end is None:

            hotkeys_end = len(lines)

        if hotkeys_start is not None and warp_index is None:

            insert_at = hotkeys_end if hotkeys_end is not None else len(lines)

            lines.insert(insert_at, "WarpIn=W\n")

            did_change = True

        if did_change:

            path.write_text("".join(lines), encoding="utf-8")

            changed.append(path)

    return changed





def install(ap_root: pathlib.Path, sc2_root: pathlib.Path, source: pathlib.Path) -> None:

    client = ap_root / "worlds" / "sc2" / "client.py"

    gui = ap_root / "worlds" / "sc2" / "client_gui.py"

    runtime_target = ap_root / "worlds" / "sc2" / "slay_the_starcraft.py"

    launcher_target = ap_root / "worlds" / "sc2" / "slay_launcher.py"

    client_entry_target = ap_root / "SlayTheStarCraftLauncher.py"

    ap_docs_target = ap_root / "worlds" / "sc2" / "slay_ap_item_docs.json"

    effect_catalog_target = ap_root / "worlds" / "sc2" / "EFFECT_CATALOG.csv"

    boon_catalog_target = ap_root / "worlds" / "sc2" / "BOON_CATALOG.csv"

    mercenary_catalog_target = ap_root / "worlds" / "sc2" / "MERCENARY_SHOP_CATALOG.csv"

    kerrigan_catalog_target = ap_root / "worlds" / "sc2" / "KERRIGAN_SHOP_CATALOG.csv"

    spear_catalog_target = ap_root / "worlds" / "sc2" / "SPEAR_OF_ADUN_SHOP_CATALOG.csv"

    unit_catalog_target = ap_root / "worlds" / "sc2" / "UNIT_SHOP_CATALOG.csv"

    generator_target = ap_root / "SlayTheStarCraft.py"

    trigger_mod_dir = sc2_root / "Mods" / "ArchipelagoTriggers.SC2Mod"

    trigger_dir = trigger_mod_dir / "Base.SC2Data"

    galaxy_lib = trigger_dir / "LibABFE498B.galaxy"

    apr_target = trigger_dir / "APRogue.galaxy"

    trigger_doc_info = trigger_mod_dir / "DocumentInfo"

    trigger_doc_header = trigger_mod_dir / "DocumentHeader"

    warpgate_game_hotkeys = trigger_mod_dir / "enUS.SC2Data" / "LocalizedData" / "GameHotkeys.txt"

    aprogue_game_strings = trigger_mod_dir / "enUS.SC2Data" / "LocalizedData" / "GameStrings.txt"

    game_data_include = trigger_dir / "GameData.xml"

    aprogue_data_target = trigger_dir / "GameData" / "APRogueData.xml"

    dependency_variant_dir = ap_root / "SlayDependencyVariants"

    dependency_variant_config = dependency_variant_dir / "config.json"

    dependency_variant_paths = {

        name: (dependency_variant_dir / f"{name}.DocumentInfo", dependency_variant_dir / f"{name}.DocumentHeader")

        for name in ("base", "swarm", "void", "swarm_void")

    }



    bundled_runtime = source / "slay_the_starcraft.py"

    bundled_launcher = source / "slay_launcher.py"

    bundled_client_entry = source / "slay_client_entry.py"

    bundled_effect_catalog = source / "EFFECT_CATALOG.csv"

    bundled_boon_catalog = source / "BOON_CATALOG.csv"

    bundled_mercenary_catalog = source / "MERCENARY_SHOP_CATALOG.csv"

    bundled_kerrigan_catalog = source / "KERRIGAN_SHOP_CATALOG.csv"

    bundled_spear_catalog = source / "SPEAR_OF_ADUN_SHOP_CATALOG.csv"

    bundled_unit_catalog = source / "UNIT_SHOP_CATALOG.csv"

    bundled_generator = source / "generate_slay_run.py"

    bundled_apr = source / "APRogue.galaxy"

    bundled_aprogue_data = source / "APRogueData.xml"

    bundled_aprogue_strings = source / "APRogueGameStrings.txt"

    for path, label in [

        (client, "Archipelago worlds/sc2/client.py"), (gui, "Archipelago worlds/sc2/client_gui.py"),

        (galaxy_lib, "ArchipelagoTriggers LibABFE498B.galaxy"),

        (trigger_doc_info, "ArchipelagoTriggers DocumentInfo"),

        (trigger_doc_header, "ArchipelagoTriggers DocumentHeader"),

        (bundled_runtime, "runtime module"),

        (bundled_launcher, "portable launcher module"),

        (bundled_client_entry, "portable launcher client entry"),

        (bundled_effect_catalog, "effect catalog"),

        (bundled_boon_catalog, "boon catalog"),

        (bundled_mercenary_catalog, "mercenary shop catalog"),

        (bundled_kerrigan_catalog, "Kerrigan shop catalog"),

        (bundled_spear_catalog, "Spear of Adun shop catalog"),

        (bundled_unit_catalog, "unit shop catalog"),

        (bundled_generator, "run generator"), (bundled_apr, "APRogue.galaxy"),

        (bundled_aprogue_data, "APRogueData.xml"),

        (bundled_aprogue_strings, "APRogueGameStrings.txt"),

    ]:

        if not path.is_file():

            raise FileNotFoundError(f"{label} not found: {path}")







    for path in (client, gui, galaxy_lib, trigger_doc_info, trigger_doc_header):

        backup = backup_path(path)

        if not backup.exists():

            shutil.copy2(path, backup)

    if warpgate_game_hotkeys.is_file():

        backup = backup_path(warpgate_game_hotkeys)

        if not backup.exists():

            backup.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(warpgate_game_hotkeys, backup)

    if aprogue_game_strings.is_file():

        backup = backup_path(aprogue_game_strings)

        if not backup.exists():

            backup.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(aprogue_game_strings, backup)







    if game_data_include.is_file() and GAME_DATA_CATALOG_PATH not in game_data_include.read_text(encoding="utf-8", errors="ignore"):

        backup = backup_path(game_data_include)

        if not backup.exists():

            backup.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(game_data_include, backup)

    if aprogue_data_target.is_file() and "APRGJetpackMarine" not in aprogue_data_target.read_text(encoding="utf-8", errors="ignore") and "APRogueBlink" not in aprogue_data_target.read_text(encoding="utf-8", errors="ignore"):

        backup = backup_path(aprogue_data_target)

        if not backup.exists():

            backup.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(aprogue_data_target, backup)



    def clean_source(path: pathlib.Path) -> str:

        old = backup_path(path, OLD_BACKUP_SUFFIX)

        v02 = backup_path(path, V02_BACKUP_SUFFIX)

        source_path = old if old.is_file() else (v02 if v02.is_file() else path)

        return source_path.read_text(encoding="utf-8")



    client_original = clean_source(client)

    gui_original = clean_source(gui)

    galaxy_original = clean_source(galaxy_lib)

    apr_text = bundled_apr.read_text(encoding="utf-8")

    trigger_doc_info_original = trigger_doc_info.read_text(encoding="utf-8")

    trigger_doc_header_original = trigger_doc_header.read_bytes()

    warpgate_game_hotkeys_original = warpgate_game_hotkeys.read_text(encoding="utf-8", errors="ignore") if warpgate_game_hotkeys.is_file() else ""

    aprogue_game_strings_original = aprogue_game_strings.read_text(encoding="utf-8", errors="ignore") if aprogue_game_strings.is_file() else ""

    game_data_include_original = game_data_include.read_text(encoding="utf-8", errors="ignore") if game_data_include.is_file() else ""

    aprogue_data_text = bundled_aprogue_data.read_text(encoding="ascii")

    aprogue_data_text, blink_override_count = inject_blink_loadtime_overrides(aprogue_data_text, sc2_root)



    client_new = patch_client(client_original)

    gui_new = patch_gui(gui_original)

    galaxy_new = patch_galaxy_library(galaxy_original)

    trigger_doc_info_new = patch_trigger_document_info(trigger_doc_info_original)

    trigger_doc_header_new = patch_trigger_document_header(trigger_doc_header_original)

    dependency_variant_extras = {

        "base": (),

        "swarm": LEGACY_SLAY_CAMPAIGN_DEPENDENCIES[:2],

        "void": (LEGACY_SLAY_CAMPAIGN_DEPENDENCIES[2],),

        "swarm_void": LEGACY_SLAY_CAMPAIGN_DEPENDENCIES,

    }

    dependency_variant_payloads: dict[str, tuple[str, bytes]] = {}

    for variant_name, extra_deps in dependency_variant_extras.items():

        info_payload = add_trigger_document_info_dependencies(trigger_doc_info_new, extra_deps)

        header_payload = add_trigger_document_header_dependencies(trigger_doc_header_new, extra_deps)

        validate_trigger_dependency_variant(info_payload, header_payload, tuple(extra_deps))

        dependency_variant_payloads[variant_name] = (info_payload, header_payload)

    dependency_variant_config_text = json.dumps({

        "version": 1,

        "target_document_info": str(trigger_doc_info),

        "target_document_header": str(trigger_doc_header),

    }, indent=2, sort_keys=True)

    warpgate_game_hotkeys_new = patch_mod_game_hotkeys(warpgate_game_hotkeys_original)

    aprogue_game_strings_new = patch_mod_game_strings(aprogue_game_strings_original, bundled_aprogue_strings.read_text(encoding="utf-8"))

    game_data_include_new = patch_game_data_includes(game_data_include_original)

    validate_trigger_dependency_metadata(trigger_doc_info_new, trigger_doc_header_new)

    validate_aprogue_data_xml(aprogue_data_text)

    ET.fromstring(game_data_include_new)

    if "UI/Hotkey/WarpIn=W" not in warpgate_game_hotkeys_new:

        raise RuntimeError("Failed to prepare mod-local WarpIn=W GameHotkeys override")

    if "Button/Name/APRogueBuildDrakkenLaserDrillButton=BUILD DRAKKEN LASER DRILL" not in aprogue_game_strings_new:

        raise RuntimeError("Failed to prepare APRogue Drakken localization")

    validate_client(client_new)

    validate_gui(gui_new)

    validate_galaxy(galaxy_new, apr_text)

    validate_python(bundled_runtime.read_text(encoding="utf-8"), "slay_the_starcraft.py")

    validate_python(bundled_launcher.read_text(encoding="utf-8"), "slay_launcher.py")

    validate_python(bundled_client_entry.read_text(encoding="utf-8"), "SlayTheStarCraftLauncher.py")

    validate_python(bundled_generator.read_text(encoding="utf-8"), "SlayTheStarCraft.py")









    post_checks = {

        client: ["mission_launch_summary", "?APRogue {mask_a} {mask_b} {mask_c} {mask_d} {mask_e} {mask_f} {auto_repair_stacks} {progression_flags} {spear_energy_regen_stacks} {mercenary_upgrade_packed} {spear_cooldown_reduction_stacks} {kerrigan_upgrade_flags} {deadly_weapons_stacks} {commander_hero_index} {godmode} {mission_layer} {mission_flags} {mercenary_upgrade_packed2} {test_potion_run_token}", "slay.progression_flags", "slay.spear_energy_regen_stacks", "slay.mercenary_upgrade_packed", "slay.spear_cooldown_reduction_stacks", "slay.kerrigan_upgrade_flags", "slay.apply_kerrigan_options", "slay.apply_purchased_kerrigan_tech(self.ctx, zerg_items)", "def _cmd_addtest", "def _cmd_cleartest", "def _cmd_canceltest", "def _cmd_victory", "def _cmd_boon", "def _cmd_credits", "def _cmd_godmode", "slay.queue_test_effect", "slay.queue_test_clear", "slay.queue_auto_victory", "slay.grant_test_boon", "slay.grant_test_credits", "slay.queue_godmode", "slay.godmode_for_mission", "slay.mission_layer_for_mission", "slay.mission_flags_for_mission", "slay.test_potion_run_token", "slay.consume_auto_victory_skip", "slay.rewrite_print_json_for_effective_rewards(self, args)", "slay.prepare_dependency_variant(ctx, mission_id)"],

        trigger_doc_info: ["ArchipelagoCore.SC2Mod", "ArchipelagoTradeSystem.SC2Mod", "ArchipelagoPatches.SC2Mod"],

        warpgate_game_hotkeys: ["UI/Hotkey/WarpIn=W"],

        aprogue_game_strings: ["Button/Name/APRogueBuildDrakkenLaserDrillButton=BUILD DRAKKEN LASER DRILL", "Button/Tooltip/APRogueBuildDrakkenLaserDrillButton=BUILD DRAKKEN LASER DRILL"],

        game_data_include: [GAME_DATA_CATALOG_PATH],

        aprogue_data_target: [ "APRogueKerriganRecklessPower", "APRogueKerriganRecklessSpeed","APRogueGloriousMartyrStack", 'AdditiveAttackSpeedFactor="0.10"', "APRogueBlink", "APRogueBlinkUnlocked", "APRogueHaveBlink", 'Requirements="APRogueHaveBlink"', "APRogueBuildDrakkenLaserDrill", "APRogueHaveDrakken", "APRogueBuildDrakkenLaserDrillButton", "APRogueEnhancedControl", 'AttackSpeedMultiplier="3"', "APRogueGargantuanTrainedDamage", "APRogueGargantuanLifeArmorQuarter", "APRogueGargantuanShieldArmorQuarter", "APRogueGargantuanRangeQuarter", "APRogueVikingAnchors", 'AttackSpeedMultiplier="2"', 'SuppressMoving', "APRogueCorrosiveClaws", "APRogueCloakedNightmare", 'StateFlags index="Cloak" value="1"', "APRogueUnstableColossi15", 'LifeArmorBonus="-1"', 'ShieldArmorBonus="-1"', 'Requirements="APRogueHaveBlink"', 'SLAY_BLINK_EXPLICIT_COMMAND_CARDS', '<AbilArray Link="APRogueBlink"/>', 'AbilCmd="ArchonWarp,SelectedUnits"'],

        gui: ["size_hint_x=0.80", "size_hint_x=0.10", "SLAY_MISSION_GAP = 36", "button.to_window(x, y, initial=True)", "width=1.8", "source_t = min(", "slay_edge_geometry_trigger"],

        runtime_target: [ "DANGER_OUTLIER_MARGIN = 250", "DANGER_CREDIT_BONUS = 100", "_mission_is_difficulty_outlier_in_nodes", "SPEAR_COOLDOWN_REDUCTION", "SPEAR_PRICE_DISCOUNT", "KERRIGAN_PRICE_DISCOUNT", "KERRIGAN_RECKLESS_POWER", "KERRIGAN_RECKLESS_SPEED", "spear_cooldown_reduction_stacks", "kerrigan_upgrade_flags", "Kerrigan available", "warfields_reinforcements", "energy_overload", "heroes_of_the_storm", "too_many_wraiths", "not_enough_energy", "void_thrashers", "viking_raids", "nuclear_annihilation", "darkness", "adrenaline", "picky_eaters", "explosive_armor", "instant_workers", "arms_race", "rising_gas_prices", "juggernaut", "assembly_line", "elite_soldiers", "squishy", "forced_variety", "occasional_thor_mutation", "enemy_regeneration", "blinding_light", "specialists", "fortifications", "baneling_stream", "tychus", "zagaras_aid", "logistics", "occasional_thor_blessing", "occasional_ultralisk_blessing", "occasional_colossus_blessing", "unexpected_evolution", "another_gorgon_blessing", "another_gorgon_mutation", "burrowed_zerglings", "sniper_thor", "horde_mode", "tower_defense", "cloaked_nightmare", "rapid_repair", "blink_blessing", "power_overwhelming", "drakken_laser_drill_blessing", "jetpacks", "stealth_tunnels", "lurker_defense", "combat_workers", "rapid_evolution_mutation", "no_deaths_allowed", "glass_cannons", "victory_is_temporary", "odin", "nuclear_workers", "bounty_kills", "tactical_binoculars", "building_overcharge", "ghost_reporting", "taldarim_reinforcements", "double_time", "shrinkage", "mineral_thieves", "active_enemies", "reflective_armor", "buddy_system", "torrasque", "nexus_shield", "gargantuan_enemies", "raynors_raiders", "boon_defender", "boon_fire_power", "boon_roachling_mines", "boon_broodling_evolution", "boon_adamantium_blades", "boon_enhanced_control", "boon_banshee_swarm", "boon_enlarged_banelings", "permanent_boons", "shop_expansion", "shop_cycle_purchases", "effective_bought", "route_horizontal_positions", "route_layout_x_fractions", "remember_route_layout_x_fractions", "_is_deprecated_item", "SHOP_STOCK_LOGIC_VERSION = 110", "MISSION_FLAG_LAB_RAT_OPENING = 8192", "MISSION_FLAG_IMMORTAL_ZERGLING = 16384", "def test_potion_run_token", "immortal_zergling", "_stock_after_progression_unlock", "DEFENSIVE_STRUCTURE_ITEMS", "shop_sections", "BOON_PREFIX", "sync_duplicate_item_replacements", "FIVE_X_GENERIC_UPGRADE_ITEMS", "STACKABLE_GENERAL_UPGRADE_ITEMS", "_effective_actual_item_count", "'purifier': (4, 512)", "_same_shop_50_percent_price", "_is_general_upgrade_item", "announce_mission_effects", "test_mission_overrides", "_test_override_for_mission", "RACE_GLOBAL_UPGRADE_ITEMS", "TERRAN_CONTRACTS", "ZERG_CONTRACTS", "KERRIGAN_UNLOCK", "SPEAR_UNLOCK", "SPEAR_ENERGY_REGEN", "progression_flags", "spear_energy_regen_stacks", "mercenary_upgrade_packed", "MERCENARY_CUSTOM_UPGRADE_ITEMS", "MERCENARY_SHOP_PRICE_OVERRIDES", "apply_kerrigan_options", "apply_purchased_kerrigan_tech", "Terran Upgrades", "Mercenary Contracts", "Spear of Adun", "boon_corrosive_claws", "boon_unlimited_power", "boon_unstable_colossi", "boon_hyrda_storms", "boon_mobile_siege", "spear_of_adun_blessing", "dehakas_pack", "zombie_apocalypse", "resource_swap", "boon_missile_defense", "boon_chaos_blessings", "maskE=", "maskF=", "autoRepairStacks=", "50% chance", "allied infested terran"],

        launcher_target: ["PACKAGE_VERSION = \"1.0.2.17\"", "SLAY_LAUNCHER_MODE", "SLAY_RUN_DIR", "def generate_run", "class ServerProcess", "def install_launcher_tab"],

        client_entry_target: ["worlds.sc2.client", "launch()"],

        generator_target: ['PACKAGE_VERSION = "1.0.2.17"', "LANES = 4", "CANVAS_WIDTH = 7", "def _generate_active_lanes", "\'dark_archons\': 1", "\'void_thrashers\': 4", "\'viking_raids\': 2", "\'nuclear_annihilation\': 3", "\'energy_overload\': 1", '"starting_credits": int(starting_credits)', "--starting-credits", "expected_tier", "opening_bias", "OPENING_POOL_WEIGHTS", "required_race", "window_keys", "for _pass in range(2):", "STARTING_STRUCTURE_UNIT_EXCLUSIONS", "LIMITED_BANK_MISSION_EXCLUSIONS", "DETECTOR_OPTIONS_BY_RACE", "DEFENSIVE_STRUCTURE_ITEMS", "mission_pool", "minimum_pool_for_layer", "SHOP_PRIORITY_ITEMS", '"victory_cache": 0', "difficulty_reward = 300 * (mission_tier - expected_tier)", "effect_reward = (150 * int(mutation_value)) - (100 * int(blessing_value)) + (100 * layer_number)", "occasional_thor_mutation", "enemy_regeneration", "blinding_light", "baneling_stream", "logistics", "occasional_thor_blessing", "occasional_ultralisk_blessing", "occasional_colossus_blessing", "unexpected_evolution", "another_gorgon_blessing", "another_gorgon_mutation", "burrowed_zerglings", "sniper_thor", "horde_mode", "tower_defense", "cloaked_nightmare", "rapid_repair", "blink_blessing", "power_overwhelming", "drakken_laser_drill_blessing", "jetpacks", "stealth_tunnels", "'compounding_interest': 2", "forbidden_blessings.add(\"rapid_repair\")", "forbidden_blessings.add(\"stealth_tunnels\")", "DEFERRED_EFFECTS: list[str] = [", "dependency_sensitive_effect_exclusions", "SWARM_DEPENDENCY_MUTATIONS", "VOID_DEPENDENCY_MUTATIONS", "EFFECT_SELECTION_WEIGHT", "MUTATION_SELECTION_WEIGHT", "mutation_profile=True", "immortal_zergling", "no_deaths_allowed", "tactical_binoculars", "lurker_defense", "combat_workers", "building_overcharge", "ghost_reporting", "taldarim_reinforcements", "glorious_martyrs", "double_time", "shrinkage", "mineral_thieves", "active_enemies", "infinite_larva", "reflective_armor", "buddy_system", "torrasque", "nexus_shield", "gargantuan_enemies", "raynors_raiders", "'purifier': 4", "'dehakas_pack': 5", "'zombie_apocalypse': 5", "'marauder_kill_teams': 2", "'resource_pickups': 1"],

        apr_target: ["?APRogue", "LOAD_FINISHED_EVENT", "APRG_UpdateMacroBaseReady", "RandomInt(1, 100) > 50", "APRG_BLESS_ENERGY_OVERLOAD", "APRG_MUT_HEROES_OF_STORM", "APRG_MUT_TOO_MANY_WRAITHS", "APRG_MUT_NOT_ENOUGH_ENERGY", "APRG_MUT_VOID_THRASHERS", "APRG_TickVoidThrashers", "KaiserWormScourgeMissile", "MinimapPing(PlayerGroupSingle(player)", "APRG_MUT_VIKING_RAIDS", "APRG_MUT_NUCLEAR_ANNIHILATION", 'APRG_CreatePlayerUnitsSafe(1, "SCV"', 'AbilityCommand("AssaultMode", 0)', '"GhostNukeIndicator"', "APRG_RetargetAlliedZombies", "c_unitStateSelectable", "APRG_SetTransportLife(created, 1000.0)", "APRG_EnsureDropperlordTransport", "c_unitStateUsingSupply", "APRG_MUT_DARKNESS", "APRG_MUT_ADRENALINE", "APRG_MUT_PICKY_EATERS", "APRG_BLESS_EXPLOSIVE_ARMOR", "APRG_BLESS_INSTANT_WORKERS", "APRG_MUT_ARMS_RACE", "APRG_MUT_RISING_GAS_PRICES", "APRG_BLESS_JUGGERNAUT", "APRG_BLESS_ASSEMBLY_LINE", "APRG_ApplyAssemblyCatalog", "APRG_BLESS_ELITE_SOLDIERS", "APRG_ApplyEliteToGroup", "oldMax * 0.7", "APRG_MUT_SQUISHY", "APRG_MUT_FORCED_VARIETY", "APRG_ForcedVariety_Func", "APRG_TickWarfieldBurst", "APRG_TickWarfieldVOQueue", "SoundLengthSync(line)", "APRG_LeviathanNextInterval", "APRG_MUT_ENEMY_REGENERATION", "APRG_BLESS_BANELING_STREAM", "APRG_BLESS_LOGISTICS", "APRG_DisplayActiveEffects", "CarrierHangar", "APRG_EXT_BLESS_OCCASIONAL_THOR", "APRG_OccasionalBlessing_Func", "APRG_QueueRealDropPod", "TerranDropPod", "ZergDropPod", "APRG_EXT_BLESS_UNEXPECTED_EVOLUTION", "APRG_EXT_BLESS_ANOTHER_GORGON", "APRG_EXT_MUT_ANOTHER_GORGON", "APRG_EXT_MUT_BURROWED_ZERGLINGS", "APRG_EXT_MUT_SNIPER_THOR", "APRG_EXT_BLESS_HORDE_MODE", "APRG_HordeUnitTypeQualifies", "APRG_ApplyHordeCatalog", "Cost.Cooldown.TimeUse", "CatalogFieldValueCount(c_gameCatalogAbil", "APRG_EXT_MUT_TOWER_DEFENSE", "APRG_EXT_MUT_CLOAKED_NIGHTMARE", "APRG_EXT_BLESS_RAPID_REPAIR", "APRG_EXT_BLESS_BLINK", "APRG_EXT_BOON_VIKING_ANCHORS", "APRG_ApplyVikingAnchors", "APRG_EXT3_BOON_CORROSIVE_CLAWS", "APRG_MercenaryUpgradeStacks", "APRG_SpearGate_Func", "UnitModifyCooldown(caster, link, duration, c_cooldownOperationSet)", "APRG_TickSpearEnergyBonus", "APRG_KerriganRespawnDelay", "APRogueKerriganRecklessPower", "APRG_ApplyMercenaryRecruitCatalog", "APRG_TickMercenaryUpgrades", "APRG_MercenaryDamage_Func", "APRG_EXT3_BOON_UNLIMITED_POWER", "APRG_EXT3_BOON_UNSTABLE_COLOSSI", "APRG_EXT3_BOON_ARCHON_CANNONS", "APRG_EXT3_BOON_HYRDA_STORMS", "APRG_EXT3_BOON_MOBILE_SIEGE", "APRG_EXT3_MUT_PURIFIER", "APRG_TickPurifier", "PurifierPlanetCracker", "APRG_EXT3_BLESS_SPEAR_OF_ADUN", "APRG_EXT3_BLESS_SPEAR_OVERCHARGE", "APRG_EXT3_MUT_DEHAKAS_PACK", "APRG_EXT3_MUT_ZOMBIE_APOCALYPSE", "APRG_EXT3_MUT_ARGUMENTS", "APRG_EXT3_MUT_COMBAT_PAY", "APRG_EXT3_MUT_NUCLEAR_STRUCTURES", "APRG_EXT3_MUT_RESOURCE_SWAP", "APRG_EXT3_BLESS_RICH_VESPENE", "APRG_EXT3_BLESS_RICH_MINERALS", "APRG_EXT3_BOON_MISSILE_DEFENSE", "APRG_EXT3_BOON_STRETCHY_SPINES", "APRG_EXT3_BOON_GARGANTUAN_UNITS", "APRG_ApplyGargantuanToTrainedUnit", "APRG_CanonicalProtossReinforcementType", "ProtossGenericWarpInOut", "libNtve_gf_PauseUnit(u, true)", "libNtve_gf_AttachModelToUnitInheritVisibility", "g_aprgPurifierBeamStopTime", "g_aprgPurifierAllianceBeamStopTime", "APRG_EXT3_BOON_CHAOS_BLESSINGS", "APRG_HydraStorms_Func", "APRG_ApplyMobileSiege", "APRG_TickUnlimitedPower", "APRG_TickUnstableColossi", "APRG_TickHeroRegeneration", "APRG_TickHordeLarva", "APRG_GoldenArmadaEarlySafety", "APRG_RetargetZagaraBanelings", "APRG_IsScriptedPurifier", "APRG_WraithRaidNextInterval", "APRG_CorrosiveClaws_Func", "UnitAbilityAdd(u, \"APRogueBlink\")", "UnitAbilityExists(u, \"APRogueBlink\")", "APRG_EXT_BLESS_POWER_OVERWHELMING", "APRG_CopyArchonWarpButton", 'TechTreeAbilityAllow(player, AbilityCommand("ArchonWarp", 0), true)', 'UnitAbilityAdd(u, "ArchonWarp")', "APRG_EXT_BLESS_DRAKKEN_DRILL", "APRG_EXT_MUT_JETPACKS", "APRG_JetpacksShellForType", "APRG_ConvertJetpacksUnit", "libNtve_gf_ReplaceUnit", "APRG_TickJetpackAttackWaves", "g_aprgJetpacksProcessed", "APRG_EXT_BLESS_STEALTH_TUNNELS", "APRG_StealthTunnelSpeed_", "InfestorBurrowed", "APRG_EXT_BLESS_LURKER_DEFENSE", "APRG_EXT_BLESS_COMBAT_WORKERS", "APRG_EXT_MUT_RAPID_EVOLUTION", "APRG_EXT_MUT_NO_DEATHS_ALLOWED", "APRG_EXT_BLESS_GLASS_CANNONS", "APRG_EXT_MUT_VICTORY_TEMPORARY", "APRG_EXT_BLESS_ODIN", "APRG_EXT_MUT_NUCLEAR_WORKERS", "APRG_EXT_BLESS_BOUNTY_KILLS", "APRG_EXT_MUT_TACTICAL_BINOCULARS", "g_aprgFarseersMacroRefreshGiven", "20.0 * UnitTypeGetProperty", "DefilerMP", "APRG_FindRaidOriginAirPoint", "nearestFriendlyDistance", "APRG_FindStaticPatrolGroundPoint", "BurrowZerglingUp", "APRG_CreateRealGorgon", 'AnimCopy ::external.GorgonFinderTag', "APRG_RegisterBanelingSources", "g_aprgNextBanelingStreamRetargetTime", "RandomFixed(5.0, 15.0)", "VoidThrasherWalker", "UnitWeaponAdd(target, weaponType, null)", "APRG_RandomHostileBaseAnchor", "APRG_TowerDefenseFrontPoint", "APRG_TickTowerDefenseProbes", "APRogueCloakedNightmare", "UnitBehaviorAdd(u, \"APRogueCloakedNightmare\", u, 1)", "RepairTime", "g_aprgNukeDetonateTime = now + 19.0", "APRG_CarrierGetsFreeInterceptors", "APRG_EnsurePlayerInterceptorCost", "g_aprgAlliedTargetBlacklist", "APRG_EnemyTargetableStructures", "APRG_AlliedBuildingTargetUntil_", "c_targetFilterInvulnerable", "APRG_ApplyPickyEaters", "APRG_NearestPathablePlayerStructure", "PointPathingIsConnected", "APRG_DisableGeneratedHeroRevive", "APRG_EXT_BLESS_BUILDING_OVERCHARGE", "APRG_EXT_BLESS_GHOST_REPORTING", "APRG_EXT_MUT_TALDARIM_REINFORCEMENTS", "APRG_CreateRealGorgon", "APRG_EXT2_MUT_MIRAS_MERCENARIES", "APRG_TickMiraMercenaries", "APRG_FindMiraCampPoint", '"HelsAngelFighter", 5', "APRG_EXT2_BLESS_GLORIOUS_MARTYRS", "APRG_ApplyGloriousMartyrs", "APRogueGloriousMartyrStack", "APRG_EXT2_BLESS_INFLATABLE_SOLDIERS", "APRG_TickInflatableSoldiers", "g_aprgInflatableBaseSpeed", "OrderTargetingUnit(AbilityCommand(\"attack\", 0), target)", "APRG_CreatePlayerUnitsVanillaSafe", "GhostCloak", "APRG_FindHeroPatrolOrigin", "APRG_AddBestDonorWeaponAnyState", "APRG_OrderBanelingStreamUnit", "APRG_SpeedyCatalog_", 'c_gameCatalogWeapon, weaponType, "Range"', "APRG_EXT2_MUT_DOUBLE_TIME", "APRG_ApplyDoubleTime", "APRG_EXT2_MUT_SHRINKAGE", "APRG_TickShrinkage", "APRG_EXT2_MUT_MINERAL_THIEVES", "APRG_TickMineralThieves", "APRG_EXT2_MUT_ACTIVE_ENEMIES", "APRG_TickActiveEnemies", "APRG_EXT2_BLESS_INFINITE_LARVA", "APRG_TickInfiniteLarva", "APRG_EXT2_MUT_ZAGARAS_BANELINGS", "APRG_TickZagarasBanelings", "BANELINGS INCOMING", "APRG_EXT2_BLESS_REFLECTIVE_ARMOR", "APRG_TickBuddySystem", "APRG_TickTorrasque", "APRG_TickNexusShield", "APRG_ApplyGargantuanEnemies", "APRG_EXT2_MUT_RAYNORS_RAIDERS", "APRG_TickRaynorsRaiders", "APRG_CacheFixedPatrolPoints", "APRG_RandomFixedPatrolPoint", "APRG_DROP_KIND_RAYNOR_ASSAULT", "APRG_DROP_KIND_RAYNOR_REPAIR", "APRG_EXT2_BOON_DEFENDER", "APRG_DefenderDamage_Func", "APRG_ReaperBlitzDamage_", "blitzAccumulatedDamage += damage;", "APRG_EXT2_BOON_FIRE_POWER", "APRG_ApplyFirePower", "APRG_EXT2_BOON_ROACHLING_MINES", "APRG_EXT2_BOON_BROODLING_EVOLUTION", "APRG_BOON_ADAMANTIUM_BLADES", "APRG_ReconcileAdamantiumWeapons", "APRG_ReconcileAdamantiumDamageField", "APRG_BOON_ENHANCED_CONTROL", "APRG_EnhancedControl_Func", "APRG_BOON_BANSHEE_SWARM", "APRG_BansheeSwarm_Func", "APRG_BOON_ENLARGED_BANELINGS", "APRG_ApplyEnlargedBanelings", "APRG_IsZergTownHallType", "APRG_TickRaynorRepairSCVs", 'OverlordTransport', 'APRG_PlayerSpawnCatalogType', 'UnitCreate(1, "MULE"', 'AbilityCommand("Smart", 0)', 'APRG_DeathSpawnExcluded', 'c_unitBehaviorFlagTimedLife', '"APRG_Uncommandable_" + IntToString(UnitGetTag(dead))'],

    }



    prepared_text = {

        client: client_new,

        trigger_doc_info: trigger_doc_info_new,

        gui: gui_new,

        runtime_target: bundled_runtime.read_text(encoding="utf-8"),

        launcher_target: bundled_launcher.read_text(encoding="utf-8"),

        client_entry_target: bundled_client_entry.read_text(encoding="utf-8"),

        **{ap_root / name: (source / name).read_text(encoding="utf-8-sig") for name in ("slay_command_ui.py", "slay_ui_support.py", "slay_ui_icons.json", "slay_endless_ui.py")},

        generator_target: bundled_generator.read_text(encoding="utf-8"),

        apr_target: apr_text,

        warpgate_game_hotkeys: warpgate_game_hotkeys_new,

        aprogue_game_strings: aprogue_game_strings_new,

        game_data_include: game_data_include_new,

        aprogue_data_target: aprogue_data_text,

    }

    for prepared_path, markers in post_checks.items():

        prepared = prepared_text[prepared_path]

        missing = [marker for marker in markers if marker not in prepared]

        if missing:

            raise RuntimeError(

                f"Pre-install package verification failed for {prepared_path.name}: {missing}"

            )







    dependency_variant_live_targets = [dependency_variant_config]

    for info_path, header_path in dependency_variant_paths.values():

        dependency_variant_live_targets.extend((info_path, header_path))

    live_targets = (client, gui, galaxy_lib, trigger_doc_info, trigger_doc_header, runtime_target, launcher_target, client_entry_target, ap_docs_target, effect_catalog_target, boon_catalog_target, mercenary_catalog_target, kerrigan_catalog_target, spear_catalog_target, unit_catalog_target, generator_target, apr_target, warpgate_game_hotkeys, aprogue_game_strings, game_data_include, aprogue_data_target, *dependency_variant_live_targets)

    prior_bytes = {

        target: (target.read_bytes() if target.exists() else None)

        for target in live_targets

    }



    try:

        client.write_text(client_new, encoding="utf-8")

        gui.write_text(gui_new, encoding="utf-8")

        galaxy_lib.write_text(galaxy_new, encoding="utf-8")

        trigger_doc_info.write_text(trigger_doc_info_new, encoding="utf-8")

        trigger_doc_header.write_bytes(trigger_doc_header_new)

        dependency_variant_dir.mkdir(parents=True, exist_ok=True)

        dependency_variant_config.write_text(dependency_variant_config_text, encoding="utf-8")

        for variant_name, (info_payload, header_payload) in dependency_variant_payloads.items():

            info_path, header_path = dependency_variant_paths[variant_name]

            info_path.write_text(info_payload, encoding="utf-8")

            header_path.write_bytes(header_payload)

        warpgate_game_hotkeys.parent.mkdir(parents=True, exist_ok=True)

        warpgate_game_hotkeys.write_text(warpgate_game_hotkeys_new, encoding="utf-8")

        aprogue_game_strings.parent.mkdir(parents=True, exist_ok=True)

        aprogue_game_strings.write_text(aprogue_game_strings_new, encoding="utf-8")

        game_data_include.parent.mkdir(parents=True, exist_ok=True)

        game_data_include.write_text(game_data_include_new, encoding="utf-8")

        aprogue_data_target.parent.mkdir(parents=True, exist_ok=True)

        aprogue_data_target.write_text(aprogue_data_text, encoding="ascii")

        shutil.copy2(bundled_runtime, runtime_target)

        shutil.copy2(bundled_launcher, launcher_target)

        shutil.copy2(bundled_client_entry, client_entry_target)

        for name in ("slay_command_ui.py", "slay_ui_support.py", "slay_ui_icons.json", "slay_endless_ui.py"):
            shutil.copy2(source / name, ap_root / name)





        refresh_ap_content_docs_cache(ap_docs_target)

        shutil.copy2(bundled_effect_catalog, effect_catalog_target)

        shutil.copy2(bundled_boon_catalog, boon_catalog_target)

        shutil.copy2(bundled_mercenary_catalog, mercenary_catalog_target)

        shutil.copy2(bundled_kerrigan_catalog, kerrigan_catalog_target)

        shutil.copy2(bundled_spear_catalog, spear_catalog_target)

        shutil.copy2(bundled_unit_catalog, unit_catalog_target)

        shutil.copy2(bundled_generator, generator_target)

        apr_target.write_text(apr_text, encoding="utf-8")





        validate_trigger_dependency_metadata(

            trigger_doc_info.read_text(encoding="utf-8"),

            trigger_doc_header.read_bytes(),

        )

        for variant_name, extra_deps in dependency_variant_extras.items():

            info_path, header_path = dependency_variant_paths[variant_name]

            validate_trigger_dependency_variant(

                info_path.read_text(encoding="utf-8"), header_path.read_bytes(), tuple(extra_deps)

            )

        ET.fromstring(game_data_include.read_text(encoding="utf-8"))

        validate_aprogue_data_xml(aprogue_data_target.read_text(encoding="ascii"))

        for written_path, markers in post_checks.items():

            installed_text = written_path.read_text(encoding="utf-8")

            missing = [marker for marker in markers if marker not in installed_text]

            if missing:

                raise RuntimeError(

                    f"Post-install verification failed for {written_path}: {missing}"

                )

    except Exception:

        for target, old_bytes in prior_bytes.items():

            try:

                if old_bytes is None:

                    if target.exists():

                        target.unlink()

                else:

                    target.parent.mkdir(parents=True, exist_ok=True)

                    target.write_bytes(old_bytes)

            except Exception:

                pass

        raise











    if os.environ.get("SLAY_PORTABLE_BUILD", "").strip().lower() in {"1", "true", "yes", "on"}:

        changed_hotkeys = []

    else:

        changed_hotkeys = patch_warpgate_hotkey()

    if changed_hotkeys:

        print(f"  Warpgate hotkey: restored WarpIn=W in {len(changed_hotkeys)} custom profile(s).")

    print(f"  Warpgate hotkey: installed mod-local UI/Hotkey/WarpIn=W override at {warpgate_game_hotkeys}")

    print(f"  Blink UI: installed {blink_override_count} explicit load-time CUnit command-card override(s); runtime command-card writes are no longer used.")

    print(f"  Drakken UI: native BuildDrakkenLaserDrill icon/button + player-specific Slay tooltip override installed at {aprogue_game_strings}")

    print("Slay the StarCraft v1.0.2.17 installed successfully.")

    print(f"  Client:     {client}")

    print(f"  GUI:        {gui}")

    print(f"  Runtime:    {runtime_target}")

    print(f"  Launcher:   {launcher_target}")

    print(f"  Entry:      {client_entry_target}")

    print(f"  Generator:  {generator_target}")

    print(f"  Galaxy:     {apr_target}")

    print(f"  GameData:   {aprogue_data_target}")

    print(f"  SC2 deps:   stock by default; mission-selected variants installed at {dependency_variant_dir}")

    sc2process = ap_root / "worlds" / "_sc2common" / "bot" / "sc2process.py"

    if sc2process.is_file():

        sc2process_text = sc2process.read_text(encoding="utf-8", errors="ignore")

        if "-extramods" in sc2process_text and "Swarm.SC2Campaign" in sc2process_text:

            print("WARNING: worlds/_sc2common/bot/sc2process.py still contains the temporary -extramods Gorgon test.")

            print("         Revert that temporary edit; Slay no longer uses global campaign dependencies.")

    print("Next: run SlayTheStarCraft.py from your Archipelago checkout to generate a run.")





def _restore_preferred(path: pathlib.Path) -> bool:





    old = backup_path(path, OLD_BACKUP_SUFFIX)

    v02 = backup_path(path, V02_BACKUP_SUFFIX)

    if old.is_file():

        shutil.copy2(old, path)

        old.unlink()

        if v02.exists():

            v02.unlink()

        return True

    if v02.is_file():

        shutil.copy2(v02, path)

        v02.unlink()

        return True

    return False





def uninstall(ap_root: pathlib.Path, sc2_root: pathlib.Path) -> None:

    client = ap_root / "worlds" / "sc2" / "client.py"

    gui = ap_root / "worlds" / "sc2" / "client_gui.py"

    runtime_target = ap_root / "worlds" / "sc2" / "slay_the_starcraft.py"

    launcher_target = ap_root / "worlds" / "sc2" / "slay_launcher.py"

    client_entry_target = ap_root / "SlayTheStarCraftLauncher.py"

    effect_catalog_target = ap_root / "worlds" / "sc2" / "EFFECT_CATALOG.csv"

    boon_catalog_target = ap_root / "worlds" / "sc2" / "BOON_CATALOG.csv"

    mercenary_catalog_target = ap_root / "worlds" / "sc2" / "MERCENARY_SHOP_CATALOG.csv"

    kerrigan_catalog_target = ap_root / "worlds" / "sc2" / "KERRIGAN_SHOP_CATALOG.csv"

    spear_catalog_target = ap_root / "worlds" / "sc2" / "SPEAR_OF_ADUN_SHOP_CATALOG.csv"

    unit_catalog_target = ap_root / "worlds" / "sc2" / "UNIT_SHOP_CATALOG.csv"

    generator_target = ap_root / "SlayTheStarCraft.py"

    trigger_mod_dir = sc2_root / "Mods" / "ArchipelagoTriggers.SC2Mod"

    trigger_dir = trigger_mod_dir / "Base.SC2Data"

    galaxy_lib = trigger_dir / "LibABFE498B.galaxy"

    apr_target = trigger_dir / "APRogue.galaxy"

    trigger_doc_info = trigger_mod_dir / "DocumentInfo"

    trigger_doc_header = trigger_mod_dir / "DocumentHeader"

    warpgate_game_hotkeys = trigger_mod_dir / "enUS.SC2Data" / "LocalizedData" / "GameHotkeys.txt"

    aprogue_game_strings = trigger_mod_dir / "enUS.SC2Data" / "LocalizedData" / "GameStrings.txt"

    game_data_include = trigger_dir / "GameData.xml"

    aprogue_data_target = trigger_dir / "GameData" / "APRogueData.xml"

    dependency_variant_dir = ap_root / "SlayDependencyVariants"



    restored = sum(_restore_preferred(path) for path in (client, gui, galaxy_lib, trigger_doc_info, trigger_doc_header))

    if not _restore_preferred(warpgate_game_hotkeys) and warpgate_game_hotkeys.exists():

        warpgate_game_hotkeys.unlink()

    if not _restore_preferred(aprogue_game_strings) and aprogue_game_strings.exists():

        aprogue_game_strings.unlink()

    if not _restore_preferred(aprogue_data_target) and aprogue_data_target.exists():

        aprogue_data_target.unlink()

    if not _restore_preferred(game_data_include) and game_data_include.exists():

        cleaned = remove_game_data_include(game_data_include.read_text(encoding="utf-8", errors="ignore"))

        if "<Catalog" in cleaned:

            game_data_include.write_text(cleaned, encoding="utf-8")

        else:

            game_data_include.unlink()

    for path in (runtime_target, launcher_target, client_entry_target, effect_catalog_target, boon_catalog_target, mercenary_catalog_target, kerrigan_catalog_target, spear_catalog_target, unit_catalog_target, generator_target, apr_target):

        if path.exists():

            path.unlink()

    if dependency_variant_dir.exists():

        shutil.rmtree(dependency_variant_dir)

    print(f"Slay the StarCraft uninstalled; restored {restored} backed-up source files.")

    print("Generated run/state JSON files are intentionally left in place as run data.")





_native_patch_client = patch_client

def patch_client(text):
    from slay_endless_client import patch_endless_client
    return patch_endless_client(_native_patch_client(text))

def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument("--archipelago", required=True, type=pathlib.Path)

    parser.add_argument("--sc2", required=True, type=pathlib.Path)

    parser.add_argument("--uninstall", action="store_true")

    args = parser.parse_args()

    try:

        if args.uninstall:

            uninstall(args.archipelago.resolve(), args.sc2.resolve())

        else:

            install(args.archipelago.resolve(), args.sc2.resolve(), pathlib.Path(__file__).resolve().parent)

    except Exception as exc:

        print(f"ERROR: {exc}", file=sys.stderr)

        return 1

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

