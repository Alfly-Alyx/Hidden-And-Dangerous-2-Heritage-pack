#!/usr/bin/env python3
"""Compare objective catalogues between matching H&D2 solo and coop missions."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT_LINE = re.compile(r'^\s*(\d+)\s+"(.*)"\s*$')


def load_texts(game: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    candidates = (
        Path("Text/English/TEXTY.txt"),
        Path("Text/English/TEXTY_DD.txt"),
        Path("Text/EnglishUS/TEXTY.txt"),
        Path("Text/EnglishUS/TEXTY_DD.txt"),
    )
    for relative in candidates:
        path = game / relative
        if not path.is_file():
            continue
        for line in path.read_text(encoding="cp1252", errors="replace").splitlines():
            match = TEXT_LINE.match(line)
            if match:
                result[int(match.group(1))] = match.group(2)
    return result


def objective_rows(mission: dict[str, object]):
    for item, text_id in enumerate(mission.get("declared_text_ids", []), 1):
        yield {"index": item, "text_id": text_id}


def build(full_audit: dict[str, object], game: Path) -> dict[str, object]:
    missions = {item["mission"]: item for item in full_audit["missions"]}
    texts = load_texts(game)
    pairs = []
    for coop_name in sorted(name for name in missions if name.startswith("co_")):
        solo_name = coop_name[3:]
        if solo_name not in missions:
            continue
        solo = missions[solo_name]
        coop = missions[coop_name]
        if solo.get("catalogue_kind") != "singleplayer" or coop.get("catalogue_kind") != "multiplayer":
            continue
        solo_rows = list(objective_rows(solo))
        coop_rows = list(objective_rows(coop))
        solo_ids = {item["text_id"] for item in solo_rows if item["text_id"] is not None}
        coop_ids = {item["text_id"] for item in coop_rows if item["text_id"] is not None}
        shared = []
        for solo_item in solo_rows:
            text_id = solo_item["text_id"]
            matches = [item for item in coop_rows if item["text_id"] == text_id]
            for coop_item in matches:
                shared.append({
                    "text_id": text_id,
                    "solo_index": solo_item["index"],
                    "coop_index": coop_item["index"],
                    "text": texts.get(text_id, ""),
                })
        def decorated(items, excluded):
            return [{
                "index": item["index"],
                "text_id": item["text_id"],
                "text": texts.get(item["text_id"], "") if item["text_id"] is not None else "",
            } for item in items if item["text_id"] not in excluded]
        missing = decorated(solo_rows, coop_ids)
        coop_only = decorated(coop_rows, solo_ids)
        if not missing and not coop_only and all(
            item["solo_index"] == item["coop_index"] for item in shared
        ):
            continue
        pairs.append({
            "solo": solo_name,
            "coop": coop_name,
            "solo_objectives": len(solo_rows),
            "coop_objectives": len(coop_rows),
            "shared_objectives": shared,
            "solo_only_objectives": missing,
            "coop_only_objectives": coop_only,
        })
    return {
        "game": str(game),
        "pair_count": len(pairs),
        "solo_only_objective_count": sum(
            len(item["solo_only_objectives"]) for item in pairs
        ),
        "coop_only_objective_count": sum(
            len(item["coop_only_objectives"]) for item in pairs
        ),
        "pairs": pairs,
    }


def label(item: dict[str, object]) -> str:
    value = str(item["text_id"])
    if item.get("text"):
        value += " — " + str(item["text"])
    return value


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# Écarts d'objectifs entre solo et coopération",
        "",
        "Comparaison automatique des identifiants de textes officiels entre chaque mission solo et sa variante `Co_`. Une omission ne prouve pas un contenu cassé : elle peut correspondre à un objectif Carnage, une étape propre au départ solo, une fusion de règles ou un scénario coopératif différent.",
        "",
        f"- {report['pair_count']} couples avec au moins un écart ou une renumérotation ;",
        f"- {report['solo_only_objective_count']} entrées solo sans texte équivalent dans le catalogue coopératif ;",
        f"- {report['coop_only_objective_count']} entrées coopératives sans texte équivalent dans le catalogue solo.",
        "",
        "Trois omissions disposent déjà d'une chaîne complète et sont intégrées aux sources stables du paquet : 15504 dans Brest, 15566/15567 dans Burgundy 1 et 15523 dans Libye 2. Le tableau décrit toujours les archives commerciales avant installation.",
        "",
        "| Solo → coop | Objectifs | Textes solo absents en coop | Textes propres à la coop | Renumérotations conservées |",
        "|---|---:|---|---|---|",
    ]
    for pair in report["pairs"]:
        missing = "<br>".join(label(item) for item in pair["solo_only_objectives"]) or "—"
        coop_only = "<br>".join(label(item) for item in pair["coop_only_objectives"]) or "—"
        renumbered = "<br>".join(
            f"{item['text_id']}: {item['solo_index']}→{item['coop_index']}"
            for item in pair["shared_objectives"]
            if item["solo_index"] != item["coop_index"]
        ) or "—"
        lines.append(
            f"| {pair['solo']} → {pair['coop']} | {pair['solo_objectives']}→{pair['coop_objectives']} | {missing} | {coop_only} | {renumbered} |"
        )
    lines += [
        "",
        "## Première classification",
        "",
        "- **restaurations stables** : Brest 15504, Burgundy 1 15566/15567 et Libye 2 15523 possèdent encore texte, acteurs, conditions et validation ;",
        "- **objectifs de survie à reconstruire pour le réseau** : 15505, 15565, 15577, 15587, 15516, 15524 et 15555 ne doivent pas reprendre aveuglément le test solo après mort, réapparition ou déconnexion ;",
        "- **objectifs Carnage ou élimination retirés du catalogue coop** : 15502, 15564, 15583, 15513, 15522, 15544 et 15552 demandent une validation séparée du mode réellement disponible ;",
        "- **scénarios incompatibles ou réécrits** : Libye 1 remplace l'escorte et le départ chronométré par de nouveaux objectifs ; Libye 3 coop est une mission largement différente ; Sicily 2 exige que le pont reste intact et ne peut pas recevoir simultanément l'objectif 15551 qui demande de le détruire ;",
        "- **routes encore à étudier** : la fuite 15573 de Burgundy 2 et le repli 15543 de Sicily 1 ne sont restaurables qu'avec leurs trajets, états de mission et conditions de fin.",
        "",
        "## Règle de décision",
        "",
        "Un objectif ne passe dans la restauration stable que si son texte, ses acteurs, ses conditions, sa validation et son comportement réseau sont encore cohérents. Les objectifs contradictoires ou dépendants des morts/réapparitions restent dans les études expérimentales.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--full-audit", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    full = json.loads(args.full_audit.read_text(encoding="utf-8"))
    report = build(full, args.game)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "pair_count", "solo_only_objective_count", "coop_only_objective_count"
    )}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())