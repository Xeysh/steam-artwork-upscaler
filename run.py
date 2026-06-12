import os
import math
import shutil
import subprocess
import time
import sys

def steam_artwork_getter(input_gif: str, output_gif: str):
    current_directory = os.getcwd()

    if not input_gif.lower().endswith(".gif"):
        input_gif += ".gif"
    if not output_gif.lower().endswith(".gif"):
        output_gif += ".gif"

    input_dir = os.path.join(current_directory, "input")
    output_dir = os.path.join(current_directory, "output")
    exe_path = os.path.join(current_directory, "realesrgan", "realesrgan-ncnn-vulkan.exe")

    if os.path.exists(input_dir):
        shutil.rmtree(input_dir)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("Getting original GIF's FPS...")
    original_fps_process = subprocess.run(
        [
            os.path.join(current_directory, "realesrgan", "ffprobe"),
            "-v", "error",
            "-loglevel", "error",
            "-hide_banner",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_gif
        ],
        capture_output=True,
        text=True,
        check=True
    )

    fps_value = original_fps_process.stdout.strip()
    print(f"Original FPS detected: {fps_value}")

    print("Getting frames from the gif...")
    subprocess.run([
        os.path.join(current_directory, "realesrgan", "ffmpeg"),
        "-loglevel", "error",
        "-hide_banner",
        "-i", input_gif,
        os.path.join(input_dir, "frame_%03d.png"),
        "-y"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # İşlenecek tüm kareleri listele
    all_frames = sorted([f for f in os.listdir(input_dir) if f.startswith('frame_') and f.endswith('.png')])
    total_frames = len(all_frames)

    print(f"\nUpscaling {total_frames} frames with Real-ESRGAN...")

    spinner = ['|', '/', '-', '\\']
    bar_length = 30 # Yükleme çubuğunun karakter uzunluğu

    for idx, filename in enumerate(all_frames, start=1):
        input_path = os.path.join(input_dir, filename)
        output_file = f"enhanced_{filename}"
        output_path = os.path.join(output_dir, output_file)

        cmd = [exe_path, '-i', input_path, '-o', output_path, '-n', 'realesrgan-x4plus-anime']

        # Real-ESRGAN arka planda çalışmaya başlar
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        frame_start_time = time.time()
        spinner_idx = 0

        # Ekran kartı bu kareyi işlediği sürece çubuk canlı olarak dolar
        while process.poll() is None:
            elapsed_time = time.time() - frame_start_time

            # Zamanla ilerleyen organik render yüzdesi
            frame_percent = 100 * (1 - math.exp(-elapsed_time / 4.0))
            if frame_percent > 99:
                frame_percent = 99  # Gerçekten bitene kadar %99'da sınırla

            # CANLI PROGRESS BAR: Çubuk artık toplam kareye göre değil, anlık render yüzdesine göre dolar!
            filled_length = int(bar_length * frame_percent / 100)
            progress_bar = '█' * filled_length + '░' * (bar_length - filled_length)

            print(f"\rFrame {idx}/{total_frames} -> Progress: [{progress_bar}] {frame_percent:.0f}% [{spinner[spinner_idx]}]", end="", flush=True)

            spinner_idx = (spinner_idx + 1) % len(spinner)
            time.sleep(0.1)

        # Kare kesin olarak bittiğinde çubuğu ve yüzdeyi %100'e vuruyoruz
        full_bar = '█' * bar_length
        print(f"\rFrame {idx}/{total_frames} -> Progress: [{full_bar}] 100% [✓]", end="", flush=True)
        process.wait()
        print() # Bir sonraki kareye geçerken alt satıra inmesi için

    print(f"\nAll {total_frames} frames have upscaled successfully.")
    print("Making frames 4K .gif again (Optimized for anime lines)...")

    subprocess.run([
        os.path.join(current_directory, "realesrgan", "ffmpeg"),
        "-loglevel", "error",
        "-hide_banner",
        "-framerate", fps_value,
        "-i", os.path.join(output_dir, "enhanced_frame_%03d.png"),
        "-filter_complex", "scale=3840:-2:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5",
        "-y",
        output_gif
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("4K .gif created successfully! Split step...")

    subprocess.run([sys.executable, "split_gif.py", output_gif])


if __name__ == "__main__":
    input_gif_name = input("Enter input .gif name: ")
    output_gif_name = input("Enter output .gif name (Make it different from the input name to compare): ")

    steam_artwork_getter(input_gif=input_gif_name, output_gif=output_gif_name)
