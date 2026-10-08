from __future__ import annotations
import argparse, ast, csv, importlib.util, py_compile, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RELEASE_ROOT=ROOT.parent
VERSION="1.0.2.17"

def load_installer():
    spec=importlib.util.spec_from_file_location("slay_release_installer", ROOT/"install_slay.py")
    if spec is None or spec.loader is None: raise RuntimeError("Could not load release installer.")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def check_python():
    for path in list(ROOT.glob("*.py"))+list((RELEASE_ROOT/"Tools").glob("*.py")):
        py_compile.compile(str(path),doraise=True)

def check_embedded_gui_methods():
    source=(ROOT/"install_slay.py").read_text(encoding="utf-8")
    tree=ast.parse(source)
    methods=None
    for node in ast.walk(tree):
        if not isinstance(node,ast.Assign) or not isinstance(node.value,ast.Constant) or not isinstance(node.value.value,str):
            continue
        if any(isinstance(target,ast.Name) and target.id=="methods" for target in node.targets):
            methods=node.value.value
            break
    if methods is None: raise RuntimeError("Could not locate embedded GUI methods block")
    compile("class SlayGuiProbe:\n"+methods,"<slay_gui_methods>","exec")

def check_catalog(path, expected):
    with path.open(encoding="utf-8-sig",newline="") as h:
        r=csv.DictReader(h); fields=tuple(r.fieldnames or ()); rows=list(r)
    if fields!=expected: raise RuntimeError(f"Unexpected columns in {path.name}: {fields}")
    if not rows: raise RuntimeError(f"{path.name} is empty.")

def check_payload():
    check_embedded_gui_methods()
    verify_v1025_changes(ROOT)
    verify_v1026_changes(ROOT)
    verify_v1027_changes(ROOT)
    verify_v1028_changes(ROOT)
    verify_v1029_changes(ROOT)
    verify_v10210_changes(ROOT)
    verify_v10211_changes(ROOT)
    verify_v10213_changes(ROOT)
    verify_v10214_changes(ROOT)
    verify_v10215_changes(ROOT)
    verify_v10216_changes(ROOT)
    verify_v10217_changes(ROOT)
    if (RELEASE_ROOT/"VERSION.txt").read_text(encoding="utf-8").strip()!=VERSION: raise RuntimeError("VERSION.txt mismatch")
    exe_path = RELEASE_ROOT / "SlayTheStarCraft.exe"
    if exe_path.is_file():
        exe = exe_path.read_bytes()
        if VERSION.encode("ascii") not in exe: raise RuntimeError("Compiled launcher version mismatch")
    launcher_go = (RELEASE_ROOT/"Tools"/"slay_launcher_windows.go").read_text(encoding="utf-8")
    expected_download_text = "nothing is installed globally, everything is installed in this folder."
    if expected_download_text not in launcher_go: raise RuntimeError("First-launch data-location text mismatch")
    for fn in ("slay_the_starcraft.py","generate_slay_run.py","slay_launcher.py"):
        if VERSION not in (ROOT/fn).read_text(encoding="utf-8"): raise RuntimeError(f"{fn} release version mismatch")
    check_catalog(ROOT/"EFFECT_CATALOG.csv",("Title","Mutation or Blessing","Description","Severity"))
    check_catalog(ROOT/"BOON_CATALOG.csv",("Boon Title","Description","Cost"))
    for fn in ("KERRIGAN_SHOP_CATALOG.csv","MERCENARY_SHOP_CATALOG.csv","SPEAR_OF_ADUN_SHOP_CATALOG.csv"):
        check_catalog(ROOT/fn,("Item Title","Description","Cost"))
    check_catalog(ROOT/"UNIT_SHOP_CATALOG.csv",("Unit","Price"))
    ET.parse(ROOT/"APRogueData.xml")
    galaxy=(ROOT/"APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        "APRG_UpdateMacroBaseReady", "APRG_TickPurifier", "APRG_RepathRandomHeroesOfStormHero",
        "APRG_ApplyBuildingOvercharge", "APRG_ApplyGodModeCatalog", "?APRogue",
        "APRG_AlarakHeroType", "APRG_FindInvasionFleetDropPoint",
        'if (abilityType == "ArchonWarp") { continue; }',
        'APRG_HideScvJumpJetsCommandCard',
        'APRG_HideScvJumpJetsButtonsForType',
        '"FlagArray[ArmySelect]"', 'c_playerAny, "1"', "respawnElapsed >= respawnDelay - 2.0",
        "bestScore = 999999.0", "APRG_VorazunHeroType", "VorazunChampion",
        "APRG_TrySwannFlamingBetty", '"FlamingBetty"', 'return "TychusCommando"',
        "APRG_FindValidCommanderHeroType", "return APRG_FindValidCommanderHeroType();",
    ):
        if token not in galaxy: raise RuntimeError(f"Missing Galaxy development symbol: {token}")
    if "UnitGroupAddUnit(" in galaxy: raise RuntimeError("Invalid Galaxy UnitGroupAddUnit call")
    runtime=(ROOT/"slay_the_starcraft.py").read_text(encoding="utf-8")
    for token in (
        "def prepare_kerrigan_options",
        'campaign != "Heart of the Swarm" and _progression_owned(ctx, KERRIGAN_UNLOCK)',
        'inventory_received_snapshot',
        'commander_hero_index(ctx, mission_id) in {10, 30}',
        '_purchased_count(ctx, item_name) < 3',
        'status not in {"future","available","selected"}',
        'def consume_shop_purchase_reveal',
    ):
        if token not in runtime: raise RuntimeError(f"Missing development runtime token: {token}")
    generator=(ROOT/"generate_slay_run.py").read_text(encoding="utf-8")
    if '"kerrigan_primal_status": "always_zerg"' not in generator: raise RuntimeError("Kerrigan latent form is not Always Zerg")
    for token in ("DEFAULT_CAMPAIGN_LENGTH = 12", "def _base_effect_means", "def _is_final_quarter", "def _is_past_halfway", "def _effect_selection_weight", "--mutation-frequency-multiplier", "--blessing-frequency-multiplier", '"extra_shop_slots"', '"start_with_spear"', '"start_with_kerrigan"'):
        if token not in generator: raise RuntimeError(f"Missing dynamic-run generator token: {token}")
    launcher=(ROOT/"slay_launcher.py").read_text(encoding="utf-8")
    for token in ("Campaign Length", "Mutation Frequency Multiplier", "Blessing Frequency Multiplier", "Extra Shop Slots", "Start with Spear of Adun", "Start with Kerrigan"):
        if token not in launcher: raise RuntimeError(f"Missing launcher setting: {token}")
    if "def _fresh_state_from_config" not in runtime: raise RuntimeError("Missing starting-progression state initialization")
    for token in ("queue_test_effect","queue_test_clear","queue_auto_victory","grant_test_boon","grant_test_credits","queue_godmode","godmode_for_mission"):
        if token not in runtime: raise RuntimeError(f"Missing beta debug support: {token}")
    installer=(ROOT/"install_slay.py").read_text(encoding="utf-8")
    # Release cleanup intentionally keeps version metadata out of gameplay-source banner checks.
    runtime_postcheck_prefix = 'runtime_target: ['
    runtime_postcheck_start = installer.find(runtime_postcheck_prefix)
    runtime_postcheck_end = installer.find('launcher_target:', runtime_postcheck_start)
    if runtime_postcheck_start < 0 or runtime_postcheck_end < 0:
        raise RuntimeError("Could not locate installer runtime post-check block")
    runtime_postcheck = installer[runtime_postcheck_start:runtime_postcheck_end]
    if f"Slay the StarCraft v{VERSION}" in runtime_postcheck:
        raise RuntimeError("Installer must not require a release banner inside slay_the_starcraft.py")
    for token in ("def _cmd_addtest","def _cmd_cleartest","def _cmd_canceltest","def _cmd_victory","def _cmd_boon","def _cmd_credits","def _cmd_godmode","def _cmd_rogue_poc"):
        if token not in installer: raise RuntimeError(f"Missing beta client debug command: {token}")
    if "slay.prepare_kerrigan_options(self.ctx)" not in installer: raise RuntimeError("Installer missing pre-pack Kerrigan normalization patch")
    for token in ("def _slay_show_purchase_reveal", "slay.consume_shop_purchase_reveal(self.ctx)"):
        if token not in installer: raise RuntimeError(f"Installer missing randomized shop reward popup support: {token}")
    # Validate the clean bundled Galaxy payload without requiring a release/version banner inside it.
    # This catches accidental verifier-only requirements before Download Data reaches the patch stage.
    installer_module=load_installer()
    host_library='include "APRogue"\nvoid libABFE498B_InitCustomScript () {\n}\nvoid libABFE498B_TestInit () {\n    libABFE498B_InitTriggers();\n    APRogue_Init();\n}\n'
    installer_module.validate_galaxy(host_library, galaxy)
    bootstrap=(RELEASE_ROOT/"Tools"/"bootstrap_slay_runtime.ps1").read_text(encoding="utf-8")
    if "Refreshing the private Archipelago source for the open beta release" in bootstrap: raise RuntimeError("Open beta must not force-refresh existing Archipelago source")
    for token in ("[IO.Path]::GetTempPath()", "Limit-ArchipelagoToSc2AtRoot", '"SlayAP-" + $ArchipelagoRef'):
        if token not in bootstrap: raise RuntimeError(f"Missing long-path-safe Archipelago extraction token: {token}")
    manifest=(RELEASE_ROOT/"launcher_manifest.json").read_text(encoding="utf-8")
    if '"release_channel": "open_beta"' not in manifest: raise RuntimeError("Development manifest channel mismatch")

def check_archipelago_patch(ap_root,sc2_root):
    installer=load_installer()
    client=ap_root/"worlds"/"sc2"/"client.py"; gui=ap_root/"worlds"/"sc2"/"client_gui.py"; gal=sc2_root/"Mods"/"ArchipelagoTriggers.SC2Mod"/"Base.SC2Data"/"LibABFE498B.galaxy"
    for p in (client,gui,gal):
        if not p.is_file(): raise RuntimeError(f"Required runtime file is missing: {p}")
    pc=installer.patch_client(client.read_text(encoding="utf-8")); pg=installer.patch_gui(gui.read_text(encoding="utf-8")); apr=(ROOT/"APRogue.galaxy").read_text(encoding="utf-8"); pgal=installer.patch_galaxy_library(gal.read_text(encoding="utf-8"))
    installer.validate_client(pc); installer.validate_gui(pg); installer.validate_galaxy(pgal,apr)
    for token in ("def _cmd_addtest","def _cmd_victory","def _cmd_credits","def _cmd_godmode"):
        if token not in pc: raise RuntimeError(f"Patched client missing {token}")


def verify_v1025_changes(payload_dir: Path) -> None:
    slay_text = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    galaxy_text = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    catalog_text = (payload_dir / "EFFECT_CATALOG.csv").read_text(encoding="utf-8")
    for expected in (
        "Hellion Run-by", "Diamondbacks", "Leviathan Approaching", "Odin",
        "Ultimate Harassment", "Brakk's Pack", "Orlan's Planetary Fortress", "Enemy Spear of Adun",
    ):
        if expected not in slay_text or expected not in catalog_text:
            raise RuntimeError(f"Missing v1.0.2.17 mutation name: {expected}")
    for forbidden_note in (
        "Every 45 seconds after your base is established",
        "A Wings of Liberty Leviathan waits in enemy territory",
        "Combines Viking Raids",
    ):
        if forbidden_note in catalog_text:
            raise RuntimeError(f"Implementation notes leaked into EFFECT_CATALOG: {forbidden_note}")
    for expected in (
        "libNtve_gf_PauseUnit(u, true)",
        "libNtve_gf_PauseUnit(u, false)",
        "libNtve_gf_AttachModelToUnitInheritVisibility",
        "libNtve_gf_SetOpacity(1.0, 3.0)",
        "g_aprgPurifierWarpTime[best] = now + 3.0",
    ):
        if expected not in galaxy_text:
            raise RuntimeError(f"Missing deterministic warp-in implementation: {expected}")

def verify_v1026_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        'campaign != "Heart of the Swarm" and _progression_owned(ctx, KERRIGAN_UNLOCK)',
        'inventory_received_snapshot',
        'len(live_records) >= len(snapshot)',
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 runtime fix: {token}")
    for token in (
        'order_weights = [EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in pool]',
        'weighted_order.append(pick)',
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.17 development weighting fix: {token}")
    for token in (
        'unit[512] g_aprgAllyWarpUnit;',
        'g_aprgAllyWarpTime[best] = now + 3.0;',
        'APRG_QueuePurifierEscortWarp',
        'bool[32] g_aprgPurifierWarpEscort;',
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 warp-in fix: {token}")
    if 'libNtve_gf_CreateModelAtPoint("ProtossGenericWarpInOut"' in galaxy:
        raise RuntimeError("Legacy point-only Protoss warp visual is still present")


def verify_v1027_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    catalog = (payload_dir / "EFFECT_CATALOG.csv").read_text(encoding="utf-8")
    for token in (
        "True Golden Armada",
        "A massive golden armada patrols the map",
        "MISSION_FLAG_TRUE_GOLDEN_ARMADA = 4096",
        "'combined_raids': 5",
    ):
        if token not in runtime and token not in generator and token not in catalog:
            raise RuntimeError(f"Missing v1.0.2.17 document update: {token}")
    for token in (
        "APRG_DiamondbackWanderDestination",
        "RandomInt(1, 100) <= 60",
        "g_aprgTorrasqueRespawnTime = now + 5.0",
        "g_aprgMacroReadyTime + 180.0",
        "elapsed >= 720.0",
        "APRG_TickTrueGoldenArmada",
        "APRG_TryTrueGoldenOracleRevelation",
        'UnitCreate(20, "Phoenix"',
        'UnitCreate(3, "Oracle"',
        "g_aprgEffectsSummaryDisplayed",
        "APRG_DisplayActiveEffects(player)",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Galaxy fix: {token}")
    for development_only in (
        "hellion_run_by", "diamondback_wanderers", "leviathan_outside_base",
        "odin_delayed_assault", "combined_raids", "brakk_primal_army",
        "orlan_fortress", "enemy_spear_of_adun", "true_golden_armada",
    ):
        if f"'{development_only}': 10.0" in generator:
            raise RuntimeError(f"Development-only selection boost still enabled: {development_only}")



def verify_v1028_changes(payload_dir: Path) -> None:
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        "g_aprgBaseLeviathanFirstDamageTriggered",
        "g_aprgBaseLeviathanBurstRemaining = 20",
        "APRG_ClaimBaseLeviathanSpawnlings",
        'AbilityCommand("stop", 0)',
        "g_aprgDelayedOdinSpawned",
        "APRG_OdinBarrageTarget",
        'AbilityCommand("OdinBarrage", 0)',
        "APRG_ClearFriendlyBlocker",
        'return "BattlecruiserMerc"',
        "APRG_TryOrlanTrainSCV",
        "APRG_SpawnOrlanReplacementSCV",
        "g_aprgNextCloneRetargetTime = now + 10.0",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Galaxy fix: {token}")


def verify_v1029_changes(payload_dir: Path) -> None:
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    for token in (
        "bool APRG_OrderStandardMove",
        "bool APRG_OrderAttackMove",
        "bool APRG_OrderAttackPlayer",
        "bool APRG_OrderPatrolMap",
        "unitgroup g_aprgMarauderKillTeamOne",
        "unitgroup g_aprgMarauderKillTeamTwo",
        "APRG_OrderMarauderKillTeamGroup",
        "UnitGroupHasUnit(g_aprgMarauderKillTeamUnits, enemy)",
        "UnitGroupHasUnit(g_aprgGoldenFleet, enemy)",
        "UnitGroupHasUnit(g_aprgDarkTemplarRaiders, enemy)",
        "g_aprgFriendlySupportAbilityCursor",
        "g_aprgFriendlyZombieAbilityCursor",
        "APRG_OrderAttackMove(clone, UnitGetPosition(target))",
        "APRG_OrderAttackMove(u, UnitGetPosition(target))",
        "void APRG_QueuePriorAutonomousOrder",
        "c_orderQueueAddToEnd",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 standardized AI fix: {token}")
    kill_team_start = galaxy.find("void APRG_OrderMarauderKillTeamGroup")
    kill_team_end = galaxy.find("void APRG_ApplyKillTeamMedicVisual", kill_team_start)
    if kill_team_start < 0 or kill_team_end < 0:
        raise RuntimeError("Missing v1.0.2.17 Marauder Kill Team patrol implementation")
    kill_team_block = galaxy[kill_team_start:kill_team_end]
    if "APRG_OrderAttackMove(u, destination)" not in kill_team_block:
        raise RuntimeError("Marauder Kill Teams are not attack-moving through patrol destinations")
    for token in (
        "def _shop_unit_parent_is_available",
        "def _unit_upgrade_has_shop_available_parent",
        "and not _unit_upgrade_has_shop_available_parent(ctx, name, owned_unlocks, table, selected_races)",
        "and not _unit_upgrade_has_shop_available_parent(ctx, item_name, owned_unlocks, table)",
        "if _unit_upgrade_requires_locked_unit(ctx, parent_name, owned_unlocks, table):",
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 race-upgrade shop fix: {token}")



def verify_v10210_changes(payload_dir: Path) -> None:
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        "def mission_pool_distribution",
        "beta = -MISSION_POOL_TILT_STEEPNESS * math.log(remaining)",
        "tier_weights=mission_pool_distribution(layer, choice_layers)",
        "desired_pool = rng.choices(all_tiers, weights=roll_weights, k=1)[0]",
        "return 4 if final else 0",
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.17 mission-tier distribution fix: {token}")
    for token in (
        "bool APRG_GoldenPatrolRouteSafe",
        "APRG_PointNearPlayerOrAlliedBuilding(sample, player, 30.0)",
        "GameGetMissionTime() < 600.0",
        "APRG_SetGroupMovementSpeed(g_aprgGoldenFleet, 1.9)",
        "APRG_SetGroupMovementSpeed(g_aprgTrueGoldenFleet, 1.9)",
        "c_unitPropLifeMax, 1000.0",
        "c_unitPropShieldsMax, 1000.0",
        'CatalogEntryIsValid(c_gameCatalogUnit, "JacksonsRevenge")',
        "CatalogEntryCount(c_gameCatalogUnit)",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Golden Armada/Orlan fix: {token}")


def verify_v10211_changes(payload_dir: Path) -> None:
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    for token in (
        "MISSION_POOL_TILT_STEEPNESS = 1.8",
        "MISSION_TIER_MUTATION_SEVERITY_PER_TIER = 2.0",
        "RED_DANGER_MARGIN = 250",
        "mission_tier_mut_shift = (expected_pool - float(mission_pool)) * MISSION_TIER_MUTATION_SEVERITY_PER_TIER",
        "scaled_mut_mean = max(0.0, (mut_mean + difficulty_mut_shift + mission_tier_mut_shift) * mut_factor)",
        "+ RED_DANGER_MARGIN",
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.17 mission pacing fix: {token}")
    for token in (
        "SHOP_STOCK_LOGIC_VERSION = 110",
        "def _unit_upgrade_available_from_owned_or_current_stock",
        "race_unit_stock = _weighted_shop_sample",
        "ctx, name, owned_unlocks, race_unit_stock, table",
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 current-shop upgrade fix: {token}")
    installer = (payload_dir / "install_slay.py").read_text(encoding="utf-8")
    if '"SHOP_STOCK_LOGIC_VERSION = 110"' not in installer:
        raise RuntimeError("Installer preflight shop-stock version is stale")
    if '"SHOP_STOCK_LOGIC_VERSION = 108"' in installer:
        raise RuntimeError("Installer still contains obsolete shop-stock version 108")



def verify_v10213_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        "MISSION_FLAG_LAB_RAT_OPENING = 8192",
        'mission_name.casefold() == "lab rat"',
        "DANGER_OUTLIER_MARGIN = 250",
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 Lab Rat runtime flag: {token}")
    for token in (
        'StringContains(unitType, "Locust", c_stringAnywhere, c_stringNoCase)',
        'StringContains(unitType, "Interceptor", c_stringAnywhere, c_stringNoCase)',
        'DataTableGetBool(true, "APRG_Uncommandable_" + tag)',
        "APRG_IsWorkerTypeForDeath(unitType)",
        "c_playerPropMineralsCollected",
        "c_playerPropSuppliesMade",
        "mineralsCollected - g_aprgLabRatMineralsCollectedStart < 300",
        'StringToText("Odin incoming!")',
        'StringToText("Brakk\'s Pack incoming!")',
        'return "AP_SoAAutonomousCaster";',
        "g_aprgEnemySpearSecondaryCaster",
        'APRG_TryEnemySpearCast(player, "Orbital", false)',
        "g_aprgNextEnemySpearNormalTime = now + 5.0",
        "APRG_NormalizeMutationLeviathanCombatCooldown",
        'basePath + ".Cooldown.TimeUse", owner, "120"',
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Galaxy fix: {token}")



def verify_v10214_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    bootstrap = (payload_dir.parent / "Tools" / "bootstrap_slay_runtime.ps1").read_text(encoding="utf-8")
    for token in (
        'DISABLED_MUTATIONS = {"enemy_spear_of_adun"}',
        '_upgrade_pack_race_is_unlocked(ctx, race, owned_unlocks)',
        'return _owned_race_unit_unlock_count(ctx, race, owned_unlocks, table) >= 3',
        'SHOP_STOCK_LOGIC_VERSION = 110',
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 runtime fix: {token}")
    if 'DEFERRED_EFFECTS: list[str] = ["shrinkage", "enemy_spear_of_adun"]' not in generator:
        raise RuntimeError("Enemy Spear of Adun is not disabled in generation")
    for token in (
        'DataTableGetBool(true, "APRG_HadTimedLife_" + IntToString(UnitGetTag(u)))',
        'APRG_RecordTimedLifeUnit',
        'APRG_TimedLifeCreated_Func',
        'TriggerAddEventUnitCreated(g_aprgTimedLifeCreatedTrigger',
        'Enemy Spear of Adun is disabled pending a reliable campaign-compatible implementation.',
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Galaxy fix: {token}")
    for token in (
        'all-retained-world-requirements-v3-direct-mpyq',
        'Installing pure-Python mpyq module directly',
        'raw.githubusercontent.com/eagleflo/mpyq/master/mpyq.py',
        "mpyq direct module passed",
    ):
        if token not in bootstrap:
            raise RuntimeError(f"Missing v1.0.2.17 bootstrap fix: {token}")


def verify_v10215_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    catalog = (payload_dir / "EFFECT_CATALOG.csv").read_text(encoding="utf-8")
    installer = (payload_dir / "install_slay.py").read_text(encoding="utf-8")
    for token in (
        "MUTATION_SELECTION_WEIGHT = {1: 0.40, 2: 0.65, 3: 1.10, 4: 1.50, 5: 1.85}",
        "0.80 if mutation_profile else 1.35",
        "mutation_profile=True",
        "'immortal_zergling': 1",
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.17 mutation weighting/content update: {token}")
    for token in (
        "Immortal Zergling",
        "A single immortal zergling attacks you constantly",
        "MISSION_FLAG_IMMORTAL_ZERGLING = 16384",
        "def test_potion_run_token",
    ):
        if token not in runtime and token not in catalog:
            raise RuntimeError(f"Missing v1.0.2.17 runtime/catalog update: {token}")
    for token in (
        "APRG_TickImmortalZergling",
        'UnitCreate(1, "Zergling"',
        "c_unitStateInvulnerable, true",
        "c_unitStateTargetable, false",
        "g_aprgMacroReadyTime + 60.0",
        "g_aprgNextImmortalZerglingTargetTime = now + 60.0",
        "APRG_OrderAttackMove(g_aprgImmortalZergling",
        "APRG_TickTestPotionUI",
        "TEST POTION  |  +1000 MINERALS",
        "minerals + 1000",
        "TestMineralPotionRunToken",
        "StringWord(EventChatMessage(false), 20)",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 Galaxy prototype: {token}")
    for token in (
        "test_potion_run_token = slay.test_potion_run_token(self.ctx)",
        "{mercenary_upgrade_packed2} {test_potion_run_token}",
        "slay.test_potion_run_token",
    ):
        if token not in installer:
            raise RuntimeError(f"Missing v1.0.2.17 client potion handshake: {token}")



def verify_v10216_changes(payload_dir: Path) -> None:
    runtime = (payload_dir / "slay_the_starcraft.py").read_text(encoding="utf-8")
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    for token in (
        'GORGON_MISSION_EXCLUSIONS = {"fire in the sky"}',
        'forbidden_mutators.add("another_gorgon_mutation")',
        'forbidden_blessings.add("another_gorgon_blessing")',
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.17 Fire in the Sky Gorgon exclusion: {token}")
    for token in (
        'mission_name.casefold() in GORGON_MISSION_EXCLUSIONS and effect == "another_gorgon_blessing"',
        'mission_name.casefold() in GORGON_MISSION_EXCLUSIONS and effect == "another_gorgon_mutation"',
    ):
        if token not in runtime:
            raise RuntimeError(f"Missing v1.0.2.17 runtime Gorgon exclusion: {token}")
    for token in (
        'string APRG_CommanderHeroDisplayName(string heroType)',
        'StringToText(APRG_CommanderHeroDisplayName(g_aprgCommanderHeroType) + " has respawned")',
        'StringToText("Kerrigan has respawned")',
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 hero respawn notification: {token}")

def verify_v10217_changes(payload_dir: Path) -> None:
    generator = (payload_dir / "generate_slay_run.py").read_text(encoding="utf-8")
    galaxy = (payload_dir / "APRogue.galaxy").read_text(encoding="utf-8")
    if 'EFFECT_SELECTION_MULTIPLIER = {"general": 3.0, "multi_class": 2.0}' not in generator:
        raise RuntimeError("New-effect development selection boosts were not removed")
    for token in (
        "destination = RegionRandomPoint(RegionPlayableMap());",
        "this deliberately allows routes through the player's base",
        'OrderTargetingPoint(AbilityCommand("attack", 0), destination)',
        "if (GameGetMissionTime() < 600.0 && g_aprgFixedPatrolPointCount > 0)",
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.17 True Golden Armada patrol update: {token}")


def main():
    pa = argparse.ArgumentParser()
    pa.add_argument("--archipelago", type=Path)
    pa.add_argument("--sc2", type=Path)
    pa.add_argument("--source-only", action="store_true", help="Validate the repository source tree without requiring a local Archipelago/SC2 installation.")
    a = pa.parse_args()
    try:
        check_python()
        check_payload()
        if not a.source_only:
            if a.archipelago is None or a.sc2 is None:
                pa.error("--archipelago and --sc2 are required unless --source-only is used")
            check_archipelago_patch(a.archipelago.resolve(), a.sc2.resolve())
    except Exception as exc:
        print(f"Release verification failed: {exc}", file=sys.stderr)
        return 1
    mode = "source verification" if a.source_only else "release verification"
    print(f"Slay the StarCraft v{VERSION} {mode} passed.")
    return 0
if __name__=="__main__": raise SystemExit(main())
