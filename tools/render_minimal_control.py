"""Render and inspect two matched silent Instagram animation drafts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import av
import imageio_ffmpeg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "launch30"


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True, **kwargs)


def frame_at(path, sec):
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        container.seek(int(sec / stream.time_base), stream=stream, backward=True)
        for frame in container.decode(stream):
            if float(frame.time or 0) >= sec:
                return frame.to_image().convert("RGB")
    raise RuntimeError(f"No frame at {sec}: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--qa-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["MINIMAL_WIDTH"] = str(args.width)
    env["PYTHONIOENCODING"] = "utf-8"
    report = []
    moments = [(1.0, "plan"), (3.9, "push 1"), (5.1, "contact"),
               (8.2, "reserve space"), (11.4, "push 2"), (13.8, "pass")]
    for variant, scene in [("A_no_labels", "MinimalControlA"), ("B_three_labels", "MinimalControlB")]:
        target = OUT / f"minimal_control_{variant}_{args.width}x{int(args.width*16/9)}.mp4"
        if not args.qa_only:
            run(sys.executable, "-m", "manim", "render", "--disable_caching", "--progress_bar", "none",
                "-v", "WARNING", "--media_dir", ROOT/"media/minimal_control", "-o", variant,
                ROOT/"scenes/minimal_control.py", scene, env=env)
            raw = ROOT/"media/minimal_control/videos/minimal_control"/f"{int(args.width*16/9)}p30"/f"{variant}.mp4"
            run(imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
                "-i", raw, "-an", "-c:v", "libx264", "-crf", "19", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", target)
        with av.open(str(target)) as container:
            streams = [{"type": s.type, "codec": s.codec_context.name,
                        "width": s.codec_context.width if s.type == "video" else None,
                        "height": s.codec_context.height if s.type == "video" else None,
                        "fps": float(s.average_rate) if s.type == "video" else None}
                       for s in container.streams]
            duration = container.duration / av.time_base
        assert len(streams) == 1 and streams[0]["type"] == "video", streams
        assert streams[0]["width"] == args.width and 12 <= duration <= 18, (streams, duration)
        cover = OUT / f"{variant}_cover.jpg"
        frame_at(target, 8.2).save(cover, quality=95)
        sheet = Image.new("RGB", (6*270, 510), "#111B29")
        draw = ImageDraw.Draw(sheet)
        for i, (sec, label) in enumerate(moments):
            thumb = frame_at(target, sec).resize((270, 480), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (i*270, 30))
            draw.text((i*270+12, 9), f"{sec:.1f}s | {label}", fill="#EEECE4")
        qa_path = OUT/f"{variant}_contact_sheet.jpg"
        sheet.save(qa_path, quality=93)
        item = {"variant": variant, "path": str(target), "duration_seconds": round(duration, 3),
                "streams": streams, "bytes": target.stat().st_size,
                "cover": str(cover), "contact_sheet": str(qa_path)}
        report.append(item)
        print(json.dumps(item), flush=True)
    notes = {
        "status": "DRAFT — requires the creator's explicit approval before any publication",
        "concept": "The same hand-authored sideways push makes an edge-hugging plan touch a wall; a route with spare clearance passes.",
        "disclaimer": "Schematic visual analogy. Not experimental data, not a controller comparison, and not a guarantee of safety.",
        "post_caption_draft": "Leave room for being wrong. A tiny visual analogy for clearance under uncertainty. Hand-animated schematic; not a controller benchmark.",
        "language": "English",
        "audio": "No audio track: no voiceover, music, or sound effects.",
        "shared_on_screen_text": ["SCHEMATIC"],
        "variant_A": "No explanatory labels or subtitles.",
        "variant_B": {"labels": ["Perfect plan", "Small push", "Leave room"], "explanatory_word_count": 6,
                      "subtitle_status": "Concept labels, not spoken-word subtitles."},
        "controlled_difference": "Only the three concept labels differ. Both versions have identical motion, timing, dimensions, colors, and no audio.",
        "visual_palette": {"background": "#111B29", "rover": "#CDD9D3", "margin": "#A6D3C3", "disturbance": "#DFB09A"},
        "shot_timeline_seconds": [
            {"start": 0, "end": 3.6, "action": "Rover follows a straight plan close to the right wall."},
            {"start": 3.6, "end": 6.8, "action": "Sideways push, wall contact, pause, then reset."},
            {"start": 6.8, "end": 10.4, "action": "A centered plan leaves clearance on both sides."},
            {"start": 10.4, "end": 13.6, "action": "The same sideways displacement, then an unobstructed pass."},
            {"start": 13.6, "end": 16.0, "action": "Quiet hold and exit."}
        ],
        "review_questions": ["Without reading the caption, can you explain what changed between the two passes?",
                             "Do the three labels help, or is A clear enough?",
                             "Does the action feel worth watching again without narration?"],
        "files": report,
    }
    (OUT/"sample_notes.json").write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT/"media_validation.json").write_text(json.dumps({"checks": "passed", "files": report}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
