#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revisore desktop multi-test per esperimenti VLM Bongard.

Per il Test 3 crea un elemento revisionabile distinto per ciascuna delle prime
20 coppie LEFT/RIGHT, conservando posizione e identificativo del JSONL sorgente.

Supporta:
- Test 1: revisione semantica di left_rule e right_rule;
- Test 2: verifica della risposta yes/no rispetto alla regola mostrata;
- Test 3: revisione individuale delle ipotesi generate (Hit@20);
- Test 4: verifica della classificazione del target rispetto ai contesti;
- Test futuri: visualizzazione generica di immagini, output e metadati.

Le annotazioni vengono salvate in JSONL con schema comune e autosalvataggio.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError as exc:
    raise SystemExit("Manca Pillow. Installalo con: pip install pillow") from exc


MODEL_LABELS = {
    "qwen35_2b": "Qwen 3.5 2B",
    "gemma4_e2b_it": "Gemma 4 E2B-it",
}

ASSESSMENT_LABELS = {
    "correct": "Corretta",
    "partial": "Parzialmente corretta",
    "incorrect": "Sbagliata",
    "uncertain": "Non valutabile",
}

KANDY_RULE_LABELS = {
    "easy-0": "Presence of triangles",
    "easy-1": "Presence of squares",
    "easy-2": "Presence of circles",
    "easy-3": "Presence of red objects",
    "easy-4": "Presence of green objects",
    "easy-5": "Presence of blue objects",
    "easy-6": "Presence of cyan objects",
    "easy-7": "Presence of magenta objects",
    "easy-8": "Presence of yellow objects",
    "easy-9": "A red triangle at the extreme right with another object",
    "easy-10": "A red triangle at the extreme right with multiple objects",
    "easy-11": "A red triangle at the extreme right and a circle",
    "easy-12": "A red triangle at the extreme right and a blue object",
    "easy-13": "A triangle and a square of the same color",
    "easy-14": "A palindrome of three objects",
    "easy-15": "Presence of a house",
    "easy-16": "Presence of a car",
    "easy-17": "Presence of a tower",
    "easy-18": "Presence of a cart",
    "easy-19": "Presence of a traffic light",
    "hard-0": "Dyads of the same color",
    "hard-1": "Dyads of the same shape",
    "hard-2": "Triads of the same color",
    "hard-3": "Triads of the same shape",
    "hard-4": "Presence of a house",
    "hard-5": "Presence of a car",
    "hard-6": "Presence of a tower",
    "hard-7": "Presence of a cart",
    "hard-8": "Presence of a traffic light",
    "hard-9": "Each group contains a shared shape",
    "hard-10": "Each group contains a shared color",
    "hard-11": "Each group contains a shared named object",
    "hard-12": "Linear palindromes",
    "hard-13": "Pseudo-palindromes",
    "hard-14": "Pseudo-palindromes with named objects",
    "hard-15": "Odd number: same color; even number: same shape",
    "hard-16": "A logical rule involving traffic light, car, house and tower",
    "hard-17": "A universal logical rule applied to a grid",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(value) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON non valido in {path.name}, riga {line_number}: {exc}") from exc
            if isinstance(value, dict):
                records.append(value)
    return records


def write_jsonl_atomic(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def decode_json(raw: str):
    raw = str(raw or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        if start >= 0:
            try:
                value, _ = json.JSONDecoder().raw_decode(raw[start:])
                return value
            except json.JSONDecodeError:
                return None
    return None


def parse_test3_hypotheses(record: dict) -> list[dict]:
    """Estrae le coppie LEFT/RIGHT dal formato del Test 3.

    Supporta il nuovo parsed_response del notebook, il JSON grezzo e,
    come fallback, le coppie complete recuperabili da un JSON troncato.
    L'ordine originale viene mantenuto perché determina il rank Hit@20.
    """
    parsed = record.get("parsed_response") or record.get("parsed")

    if isinstance(parsed, dict):
        values = parsed.get("hypotheses")
        if isinstance(values, list):
            return [
                {
                    "left_rule": str(h.get("left_rule", h.get("LEFT_RULE", "")) or "").strip(),
                    "right_rule": str(h.get("right_rule", h.get("RIGHT_RULE", "")) or "").strip(),
                }
                for h in values
                if isinstance(h, dict)
            ]

    raw = str(record.get("raw_response") or "")
    decoded = decode_json(raw)

    if isinstance(decoded, dict) and isinstance(decoded.get("hypotheses"), list):
        return [
            {
                "left_rule": str(h.get("left_rule", h.get("LEFT_RULE", "")) or "").strip(),
                "right_rule": str(h.get("right_rule", h.get("RIGHT_RULE", "")) or "").strip(),
            }
            for h in decoded["hypotheses"]
            if isinstance(h, dict)
        ]

    #fallback: recupera le coppie complete anche da JSON troncati
    pair_pattern = re.compile(
        r'"left_rule"\s*:\s*"((?:\\.|[^"\\])*)"\s*,\s*'
        r'"right_rule"\s*:\s*"((?:\\.|[^"\\])*)"',
        flags=re.DOTALL | re.IGNORECASE,
    )

    hypotheses = []
    for left, right in pair_pattern.findall(raw):
        try:
            left_value = json.loads('"' + left + '"')
            right_value = json.loads('"' + right + '"')
        except json.JSONDecodeError:
            left_value, right_value = left, right
        hypotheses.append({
            "left_rule": str(left_value).strip(),
            "right_rule": str(right_value).strip(),
        })

    return hypotheses


def get_parsed(record: dict):
    parsed = record.get("parsed") or record.get("parsed_response")
    if isinstance(parsed, dict):
        return parsed
    decoded = decode_json(record.get("raw_response", ""))
    return decoded if isinstance(decoded, dict) else {}


def invert_kandy_concept(concept: str) -> str:
    concept = str(concept or "").strip()
    for old, new in [
        ("Presenza di ", "Assenza di "),
        ("Presenza ", "Assenza "),
        ("presenza di ", "assenza di "),
        ("presenza ", "assenza "),
        ("Presence of ", "Absence of "),
        ("Presence ", "Absence "),
        ("presence of ", "absence of "),
        ("presence ", "absence "),
    ]:
        if concept.startswith(old):
            return new + concept[len(old):]
    return f"Absence of the following concept: {concept}" if concept else ""


def stable_id(parts: list[str]) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def legacy_test1_id(source: Path, record: dict, side: str) -> str:
    #compatibilita' con gli ID prodotti dalla prima versione di review_test1_app.py
    identity = "|".join([
        str(source.resolve()), str(record.get("model", "")),
        str(record.get("dataset", "")), str(record.get("problem_id", "")), side,
    ])
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()


def discover_project_root(files: list[Path]) -> Path | None:
    for file in files:
        for parent in [file.parent, *file.parents]:
            if (parent / "data" / "processed").is_dir():
                return parent
    return None


class ReferenceLookup:
    """Recupera le regole di riferimento da record e manifest del progetto."""

    def __init__(self, root: Path | None):
        self.root = root
        self.rwr = {}
        self.kandy = dict(KANDY_RULE_LABELS)
        if root is None:
            return
        processed = root / "data" / "processed"
        rwr_manifest = processed / "dataset_2_rwr_plus" / "manifest.csv"
        if rwr_manifest.is_file():
            with rwr_manifest.open("r", encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    pid = str(row.get("profile_id", "")).strip()
                    if pid:
                        self.rwr[pid] = {
                            "left": str(row.get("left_concept", "")).strip(),
                            "right": str(row.get("right_concept", "")).strip(),
                        }
        metadata = processed / "metadata" / "concept_comparison_kandy_rwr.csv"
        if metadata.is_file():
            with metadata.open("r", encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    pid = str(row.get("problem_id", "")).strip()
                    concept = str(row.get("kandy_concept", "")).strip()
                    if pid and concept:
                        self.kandy[pid] = concept

    def pair(self, record: dict) -> tuple[str, str]:
        if record.get("reference_left_rule") or record.get("reference_right_rule"):
            return (
                str(record.get("reference_left_rule", "")).strip(),
                str(record.get("reference_right_rule", "")).strip(),
            )
        reference = record.get("reference") or {}
        if isinstance(reference, dict):
            left = reference.get("left_rule") or reference.get("left_concept")
            right = reference.get("right_rule") or reference.get("right_concept")
            if left or right:
                return str(left or "").strip(), str(right or "").strip()
            concept = str(reference.get("concept", "")).strip()
            if concept:
                positive = norm(reference.get("positive_side", "left"))
                negative = norm(reference.get("negative_side", "right"))
                return (
                    concept if positive == "left" else invert_kandy_concept(concept),
                    concept if positive == "right" else invert_kandy_concept(concept),
                )

        dataset = norm(record.get("dataset"))
        pid = str(record.get("problem_id", "")).strip()
        if dataset in {"kandy", "kandy_bongard", "kandy-bongard"}:
            concept = self.kandy.get(pid, "")
            return concept, invert_kandy_concept(concept)
        if dataset in {"rwr+", "bongard_rwr_plus", "bongard-rwr+", "rwr"}:
            pair = self.rwr.get(pid, {})
            return pair.get("left", ""), pair.get("right", "")
        return "", ""


def resolve_image(raw_path, root: Path | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path)).expanduser()
    if path.is_absolute() and path.is_file():
        return path
    if root is not None:
        candidate = root / path
        if candidate.is_file():
            return candidate.resolve()
    if path.is_file():
        return path.resolve()
    return path


def record_test_name(record: dict) -> str:
    """Identifica il test dando priorita' al campo esplicito del JSONL.

    Le euristiche basate sui campi vengono usate soltanto quando il record
    non dichiara un test riconoscibile. Questo evita che i record del Test 3,
    che contengono reference e image_path, vengano scambiati per Test 1.
    """
    name = norm(record.get("test") or record.get("test_name"))

    #prima scelta: nome esplicito del test scritto dal notebook
    explicit_tests = {
        "test_1_rule_induction": "test_1_rule_induction",
        "test_2_rule_application": "test_2_rule_application",
        "test_3_generation_20": "test_3_generation_20",
        "test_4_context_generalization": "test_4_context_generalization",
    }

    for marker, canonical_name in explicit_tests.items():
        if name == marker or marker in name:
            return canonical_name

    #seconda scelta: struttura del record, solo se manca un nome esplicito
    parsed = get_parsed(record)

    if isinstance(parsed, dict) and isinstance(parsed.get("hypotheses"), list):
        return "test_3_generation_20"

    if record.get("target_path") and record.get("correct_side") is not None:
        return "test_4_context_generalization"

    if record.get("rule_text") and record.get("correct_answer") is not None:
        return "test_2_rule_application"

    if record.get("reference") and record.get("image_path") and not record.get("correct_answer"):
        return "test_1_rule_induction"

    return name or "other"


def model_prediction(record: dict, test_name: str) -> str:
    parsed = get_parsed(record)
    if test_name == "test_2_rule_application":
        return norm(parsed.get("membership") or parsed.get("answer"))
    if test_name == "test_4_context_generalization":
        return norm(parsed.get("classification") or parsed.get("prediction"))
    return ""


class ReviewApp:
    def __init__(self, root: tk.Tk, files: list[Path], project_root: Path | None = None,
                 output_path: Path | None = None):
        self.root = root
        self.files = [p.expanduser().resolve() for p in files if p.is_file()]
        self.project_root = project_root or discover_project_root(self.files)
        self.lookup = ReferenceLookup(self.project_root)
        self.output_path = output_path or self.default_output_path(self.files)
        self.items: list[dict] = []
        self.annotations: dict[str, dict] = {}
        self.index = 0
        self.current_photo = None
        self.note_dirty = False
        self._build_items()
        self._load_annotations()

        self.root.title("Revisione VLM — Tutti i test Bongard")
        self.root.geometry("1420x920")
        self.root.minsize(1100, 740)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self._build_ui()
        self._update_progress()
        self.show_current()

    @staticmethod
    def default_output_path(files: list[Path]) -> Path:
        if not files:
            return Path.cwd() / "review_all_tests.jsonl"
        parents = [str(p.parent.resolve()) for p in files]
        common = Path(os.path.commonpath(parents))
        return common / "review_all_tests.jsonl"

    def _record_images(self, record: dict, test_name: str) -> list[tuple[str, str]]:
        images = []
        inputs = record.get("input_images") or []
        if isinstance(inputs, str):
            inputs = [inputs]
        if not isinstance(inputs, list):
            inputs = []

        if test_name == "test_1_rule_induction":
            path = record.get("image_path") or record.get("board_path") or (inputs[0] if inputs else None)
            if path:
                images.append(("Matrice Bongard", str(path)))
        elif test_name == "test_2_rule_application":
            path = record.get("image_path") or (inputs[0] if inputs else None)
            if path:
                images.append(("Immagine da classificare", str(path)))
        elif test_name == "test_3_generation_20":
            path = record.get("board_path") or (inputs[0] if inputs else None)
            if path:
                images.append(("Matrice Bongard", str(path)))
        elif test_name == "test_4_context_generalization":
            #l'ordine prodotto dal notebook e': contesto sinistro, contesto destro, target
            labels = ["Contesto LEFT", "Contesto RIGHT", "Target"]
            paths = list(inputs[:3])
            target = record.get("target_path")
            if target and len(paths) < 3:
                paths.append(target)
            for index, path in enumerate(paths):
                images.append((labels[index] if index < len(labels) else f"Input {index + 1}", str(path)))
        else:
            paths = list(inputs[:4])
            if not paths:
                path = record.get("image_path") or record.get("target_path") or record.get("board_path")
                if path:
                    paths = [path]
            images.extend((f"Input {i + 1}", str(path)) for i, path in enumerate(paths))
        return images

    def _build_items(self):
        for source in self.files:
            records = load_jsonl(source)
            for record_index, record in enumerate(records):
                test_name = record_test_name(record)
                model = str(record.get("model", "unknown"))
                model_label = record.get("model_label") or MODEL_LABELS.get(model, model)
                dataset = str(record.get("dataset", ""))
                problem_id = str(record.get("problem_id", ""))
                task_id = str(record.get("task_id") or f"row-{record_index + 1}")
                images = self._record_images(record, test_name)

                if test_name == "test_1_rule_induction":
                    left_ref, right_ref = self.lookup.pair(record)
                    parsed = get_parsed(record)
                    raw = str(record.get("raw_response", ""))
                    for side, reference in [("left", left_ref), ("right", right_ref)]:
                        model_rule = str(parsed.get(f"{side}_rule", "")).strip()
                        if not model_rule:
                            match = re.search(rf"(?im)^\s*{side.upper()}_RULE\s*:\s*(.*?)\s*$", raw)
                            model_rule = match.group(1).strip() if match else ""
                        item_id = legacy_test1_id(source, record, side)
                        self.items.append({
                            "review_id": item_id, "source_file": str(source), "record": record,
                            "test": test_name, "item_type": "semantic_rule", "item_key": side,
                            "side": side, "images": images,
                            "reference": reference, "model_output": model_rule,
                            "prediction": model_rule, "gold": reference,
                            "display_title": f"Regola {side.upper()}",
                        })
                    continue

                if test_name == "test_2_rule_application":
                    parsed = get_parsed(record)
                    prediction = model_prediction(record, test_name)
                    self._add_item(source, record, test_name, task_id, "application", "membership",
                                   images, str(record.get("rule_text", "")),
                                   prediction or str(record.get("raw_response", "")),
                                   prediction, norm(record.get("correct_answer")),
                                   "Applicazione della regola")
                    continue

                if test_name == "test_3_generation_20":
                    left_ref, right_ref = self.lookup.pair(record)
                    hypotheses = parse_test3_hypotheses(record)

                    #il notebook registra anche il numero di coppie estratte
                    reported_count = record.get("num_hypotheses")
                    try:
                        reported_count = int(reported_count)
                    except (TypeError, ValueError):
                        reported_count = len(hypotheses)

                    #usiamo il numero effettivo per mantenere il rank originale
                    generated_count = max(reported_count, len(hypotheses))

                    reference = (
                        f"LEFT_RULE: {left_ref or '[riferimento LEFT non disponibile]'}\n"
                        f"RIGHT_RULE: {right_ref or '[riferimento RIGHT non disponibile]'}"
                    )

                    if not hypotheses:
                        raw = str(record.get("raw_response", ""))
                        self._add_item(
                            source, record, test_name, task_id,
                            "generation_output", "unparsed",
                            images, reference, raw, "", "",
                            "Output generato non interpretabile"
                        )
                    else:
                        #Hit@20 considera esclusivamente le prime 20 posizioni
                        for rank, hypothesis in enumerate(hypotheses[:20], start=1):
                            left_rule = str(hypothesis.get("left_rule", "")).strip()
                            right_rule = str(hypothesis.get("right_rule", "")).strip()

                            model_output = (
                                f"LEFT_RULE: {left_rule or '[regola LEFT mancante]'}\n"
                                f"RIGHT_RULE: {right_rule or '[regola RIGHT mancante]'}"
                            )

                            self._add_item(
                                source, record, test_name, task_id,
                                "generation_hypothesis", str(rank),
                                images, reference, model_output,
                                model_output, reference,
                                f"Ipotesi {rank}/20 (estratte: {generated_count})",
                                rank=rank, generated_count=generated_count
                            )
                    continue

                if test_name == "test_4_context_generalization":
                    prediction = model_prediction(record, test_name)
                    gold = norm(record.get("correct_side"))
                    context = (
                        f"Condizione: {record.get('experiment', '')}\n"
                        f"Esempi di contesto LEFT: {record.get('kandy_count_left', '')} KANDY, "
                        f"{record.get('rwr_count_left', '')} RWR+\n"
                        f"Esempi di contesto RIGHT: {record.get('kandy_count_right', '')} KANDY, "
                        f"{record.get('rwr_count_right', '')} RWR+"
                    )
                    self._add_item(source, record, test_name, task_id, "generalization", "target",
                                   images, context, prediction or str(record.get("raw_response", "")),
                                   prediction, gold, "Classificazione del target")
                    continue

                #adattatore generico: rende revisionabili anche i test futuri
                raw = str(record.get("raw_response", ""))
                reference = record.get("reference") or record.get("ground_truth") or record.get("rule_text") or ""
                parsed = get_parsed(record)
                model_output = json.dumps(parsed, ensure_ascii=False, indent=2) if parsed else raw
                self._add_item(source, record, test_name, task_id, "generic", "record",
                               images, str(reference), model_output, model_output,
                               str(record.get("correct_answer", "")), "Revisione generica")

    def _add_item(self, source, record, test_name, task_id, item_type, item_key,
                  images, reference, model_output, prediction, gold, title,
                  rank=None, generated_count=None):
        model = str(record.get("model", "unknown"))
        dataset = str(record.get("dataset", ""))
        problem_id = str(record.get("problem_id", ""))
        item_id = stable_id([
            str(source.resolve()), model, test_name, task_id, item_type, str(item_key)
        ])
        self.items.append({
            "review_id": item_id, "source_file": str(source), "record": record,
            "test": test_name, "item_type": item_type, "item_key": str(item_key),
            "rank": rank, "generated_count": generated_count,
            "side": "", "images": images,
            "reference": str(reference or ""), "model_output": str(model_output or ""),
            "prediction": str(prediction or ""), "gold": str(gold or ""),
            "display_title": title,
        })

    def _load_annotations(self):
        candidates = {self.output_path}
        #migra automaticamente le revisioni del vecchio revisore Test 1
        for source in self.files:
            legacy = source.parent / "review_semantica_test1.jsonl"
            if legacy.is_file():
                candidates.add(legacy)
        for path in candidates:
            if not path.is_file():
                continue
            try:
                for row in load_jsonl(path):
                    if row.get("review_id"):
                        self.annotations[row["review_id"]] = row
            except Exception as exc:
                messagebox.showwarning("Revisione non caricata", f"{path}:\n{exc}")

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("TkDefaultFont", 16, "bold"))
        style.configure("Section.TLabel", font=("TkDefaultFont", 11, "bold"))
        style.configure("Action.TButton", font=("TkDefaultFont", 10, "bold"), padding=8)

        top = ttk.Frame(self.root, padding=(14, 10))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Revisione VLM — Test 1, 2, 3, 4 e successivi", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(top, text="Carica altri JSONL…", command=self.add_files).grid(row=0, column=1, padx=4)
        ttk.Button(top, text="Cartella progetto…", command=self.choose_root).grid(row=0, column=2, padx=4)
        self.source_label = ttk.Label(top, text="", foreground="#555")
        self.source_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

        progress = ttk.Frame(self.root, padding=(14, 0, 14, 10))
        progress.grid(row=1, column=0, sticky="ew")
        progress.columnconfigure(0, weight=1)
        self.progress_label = ttk.Label(progress, text="")
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.stats_label = ttk.Label(progress, text="", foreground="#555")
        self.stats_label.grid(row=0, column=1, sticky="e")
        self.progress_bar = ttk.Progressbar(progress, mode="determinate")
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        main = ttk.Frame(self.root, padding=(14, 0, 14, 10))
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=6, uniform="main")
        main.columnconfigure(1, weight=5, uniform="main")
        main.rowconfigure(0, weight=1)

        image_frame = ttk.LabelFrame(main, text="Immagini di input", padding=8)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        self.image_label = ttk.Label(image_frame, text="", anchor="center", justify="center")
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_path_label = ttk.Label(image_frame, text="", foreground="#666", wraplength=700)
        self.image_path_label.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        detail = ttk.Frame(main)
        detail.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(2, weight=1)
        self.problem_label = ttk.Label(detail, text="", style="Section.TLabel")
        self.problem_label.grid(row=0, column=0, sticky="w", pady=(0, 7))
        self.item_label = ttk.Label(detail, text="", style="Section.TLabel")
        self.item_label.grid(row=1, column=0, sticky="w", pady=(0, 7))

        text_frame = ttk.LabelFrame(detail, text="Riferimento e risposta del modello", padding=7)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.details = tk.Text(text_frame, wrap="word", font=("TkDefaultFont", 11), height=18)
        self.details.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(text_frame, command=self.details.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.details.configure(yscrollcommand=scroll.set, state="disabled")

        self.status_label = ttk.Label(detail, text="", foreground="#666", wraplength=580)
        self.status_label.grid(row=3, column=0, sticky="w", pady=(0, 8))

        notes_frame = ttk.LabelFrame(detail, text="Note (facoltative)", padding=7)
        notes_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        notes_frame.columnconfigure(0, weight=1)
        self.notes = tk.Text(notes_frame, height=3, wrap="word", font=("TkDefaultFont", 10))
        self.notes.grid(row=0, column=0, sticky="ew")
        self.notes.bind("<FocusOut>", self._save_note_on_focus_out)
        self.notes.bind("<KeyRelease>", self._mark_note_dirty)

        actions = ttk.LabelFrame(detail, text="Valutazione", padding=7)
        actions.grid(row=5, column=0, sticky="ew")
        for col in range(3):
            actions.columnconfigure(col, weight=1)
        self.button_left = ttk.Button(actions, style="Action.TButton", command=lambda: self.rate("incorrect", "left"))
        self.button_mid = ttk.Button(actions, style="Action.TButton", command=lambda: self.rate("partial", "up"))
        self.button_right = ttk.Button(actions, style="Action.TButton", command=lambda: self.rate("correct", "right"))
        self.button_left.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        self.button_mid.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        self.button_right.grid(row=0, column=2, sticky="ew", padx=3, pady=3)

        footer = ttk.Frame(self.root, padding=(14, 0, 14, 12))
        footer.grid(row=3, column=0, sticky="ew")
        ttk.Button(footer, text="← Precedente", command=self.previous_item).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(footer, text="Salta", command=self.next_item).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(footer, text="Annulla valutazione", command=self.clear_rating).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(footer, text="Prossimo non valutato", command=self.next_unreviewed).grid(row=0, column=3, padx=(0, 8))
        self.save_label = ttk.Label(footer, text=f"Salvataggio: {self.output_path}", foreground="#555")
        self.save_label.grid(row=0, column=4, sticky="e")

        self.root.bind_all("<Left>", lambda event: self._key_rate(event, "incorrect", "left"))
        self.root.bind_all("<Right>", lambda event: self._key_rate(event, "correct", "right"))
        self.root.bind_all("<Up>", lambda event: self._key_rate(event, "partial", "up"))
        self.root.bind_all("<Down>", lambda event: self._key_rate(event, "uncertain", "down"))
        self.root.bind_all("<Escape>", lambda event: self.next_item())

        self.source_label.configure(
            text=f"{len(self.files)} file · {len(self.items)} elementi da revisionare · output: {self.output_path}"
        )

    def _render_images(self, item: dict):
        entries = item.get("images", [])
        self.current_photo = None
        if not entries:
            self.image_label.configure(image="", text="Nessuna immagine associata a questo record.")
            self.image_path_label.configure(text="")
            return

        cols = 1 if len(entries) == 1 else 2
        tile_w, tile_h, header = 350, 275, 28
        rows = (len(entries) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * tile_w, rows * (tile_h + header)), "white")
        draw = ImageDraw.Draw(canvas)
        shown_paths = []

        for index, (label, raw_path) in enumerate(entries):
            row, col = divmod(index, cols)
            x, y = col * tile_w, row * (tile_h + header)
            draw.rectangle((x, y, x + tile_w, y + header), fill=(235, 238, 242))
            draw.text((x + 8, y + 7), label[:48], fill=(20, 20, 20))
            path = resolve_image(raw_path, self.project_root)
            shown_paths.append(f"{label}: {path}")
            if path is None or not path.is_file():
                draw.text((x + 12, y + header + 20), f"Immagine non trovata:\n{path}", fill=(150, 30, 30))
                continue
            try:
                with Image.open(path) as source:
                    image = source.convert("RGB")
                    image.thumbnail((tile_w - 16, tile_h - 16), Image.Resampling.LANCZOS)
                ix = x + (tile_w - image.width) // 2
                iy = y + header + (tile_h - image.height) // 2
                canvas.paste(image, (ix, iy))
            except Exception as exc:
                draw.text((x + 12, y + header + 20), f"Errore apertura immagine: {exc}", fill=(150, 30, 30))

        canvas.thumbnail((760, 650), Image.Resampling.LANCZOS)
        self.current_photo = ImageTk.PhotoImage(canvas)
        self.image_label.configure(image=self.current_photo, text="")
        self.image_path_label.configure(text="\n".join(shown_paths))

    def _current_item(self):
        if not self.items:
            return None
        self.index = max(0, min(self.index, len(self.items) - 1))
        return self.items[self.index]

    def show_current(self):
        item = self._current_item()
        if item is None:
            self.problem_label.configure(text="Nessun elemento caricato")
            return
        self._save_note(silent=True)
        record = item["record"]
        model = str(record.get("model", "unknown"))
        model_label = record.get("model_label") or MODEL_LABELS.get(model, model)
        dataset = str(record.get("dataset", ""))
        pid = str(record.get("problem_id", ""))
        test_label = item["test"].replace("_", " ").upper()

        self.problem_label.configure(text=f"{test_label} · {dataset} · {pid} · {model_label}")
        self.item_label.configure(text=item["display_title"])

        if item["test"] == "test_1_rule_induction":
            content = (
                f"Lato valutato: {item['side'].upper()}\n\n"
                f"REGOLA DI RIFERIMENTO\n{item['reference'] or '[non disponibile]'}\n\n"
                f"REGOLA DEL MODELLO\n{item['model_output'] or '[nessuna regola parsabile]'}"
            )
            semantic = True
        elif item["test"] == "test_2_rule_application":
            content = (
                f"REGOLA DATA AL MODELLO\n{item['reference'] or '[non disponibile]'}\n\n"
                f"RISPOSTA DEL MODELLO\n{item['model_output'] or '[nessuna risposta parsabile]'}\n\n"
                f"RISPOSTA CORRETTA\n{item['gold'] or '[non disponibile]'}\n\n"
                f"La valutazione indica se la risposta del modello e' corretta rispetto al gold."
            )
            semantic = False
        elif item["test"] == "test_3_generation_20":
            content = (
                f"REGOLE DI RIFERIMENTO\n{item['reference'] or '[non disponibili: controlla manifest/root progetto]'}\n\n"
                f"COPPIA DI REGOLE GENERATA\n{item['model_output']}\n\n"
                f"Posizione nell'elenco: {item.get('rank') or 'non disponibile'} / 20\n"
                f"Ipotesi estratte dal modello: {item.get('generated_count') or 'non disponibile'}\n\n"
                "CRITERIO DI REVISIONE\n"
                "Valuta la coppia nel suo insieme: Corretta se entrambe le regole "
                "esprimono la distinzione attesa; Parziale se la distinzione è "
                "colta solo in parte; Sbagliata se la coppia non descrive il "
                "concetto che separa i due gruppi. "
                "Hit@20 sarà positivo se almeno una delle prime 20 coppie è "
                "giudicata Corretta."
            )
            semantic = True
        elif item["test"] == "test_4_context_generalization":
            content = (
                f"CONDIZIONE / CONTESTO\n{item['reference'] or '[non disponibile]'}\n\n"
                f"PREDIZIONE DEL MODELLO\n{item['model_output'] or '[nessuna risposta parsabile]'}\n\n"
                f"LATO CORRETTO DEL TARGET\n{item['gold'] or '[non disponibile]'}"
            )
            semantic = False
        else:
            content = (
                f"RIFERIMENTO\n{item['reference'] or '[non disponibile]'}\n\n"
                f"OUTPUT DEL MODELLO\n{item['model_output'] or '[vuoto]'}"
            )
            semantic = True

        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", content)
        self.details.configure(state="disabled")

        status = record.get("status", "non specificato")
        finish = record.get("finish_reason", "")
        self.status_label.configure(text=f"Status: {status}" + (f" · finish: {finish}" if finish else ""))

        annotation = self.annotations.get(item["review_id"], {})
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", annotation.get("notes", ""))
        self.note_dirty = False
        assessment = annotation.get("assessment")
        self.save_label.configure(
            text=f"Valutazione salvata: {ASSESSMENT_LABELS.get(assessment, assessment)}"
            if assessment else f"Output: {self.output_path.name}"
        )

        if semantic:
            self.button_left.configure(text="← Sbagliata / Non coincide", command=lambda: self.rate("incorrect", "left"))
            self.button_mid.configure(text="↑ Parziale", command=lambda: self.rate("partial", "up"))
            self.button_right.configure(text="→ Corretta / Coincide", command=lambda: self.rate("correct", "right"))
        else:
            self.button_left.configure(text="← Risposta sbagliata", command=lambda: self.rate("incorrect", "left"))
            self.button_mid.configure(text="↓ Non valutabile", command=lambda: self.rate("uncertain", "down"))
            self.button_right.configure(text="→ Risposta corretta", command=lambda: self.rate("correct", "right"))

        self._render_images(item)
        self._update_progress()

    def _base_annotation(self, item: dict) -> dict:
        record = item["record"]
        return {
            "review_id": item["review_id"],
            "source_jsonl": item["source_file"],
            "model": record.get("model"),
            "model_label": record.get("model_label") or MODEL_LABELS.get(record.get("model"), record.get("model")),
            "test": item["test"],
            "prompt_version": record.get("prompt_version"),
            "dataset": record.get("dataset"),
            "problem_id": record.get("problem_id"),
            "task_id": record.get("task_id"),
            "item_type": item["item_type"],
            "item_key": item["item_key"],
            "side": item.get("side", ""),
            "rank": item.get("rank"),
            "generated_count": item.get("generated_count"),
            "reference": item.get("reference", ""),
            "model_output": item.get("model_output", ""),
            "prediction": item.get("prediction", ""),
            "gold": item.get("gold", ""),
            "status": record.get("status"),
        }

    def _write_annotations(self):
        rows = sorted(self.annotations.values(), key=lambda x: (
            str(x.get("source_jsonl")), str(x.get("test")), str(x.get("problem_id")),
            str(x.get("item_key")),
        ))
        write_jsonl_atomic(self.output_path, rows)

    def _save_note(self, silent=False):
        if not self.items or not self.note_dirty:
            return
        item = self._current_item()
        if item is None:
            return
        existing = self.annotations.get(item["review_id"], {})
        annotation = {**self._base_annotation(item), **existing}
        annotation["notes"] = self.notes.get("1.0", "end-1c").strip()
        annotation["updated_at"] = now_iso()
        self.annotations[item["review_id"]] = annotation
        try:
            self._write_annotations()
            self.note_dirty = False
            if not silent:
                self.save_label.configure(text="Nota salvata")
        except Exception as exc:
            messagebox.showerror("Errore salvataggio", str(exc))

    def _mark_note_dirty(self, _event=None):
        self.note_dirty = True

    def _save_note_on_focus_out(self, _event=None):
        self._save_note(silent=True)

    def rate(self, assessment: str, gesture: str):
        item = self._current_item()
        if item is None:
            return
        existing = self.annotations.get(item["review_id"], {})
        annotation = {**self._base_annotation(item), **existing}
        annotation.update({
            "assessment": assessment,
            "assessment_label": ASSESSMENT_LABELS[assessment],
            "gesture": gesture,
            "notes": self.notes.get("1.0", "end-1c").strip(),
            "updated_at": now_iso(),
        })
        self.annotations[item["review_id"]] = annotation
        try:
            self._write_annotations()
        except Exception as exc:
            messagebox.showerror("Errore salvataggio", str(exc))
            return
        self.note_dirty = False
        self.next_unreviewed()

    def clear_rating(self):
        item = self._current_item()
        if item is None:
            return
        annotation = self.annotations.get(item["review_id"])
        if annotation:
            annotation.pop("assessment", None)
            annotation.pop("assessment_label", None)
            annotation.pop("gesture", None)
            annotation["updated_at"] = now_iso()
            self.annotations[item["review_id"]] = annotation
            self._write_annotations()
        self.show_current()

    def _update_progress(self):
        total = len(self.items)
        reviewed = sum(
            self.annotations.get(item["review_id"], {}).get("assessment") in ASSESSMENT_LABELS
            for item in self.items
        )
        counts = {key: 0 for key in ASSESSMENT_LABELS}
        for item in self.items:
            assessment = self.annotations.get(item["review_id"], {}).get("assessment")
            if assessment in counts:
                counts[assessment] += 1
        test_counts = {}
        for item in self.items:
            test_counts[item["test"]] = test_counts.get(item["test"], 0) + 1
        current = self.index + 1 if total else 0
        self.progress_label.configure(text=f"Elemento {current}/{total} · revisionati {reviewed}/{total}")
        self.stats_label.configure(text=(
            f"Corrette: {counts['correct']} · Parziali: {counts['partial']} · "
            f"Sbagliate: {counts['incorrect']} · Non valutabili: {counts['uncertain']}"
        ))
        self.progress_bar.configure(maximum=max(total, 1), value=reviewed)

    def next_unreviewed(self):
        if not self.items:
            return
        self._save_note(silent=True)
        for offset in range(1, len(self.items) + 1):
            candidate = (self.index + offset) % len(self.items)
            item = self.items[candidate]
            assessment = self.annotations.get(item["review_id"], {}).get("assessment")
            if assessment not in ASSESSMENT_LABELS:
                self.index = candidate
                self.show_current()
                return
        self._update_progress()
        self.save_label.configure(text="Tutte le valutazioni sono state completate")

    def next_item(self):
        if not self.items:
            return
        self._save_note(silent=True)
        self.index = min(self.index + 1, len(self.items) - 1)
        self.show_current()

    def previous_item(self):
        if not self.items:
            return
        self._save_note(silent=True)
        self.index = max(self.index - 1, 0)
        self.show_current()

    def _key_rate(self, event, assessment, gesture):
        if isinstance(self.root.focus_get(), tk.Text):
            return None
        self.rate(assessment, gesture)
        return "break"

    def add_files(self):
        paths = filedialog.askopenfilenames(
            parent=self.root, title="Aggiungi JSONL di qualsiasi test",
            filetypes=[("File JSONL", "*.jsonl"), ("Tutti i file", "*.*")],
        )
        if not paths:
            return
        new_paths = [Path(p).resolve() for p in paths if Path(p).resolve() not in self.files]
        if not new_paths:
            return
        self.files.extend(new_paths)
        if self.project_root is None:
            self.project_root = discover_project_root(new_paths)
            self.lookup = ReferenceLookup(self.project_root)
        old_count = len(self.items)
        self._build_items_from_files(new_paths)
        self._load_annotation_files(new_paths)
        self.source_label.configure(text=f"{len(self.files)} file · {len(self.items)} elementi da revisionare · output: {self.output_path}")
        if len(self.items) > old_count:
            self.index = old_count
            self.show_current()

    def _build_items_from_files(self, files):
        #riusa il costruttore principale senza perdere le annotazioni gia' caricate
        previous_files = self.files
        previous_items = self.items
        self.files = files
        self.items = []
        self._build_items()
        added = self.items
        self.items = previous_items + added
        self.files = previous_files

    def _load_annotation_files(self, files):
        candidates = {self.output_path}
        for source in files:
            legacy = source.parent / "review_semantica_test1.jsonl"
            if legacy.is_file():
                candidates.add(legacy)
        for path in candidates:
            if path.is_file():
                for row in load_jsonl(path):
                    if row.get("review_id"):
                        self.annotations[row["review_id"]] = row

    def choose_root(self):
        selected = filedialog.askdirectory(parent=self.root, title="Seleziona la root del progetto (contiene data/processed)")
        if not selected:
            return
        self.project_root = Path(selected).resolve()
        self.lookup = ReferenceLookup(self.project_root)
        current_id = self.items[self.index]["review_id"] if self.items else None
        self.items = []
        self._build_items()
        if current_id:
            self.index = next((i for i, item in enumerate(self.items) if item["review_id"] == current_id), 0)
        self.show_current()


def main():
    parser = argparse.ArgumentParser(description="Revisore desktop per tutti i test VLM Bongard")
    parser.add_argument("files", nargs="*", help="Uno o piu' JSONL dei Test 1, 2, 3, 4 o successivi")
    parser.add_argument("--root", help="Root del progetto che contiene data/processed")
    parser.add_argument("--output", help="Percorso del JSONL delle annotazioni")
    args = parser.parse_args()

    files = [Path(value).expanduser().resolve() for value in args.files]
    if not files:
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askopenfilenames(
            title="Seleziona uno o più JSONL di qualsiasi test",
            filetypes=[("File JSONL", "*.jsonl"), ("Tutti i file", "*.*")],
        )
        root.destroy()
        files = [Path(value).resolve() for value in selected]
    if not files:
        raise SystemExit("Nessun file JSONL selezionato.")

    project_root = Path(args.root).expanduser().resolve() if args.root else discover_project_root(files)
    output_path = Path(args.output).expanduser().resolve() if args.output else None

    root = tk.Tk()
    ReviewApp(root, files=files, project_root=project_root, output_path=output_path)
    root.mainloop()


if __name__ == "__main__":
    main()
