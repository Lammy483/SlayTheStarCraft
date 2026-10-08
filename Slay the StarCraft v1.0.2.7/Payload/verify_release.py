from __future__ import annotations
import argparse, ast, csv, importlib.util, py_compile, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RELEASE_ROOT=ROOT.parent
VERSION="1.0.2.7"

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
    if (RELEASE_ROOT/"VERSION.txt").read_text(encoding="utf-8").strip()!=VERSION: raise RuntimeError("VERSION.txt mismatch")
    exe = (RELEASE_ROOT/"SlayTheStarCraft.exe").read_bytes()
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
            raise RuntimeError(f"Missing v1.0.2.7 mutation name: {expected}")
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
            raise RuntimeError(f"Missing v1.0.2.7 runtime fix: {token}")
    for token in (
        'order_weights = [EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in pool]',
        'weighted_order.append(pick)',
    ):
        if token not in generator:
            raise RuntimeError(f"Missing v1.0.2.7 development weighting fix: {token}")
    for token in (
        'unit[512] g_aprgAllyWarpUnit;',
        'g_aprgAllyWarpTime[best] = now + 3.0;',
        'APRG_QueuePurifierEscortWarp',
        'bool[32] g_aprgPurifierWarpEscort;',
    ):
        if token not in galaxy:
            raise RuntimeError(f"Missing v1.0.2.7 warp-in fix: {token}")
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
            raise RuntimeError(f"Missing v1.0.2.7 document update: {token}")
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
            raise RuntimeError(f"Missing v1.0.2.7 Galaxy fix: {token}")
    if "'true_golden_armada': 10.0" not in generator:
        raise RuntimeError("True Golden Armada is not 10x weighted in development")


def main():
    pa=argparse.ArgumentParser(); pa.add_argument("--archipelago",required=True,type=Path); pa.add_argument("--sc2",required=True,type=Path); a=pa.parse_args()
    try: check_python(); check_payload(); check_archipelago_patch(a.archipelago.resolve(),a.sc2.resolve())
    except Exception as exc: print(f"Release verification failed: {exc}",file=sys.stderr); return 1
    print(f"Slay the StarCraft v{VERSION} release verification passed."); return 0
if __name__=="__main__": raise SystemExit(main())
