



from __future__ import annotations



import argparse

import json

import shutil

import tempfile

import zipfile

from pathlib import Path





def _safe_extract(zip_path: Path, destination: Path) -> None:

    destination = destination.resolve()

    with zipfile.ZipFile(zip_path) as zf:

        for member in zf.infolist():

            candidate = (destination / member.filename).resolve()

            try:

                candidate.relative_to(destination)

            except ValueError as exc:

                raise RuntimeError(f"Unsafe path in SC2 data archive: {member.filename}") from exc

        zf.extractall(destination)









def _find_payload_root(staging: Path) -> Path:













    candidates = [staging]

    candidates.extend(path for path in staging.rglob("*") if path.is_dir() and len(path.relative_to(staging).parts) <= 3)

    for candidate in candidates:

        if (candidate / "Mods" / "ArchipelagoTriggers.SC2Mod").exists() and (candidate / "Maps" / "ArchipelagoCampaign").exists():

            return candidate

    raise RuntimeError(

        "SC2 data ZIP does not contain the expected Maps/ArchipelagoCampaign "

        "and Mods/ArchipelagoTriggers.SC2Mod trees"

    )



def _clean_metadata(metadata: dict) -> dict:





    for asset in metadata.get("assets", []):

        asset.pop("download_count", None)

    return metadata





def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument("--sc2-root", required=True)

    parser.add_argument("--metadata-json", required=True)

    parser.add_argument("--data-zip", required=True)

    args = parser.parse_args()



    sc2_root = Path(args.sc2_root).resolve()

    metadata_path = Path(args.metadata_json).resolve()

    data_zip = Path(args.data_zip).resolve()

    if not sc2_root.is_dir():

        raise RuntimeError(f"StarCraft II directory does not exist: {sc2_root}")

    if not zipfile.is_zipfile(data_zip):

        raise RuntimeError(f"Downloaded SC2 data is not a valid ZIP: {data_zip}")



    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))

    if str(metadata.get("tag_name", "")).upper() != "API4":

        raise RuntimeError(f"Expected SC2 data tag API4, got {metadata.get('tag_name')!r}")









    with tempfile.TemporaryDirectory(prefix="slay_sc2_data_") as td:

        staging = Path(td)

        _safe_extract(data_zip, staging)

        payload_root = _find_payload_root(staging)

        for top in ("Mods", "Maps"):

            shutil.copytree(payload_root / top, sc2_root / top, dirs_exist_ok=True)



    cleaned = _clean_metadata(metadata)

    (sc2_root / "ArchipelagoSC2Metadata.txt").write_text(repr(cleaned), encoding="utf-8")

    print("Official Archipelago SC2 API4 data installed.")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

