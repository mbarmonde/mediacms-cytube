# dev-v0.2.0 - GPU encoding support via h264_nvenc (ENCODING_BACKEND=gpu in .env)

#####
# CHANGELOG
# v0.2.0 - GPU ENCODING SUPPORT
#   - produce_ffmpeg_commands(): reads ENCODING_BACKEND from settings
#     - 'gpu' + h264 codec: encoder = h264_nvenc, passes use_gpu=True to get_base_ffmpeg_command()
#     - 'cpu' or any other codec: encoder unchanged, passes use_gpu=False (zero behavioral change)
#   - get_base_ffmpeg_command(): added use_gpu parameter (default False)
#     - CPU path (use_gpu=False): 100% identical to v0.1.0 - all flags preserved exactly
#     - GPU path (use_gpu=True, h264 only):
#       - -crf replaced with -cq (NVENC constant quality, same numeric value)
#       - -preset uses ENCODING_GPU_PRESET from settings (p1-p7 scale)
#       - -x264-params removed (fatal error with h264_nvenc, not supported)
#       - -maxrate, -bufsize, -force_key_frames, -profile:v, -level: all preserved
#       - enc_type forced to 'crf' for GPU (NVENC two-pass not compatible with passlogfile)
#   - vp9 and h265 codecs: always use CPU encoders, completely unaffected
#   - All other functions: unchanged from v0.1.0
# v0.1.0 - Encoding settings now read from Django settings (configured via .env)
#   - Added get_video_crfs() to dynamically load CRF values from settings
#   - VIDEO_CRFS now reads from settings.FFMPEG_CRF_H264, FFMPEG_CRF_H265, FFMPEG_CRF_VP9
#   - Fixes bug where FFMPEG_CRF in local_settings.py was ignored (hardcoded values)
#   - Falls back to sensible defaults if settings not available (backward compatible)
#####

# Kudos to Werner Robitza, AVEQ GmbH, for helping with ffmpeg related content

import hashlib
import json
import logging
import os
import random
import shutil
import subprocess
import tempfile
from fractions import Fraction

import filetype
from django.conf import settings

CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

logger = logging.getLogger(__name__)


CRF_ENCODING_NUM_SECONDS = 2  # 0 * 60 # videos with greater duration will get
# CRF encoding and not two-pass
# Encoding individual chunks may yield quality variations if you use a
# too low bitrate, so if you go for the chunk-based variant
# you should use CRF encoding.

MAX_RATE_MULTIPLIER = 1.5
MIN_RATE_MULTIPLIER = 0.5

BUF_SIZE_MULTIPLIER = 1.5

# in seconds, anything between 2 and 6 makes sense
KEYFRAME_DISTANCE = 4
KEYFRAME_DISTANCE_MIN = 2

# VP9_SPEED = 1  # between 0 and 4, lower is slower
VP9_SPEED = 2


# ============================================
# DYNAMIC CRF LOADING FROM SETTINGS (.ENV)
# ============================================
# Fixes bug where FFMPEG_CRF was hardcoded and ignored settings
# Now reads from settings.FFMPEG_CRF_H264, settings.FFMPEG_CRF_H265, settings.FFMPEG_CRF_VP9
# These are configured via .env file and loaded in local_settings.py

def get_video_crfs():
    """Get CRF values from Django settings or use defaults

    Returns:
        dict: CRF values for different codecs

    CRF (Constant Rate Factor) controls quality:
    - Lower CRF = Better quality, larger files
    - Higher CRF = Lower quality, smaller files

    Default values:
    - H.264: 23 (FFmpeg default)
    - H.265: 28 (equivalent to H.264 CRF 23)
    - VP9: 32 (equivalent to H.264 CRF 23)
    """
    try:
        from django.conf import settings
        crfs = {
            "h264_baseline": getattr(settings, 'FFMPEG_CRF_H264', 23),
            "h264": getattr(settings, 'FFMPEG_CRF_H264', 23),
            "h265": getattr(settings, 'FFMPEG_CRF_H265', 28),
            "vp9": getattr(settings, 'FFMPEG_CRF_VP9', 32),
        }
        logger.info(f"📊 CRF values loaded from settings: H.264={crfs['h264']}, H.265={crfs['h265']}, VP9={crfs['vp9']}")
        return crfs
    except (ImportError, AttributeError) as e:
        logger.warning(f"⚠️  Could not load CRF from settings: {e}. Using defaults.")
        return {
            "h264_baseline": 23,
            "h264": 23,
            "h265": 28,
            "vp9": 32,
        }


# VIDEO_CRFS now loaded dynamically from settings (configured via .env)
# Previously hardcoded, now respects FFMPEG_CRF_H264, FFMPEG_CRF_H265, FFMPEG_CRF_VP9
VIDEO_CRFS = get_video_crfs()

# video rates for 25 or 60 fps input, for different codecs, in kbps
VIDEO_BITRATES = {
    "h264": {
        25: {
            144: 150,
            240: 300,
            360: 500,
            480: 1000,
            720: 2500,
            1080: 4500,
            1440: 9000,
            2160: 18000,
        },
        60: {720: 3500, 1080: 7500, 1440: 18000, 2160: 40000},
    },
    "h265": {
        25: {
            144: 75,
            240: 150,
            360: 275,
            480: 500,
            720: 1024,
            1080: 1800,
            1440: 4500,
            2160: 10000,
        },
        60: {720: 1800, 1080: 3000, 1440: 8000, 2160: 18000},
    },
    "vp9": {
        25: {
            144: 75,
            240: 150,
            360: 275,
            480: 500,
            720: 1024,
            1080: 1800,
            1440: 4500,
            2160: 10000,
        },
        60: {720: 1800, 1080: 3000, 1440: 8000, 2160: 18000},
    },
}


AUDIO_ENCODERS = {"h264": "aac", "h265": "aac", "vp9": "libopus"}

AUDIO_BITRATES = {"h264": 128, "h265": 128, "vp9": 96}

EXTENSIONS = {"h264": "mp4", "h265": "mp4", "vp9": "webm"}

VIDEO_PROFILES = {"h264": "main", "h265": "main"}


def get_portal_workflow():
    return settings.PORTAL_WORKFLOW


def get_default_state(user=None):
    state = "private"
    if settings.PORTAL_WORKFLOW == "public":
        state = "public"
    if settings.PORTAL_WORKFLOW == "unlisted":
        state = "unlisted"
    if settings.PORTAL_WORKFLOW == "private_verified":
        if user and user.advancedUser:
            state = "unlisted"
    return state


def get_file_name(filename):
    return filename.split("/")[-1]


def get_file_type(filename):
    if not os.path.exists(filename):
        return None
    file_type = None
    kind = filetype.guess(filename)
    if kind is not None:
        if kind.mime.startswith("video"):
            file_type = "video"
        elif kind.mime.startswith("image"):
            file_type = "image"
        elif kind.mime.startswith("audio"):
            file_type = "audio"
        elif "pdf" in kind.mime:
            file_type = "pdf"
    else:
        pass
    return file_type


def rm_file(filename):
    if os.path.isfile(filename):
        try:
            os.remove(filename)
            return True
        except OSError:
            pass
    return False


def rm_files(filenames):
    if isinstance(filenames, list):
        for filename in filenames:
            rm_file(filename)
    return True


def rm_dir(directory):
    if os.path.isdir(directory):
        if directory.startswith(settings.BASE_DIR):
            try:
                shutil.rmtree(directory)
                return True
            except (FileNotFoundError, PermissionError):
                pass
    return False


def url_from_path(filename):
    return f"{settings.MEDIA_URL}{filename.replace(settings.MEDIA_ROOT, '')}"


def create_temp_file(suffix=None, dir=settings.TEMP_DIRECTORY):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=dir)
    return tf.name


def create_temp_dir(suffix=None, dir=settings.TEMP_DIRECTORY):
    td = tempfile.mkdtemp(dir=dir)
    return td


def produce_friendly_token(token_len=settings.FRIENDLY_TOKEN_LEN):
    token = ""
    while len(token) != token_len:
        token += CHARS[random.randint(0, len(CHARS) - 1)]
    return token


def clean_friendly_token(token):
    for char in token:
        if char not in CHARS:
            token.replace(char, "")
    return token


def mask_ip(ip_address):
    return hashlib.md5(ip_address.encode("utf-8")).hexdigest()


def run_command(cmd, cwd=None):
    """Run a command directly"""
    if isinstance(cmd, str):
        cmd = cmd.split()
    ret = {}
    if cwd:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        try:
            ret["out"] = stdout.decode("utf-8")
        except BaseException:
            ret["out"] = ""
        try:
            ret["error"] = stderr.decode("utf-8")
        except BaseException:
            ret["error"] = ""
    else:
        try:
            ret["error"] = stderr.decode("utf-8")
        except BaseException:
            ret["error"] = ""
    return ret


def media_file_info(input_file):
    """
    Get the info about an input file, as determined by ffprobe

    Returns a dict, with the keys:
    - `filename`: Filename
    - `file_size`: Size of the file in bytes
    - `video_duration`: Duration of the video in `s.msec`
    - `video_frame_rate_d`: Framerate fraction denominator
    - `video_frame_rate_n`: Framerate fraction nominator
    - `video_bitrate`: Bitrate of the video stream in kBit/s
    - `video_width`: Width in pixels
    - `video_height`: Height in pixels
    - `interlaced` : True if the video is interlaced
    - `video_codec`: Video codec
    - `audio_duration`: Duration of the audio in `s.msec`
    - `audio_sample_rate`: Audio sample rate in Hz
    - `audio_codec`: Audio codec name (`aac`)
    - `audio_bitrate`: Bitrate of the video stream in kBit/s

    Also returns the video and audio info raw from ffprobe.
    """
    ret = {}

    if not os.path.isfile(input_file):
        ret["fail"] = True
        return ret

    video_info = {}
    audio_info = {}
    cmd = ["stat", "-c", "%s", input_file]

    stdout = run_command(cmd).get("out")
    if stdout:
        file_size = int(stdout.strip())
    else:
        ret["fail"] = True
        return ret

    cmd = ["md5sum", input_file]
    stdout = run_command(cmd).get("out")
    if stdout:
        md5sum = stdout.split()[0]
    else:
        md5sum = ""

    cmd = [
        settings.FFPROBE_COMMAND,
        "-loglevel",
        "error",
        "-show_streams",
        "-show_entries",
        "format=format_name",
        "-of",
        "json",
        input_file,
    ]
    stdout = run_command(cmd).get("out")
    try:
        info = json.loads(stdout)
    except TypeError:
        ret["fail"] = True
        return ret

    has_video = False
    has_audio = False
    for stream_info in info["streams"]:
        if stream_info["codec_type"] == "video":
            video_info = stream_info
            has_video = True
            if info.get("format") and info["format"].get("format_name", "") in [
                "tty",
                "image2",
                "image2pipe",
                "bin",
                "png_pipe",
                "gif",
            ]:
                ret["fail"] = True
                return ret
        elif stream_info["codec_type"] == "audio":
            audio_info = stream_info
            has_audio = True

    if not has_video:
        ret["is_video"] = False
        ret["is_audio"] = has_audio
        ret["audio_info"] = audio_info
        return ret

    if "duration" in video_info.keys():
        video_duration = float(video_info["duration"])
    elif "tags" in video_info.keys() and "DURATION" in video_info["tags"]:
        duration_str = video_info["tags"]["DURATION"]
        try:
            hms, msec = duration_str.split(".")
        except ValueError:
            hms, msec = duration_str.split(",")
        total_dur = sum(int(x) * 60**i for i, x in enumerate(reversed(hms.split(":"))))
        video_duration = total_dur + float("0." + msec)
    else:
        cmd = [
            settings.FFPROBE_COMMAND,
            "-loglevel",
            "error",
            "-show_format",
            "-of",
            "json",
            input_file,
        ]
        stdout = run_command(cmd).get("out")
        format_info = json.loads(stdout)["format"]
        try:
            video_duration = float(format_info["duration"])
        except KeyError:
            ret["fail"] = True
            return ret

    if "bit_rate" in video_info.keys():
        video_bitrate = round(float(video_info["bit_rate"]) / 1024.0, 2)
    else:
        cmd = [
            settings.FFPROBE_COMMAND,
            "-loglevel",
            "error",
            "-select_streams",
            "v",
            "-show_entries",
            "packet=size",
            "-of",
            "compact=p=0:nk=1",
            input_file,
        ]
        stdout = run_command(cmd).get("out")
        stream_size = sum([int(line.replace("|", "")) for line in stdout.split("\n") if line != ""])
        video_bitrate = round((stream_size * 8 / 1024.0) / video_duration, 2)

    if "r_frame_rate" in video_info.keys():
        video_frame_rate = video_info["r_frame_rate"].partition("/")
        video_frame_rate_n = video_frame_rate[0]
        video_frame_rate_d = video_frame_rate[2]

    interlaced = False
    if video_info.get("field_order") in ("tt", "tb", "bt", "bb"):
        interlaced = True

    ret = {
        "filename": input_file,
        "file_size": file_size,
        "video_duration": video_duration,
        "video_frame_rate_n": video_frame_rate_n,
        "video_frame_rate_d": video_frame_rate_d,
        "video_bitrate": video_bitrate,
        "video_width": video_info["width"],
        "video_height": video_info["height"],
        "video_codec": video_info["codec_name"],
        "has_video": has_video,
        "has_audio": has_audio,
        "color_range": video_info.get("color_range"),
        "color_space": video_info.get("color_space"),
        "color_transfer": video_info.get("color_space"),
        "color_primaries": video_info.get("color_primaries"),
        "interlaced": interlaced,
        "display_aspect_ratio": video_info.get("display_aspect_ratio"),
        "sample_aspect_ratio": video_info.get("sample_aspect_ratio"),
    }

    if has_audio:
        if "duration" in audio_info.keys():
            audio_duration = float(audio_info["duration"])
        elif "tags" in audio_info.keys() and "DURATION" in audio_info["tags"]:
            duration_str = audio_info["tags"]["DURATION"]
            try:
                hms, msec = duration_str.split(".")
            except ValueError:
                hms, msec = duration_str.split(",")
            total_dur = sum(int(x) * 60**i for i, x in enumerate(reversed(hms.split(":"))))
            audio_duration = total_dur + float("0." + msec)
        else:
            cmd = [
                settings.FFPROBE_COMMAND,
                "-loglevel",
                "error",
                "-show_format",
                "-of",
                "json",
                input_file,
            ]
            stdout = run_command(cmd).get("out")
            format_info = json.loads(stdout)["format"]
            audio_duration = float(format_info["duration"])

        if "bit_rate" in audio_info.keys():
            audio_bitrate = round(float(audio_info["bit_rate"]) / 1024.0, 2)
        else:
            cmd = [
                settings.FFPROBE_COMMAND,
                "-loglevel",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "packet=size",
                "-of",
                "compact=p=0:nk=1",
                input_file,
            ]
            stdout = run_command(cmd).get("out")
            stream_size = sum([int(line.replace("|", "")) for line in stdout.split("\n") if line != ""])
            audio_bitrate = round((stream_size * 8 / 1024.0) / audio_duration, 2)

        ret.update(
            {
                "audio_duration": audio_duration,
                "audio_sample_rate": audio_info["sample_rate"],
                "audio_codec": audio_info["codec_name"],
                "audio_bitrate": audio_bitrate,
                "audio_channels": audio_info["channels"],
            }
        )

    ret["video_info"] = video_info
    ret["audio_info"] = audio_info
    ret["is_video"] = True
    ret["md5sum"] = md5sum
    return ret


def calculate_seconds(duration):
    ret = 0
    if isinstance(duration, str):
        duration = duration.split(":")
        if len(duration) != 3:
            return ret
    else:
        return ret

    ret += int(float(duration[2]))
    ret += int(float(duration[1])) * 60
    ret += int(float(duration[0])) * 60 * 60
    return ret


def show_file_size(size):
    if size:
        size = size / 1000000
        size = round(size, 1)
        size = f"{str(size)}MB"
    return size


def get_base_ffmpeg_command(
    input_file,
    output_file,
    has_audio,
    codec,
    encoder,
    audio_encoder,
    target_fps,
    interlaced,
    target_height,
    target_rate,
    target_rate_audio,
    pass_file,
    pass_number,
    enc_type,
    chunk,
    use_gpu=False,       # dev-v0.2.0: True when ENCODING_BACKEND=gpu and codec=h264
):
    """Get the base command for a specific codec, height/rate, and pass

    Arguments:
        input_file {str} -- input file name
        output_file {str} -- output file name
        has_audio {bool} -- does the input have audio?
        codec {str} -- video codec
        encoder {str} -- video encoder
        audio_encoder {str} -- audio encoder
        target_fps {fractions.Fraction} -- target FPS
        interlaced {bool} -- true if interlaced
        target_height {int} -- height
        target_rate {int} -- target bitrate in kbps
        target_rate_audio {int} -- audio target bitrate
        pass_file {str} -- path to temp pass file
        pass_number {int} -- number of passes
        enc_type {str} -- encoding type (twopass or crf)
        chunk {bool} -- whether this is a chunk encode
        use_gpu {bool} -- use h264_nvenc GPU path (default False, CPU path unchanged)
    """

    # avoid very high frame rates
    while target_fps > 60:
        target_fps = target_fps / 2

    if target_fps < 1:
        target_fps = 1

    filters = []

    if interlaced:
        filters.append("yadif")

    target_width = round(target_height * 16 / 9)
    scale_filter_opts = [
        f"if(lt(iw\\,ih)\\,{target_height}\\,{target_width})",
        f"if(lt(iw\\,ih)\\,{target_width}\\,{target_height})",
        "force_original_aspect_ratio=decrease",
        "force_divisible_by=2",
        "flags=lanczos",
    ]
    scale_filter_str = "scale=" + ":".join(scale_filter_opts)
    filters.append(scale_filter_str)

    fps_str = f"fps=fps={target_fps}"
    filters.append(fps_str)

    filters_str = ",".join(filters)

    base_cmd = [
        settings.FFMPEG_COMMAND,
        "-y",
        "-i",
        input_file,
        "-c:v",
        encoder,
        "-filter:v",
        filters_str,
        "-pix_fmt",
        "yuv420p",
    ]

    if enc_type == "twopass":
        base_cmd.extend(["-b:v", str(target_rate) + "k"])
    elif enc_type == "crf":
        if use_gpu:
            # NVENC: -cq instead of -crf, same numeric value
            base_cmd.extend(["-cq", str(VIDEO_CRFS[codec])])
        else:
            base_cmd.extend(["-crf", str(VIDEO_CRFS[codec])])
        if encoder == "libvpx-vp9":
            base_cmd.extend(["-b:v", str(target_rate) + "k"])

    if has_audio:
        base_cmd.extend(
            [
                "-c:a",
                audio_encoder,
                "-b:a",
                str(target_rate_audio) + "k",
                "-ac",
                "2",
            ]
        )

    # get keyframe distance in frames
    keyframe_distance = int(target_fps * KEYFRAME_DISTANCE)

    cmd = base_cmd[:]

    # preset settings
    preset = getattr(settings, "FFMPEG_DEFAULT_PRESET", "medium")

    if encoder == "libvpx-vp9":
        if pass_number == 1:
            speed = 4
        else:
            speed = VP9_SPEED

    # ============================================
    # dev-v0.2.0: ENCODER-SPECIFIC FLAG BLOCKS
    # CPU path (use_gpu=False): identical to v0.1.0 in every flag
    # GPU path (use_gpu=True): h264_nvenc-compatible flags only
    # ============================================

    if encoder == "libx264":
        # ── CPU PATH ── unchanged from v0.1.0
        level = "4.2" if target_height <= 1080 else "5.2"

        x264_params = [
            "keyint=" + str(keyframe_distance * 2),
            "keyint_min=" + str(keyframe_distance),
        ]

        cmd.extend(
            [
                "-maxrate",
                str(int(int(target_rate) * MAX_RATE_MULTIPLIER)) + "k",
                "-bufsize",
                str(int(int(target_rate) * BUF_SIZE_MULTIPLIER)) + "k",
                "-force_key_frames",
                "expr:gte(t,n_forced*" + str(KEYFRAME_DISTANCE) + ")",
                "-x264-params",
                ":".join(x264_params),
                "-preset",
                preset,
                "-profile:v",
                VIDEO_PROFILES[codec],
                "-level",
                level,
            ]
        )

        if enc_type == "twopass":
            cmd.extend(["-passlogfile", pass_file, "-pass", pass_number])

    elif encoder == "h264_nvenc":
        # ── GPU PATH ── h264_nvenc-compatible flags only
        # REMOVED: -x264-params (fatal error with h264_nvenc, not supported)
        # REMOVED: two-pass passlogfile (NVENC twopass != libx264 twopass, not compatible)
        # PRESERVED: -maxrate, -bufsize, -force_key_frames, -profile:v, -level
        level = "4.2" if target_height <= 1080 else "5.2"
        gpu_preset = getattr(settings, "ENCODING_GPU_PRESET", "p4")

        cmd.extend(
            [
                "-maxrate",
                str(int(int(target_rate) * MAX_RATE_MULTIPLIER)) + "k",
                "-bufsize",
                str(int(int(target_rate) * BUF_SIZE_MULTIPLIER)) + "k",
                "-force_key_frames",
                "expr:gte(t,n_forced*" + str(KEYFRAME_DISTANCE) + ")",
                "-g",
                str(keyframe_distance * 2),
                "-keyint_min",
                str(keyframe_distance),
                "-preset",
                gpu_preset,
                "-profile:v",
                VIDEO_PROFILES[codec],
                "-level",
                level,
            ]
        )
        logger.info(
            f"🖥️  GPU encode: h264_nvenc preset={gpu_preset} "
            f"resolution={target_height}p cq={VIDEO_CRFS[codec]}"
        )

    elif encoder == "libx265":
        # ── CPU PATH ── unchanged from v0.1.0
        x265_params = [
            "vbv-maxrate=" + str(int(int(target_rate) * MAX_RATE_MULTIPLIER)),
            "vbv-bufsize=" + str(int(int(target_rate) * BUF_SIZE_MULTIPLIER)),
            "keyint=" + str(keyframe_distance * 2),
            "keyint_min=" + str(keyframe_distance),
        ]

        if enc_type == "twopass":
            x265_params.extend(["stats=" + str(pass_file), "pass=" + str(pass_number)])

        cmd.extend(
            [
                "-force_key_frames",
                "expr:gte(t,n_forced*" + str(KEYFRAME_DISTANCE) + ")",
                "-x265-params",
                ":".join(x265_params),
                "-preset",
                preset,
                "-profile:v",
                VIDEO_PROFILES[codec],
            ]
        )

    elif encoder == "libvpx-vp9":
        # ── CPU PATH ── unchanged from v0.1.0
        cmd.extend(
            [
                "-g",
                str(keyframe_distance),
                "-keyint_min",
                str(keyframe_distance),
                "-maxrate",
                str(int(int(target_rate) * MAX_RATE_MULTIPLIER)) + "k",
                "-minrate",
                str(int(int(target_rate) * MIN_RATE_MULTIPLIER)) + "k",
                "-bufsize",
                str(int(int(target_rate) * BUF_SIZE_MULTIPLIER)) + "k",
                "-speed",
                speed,
            ]
        )

        if enc_type == "twopass":
            cmd.extend(["-passlogfile", pass_file, "-pass", pass_number])

    cmd.extend(
        [
            "-strict",
            "-2",
        ]
    )

    if pass_number == 1:
        cmd.extend(["-an", "-f", "null", "/dev/null"])
    elif pass_number == 2:
        if output_file.endswith("mp4") and chunk:
            cmd.extend(["-movflags", "+faststart"])
        cmd.extend([output_file])

    return cmd


def produce_ffmpeg_commands(media_file, media_info, resolution, codec, output_filename, pass_file, chunk=False):
    # dev-v0.2.0: reads ENCODING_BACKEND from settings to select CPU or GPU encoder for h264
    # vp9 and h265 are always CPU-encoded regardless of ENCODING_BACKEND
    try:
        media_info = json.loads(media_info)
    except BaseException:
        media_info = {}

    # ── ENCODER SELECTION ──────────────────────────────────────────
    # dev-v0.2.0: GPU path activates only for h264 + ENCODING_BACKEND=gpu
    # All other codecs (h265, vp9) always use CPU encoders
    use_gpu = False

    if codec == "h264":
        encoding_backend = getattr(settings, "ENCODING_BACKEND", "cpu").lower()
        if encoding_backend == "gpu":
            encoder = "h264_nvenc"
            use_gpu = True
            logger.info(f"🖥️  GPU encoding selected for h264 (ENCODING_BACKEND=gpu)")
        else:
            encoder = "libx264"
            logger.debug(f"💻 CPU encoding selected for h264 (ENCODING_BACKEND=cpu)")
    elif codec in ["h265", "hevc"]:
        encoder = "libx265"
        # vp9 and h265 always CPU — GPU path not implemented for these codecs
    elif codec == "vp9":
        encoder = "libvpx-vp9"
        # vp9 and h265 always CPU — GPU path not implemented for these codecs
    else:
        return False
    # ──────────────────────────────────────────────────────────────

    target_fps = Fraction(int(media_info.get("video_frame_rate_n", 30)), int(media_info.get("video_frame_rate_d", 1)))
    if target_fps <= 30:
        target_rate = VIDEO_BITRATES[codec][25].get(resolution)
    else:
        target_rate = VIDEO_BITRATES[codec][60].get(resolution)
    if not target_rate:
        target_rate = VIDEO_BITRATES[codec][25].get(resolution)
    if not target_rate:
        return False

    if media_info.get("video_height") < resolution:
        if resolution not in settings.MINIMUM_RESOLUTIONS_TO_ENCODE:
            return False

    if media_info.get("video_duration") > CRF_ENCODING_NUM_SECONDS:
        enc_type = "crf"
    else:
        enc_type = "twopass"

    # dev-v0.2.0: GPU path forces crf mode
    # NVENC two-pass is a different mechanism and not compatible with the
    # existing passlogfile-based two-pass in tasks.py
    # In practice this never triggers since CRF_ENCODING_NUM_SECONDS=2
    # means all real videos already use enc_type="crf"
    if use_gpu and enc_type == "twopass":
        logger.warning(
            f"⚠️  GPU mode does not support passlogfile two-pass. "
            f"Forcing enc_type=crf for {codec} {resolution}p"
        )
        enc_type = "crf"

    if enc_type == "twopass":
        passes = [1, 2]
    elif enc_type == "crf":
        passes = [2]

    interlaced = media_info.get("interlaced")

    cmds = []
    for pass_number in passes:
        cmds.append(
            get_base_ffmpeg_command(
                media_file,
                output_file=output_filename,
                has_audio=media_info.get("has_audio"),
                codec=codec,
                encoder=encoder,
                audio_encoder=AUDIO_ENCODERS[codec],
                target_fps=target_fps,
                interlaced=interlaced,
                target_height=resolution,
                target_rate=target_rate,
                target_rate_audio=AUDIO_BITRATES[codec],
                pass_file=pass_file,
                pass_number=pass_number,
                enc_type=enc_type,
                chunk=chunk,
                use_gpu=use_gpu,    # dev-v0.2.0: passed through to flag builder
            )
        )
    return cmds


def clean_query(query):
    """Clear text to comply with SearchQuery known exception cases"""
    if not query:
        return ""
    chars = ["^", "{", "}", "&", "|", "<", ">", '"', ")", "(", "!", ":", ";", "'", "#"]
    for char in chars:
        query = query.replace(char, "")
    return query.lower()


def timestamp_to_seconds(timestamp):
    """Convert a timestamp in format HH:MM:SS.mmm to seconds"""
    h, m, s = timestamp.split(':')
    s, ms = s.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + float('0.' + ms)


def seconds_to_timestamp(seconds):
    """Convert seconds to timestamp in format HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    seconds_int = int(seconds_remainder)
    milliseconds = int((seconds_remainder - seconds_int) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}.{milliseconds:03d}"


def get_trim_timestamps(media_file_path, timestamps_list, run_ffprobe=False):
    """Process a list of timestamps to align start times with I-frames for better video trimming"""
    if not isinstance(timestamps_list, list):
        return []

    timestamps_results = []
    timestamps_to_process = []

    for item in timestamps_list:
        if isinstance(item, dict) and 'startTime' in item and 'endTime' in item:
            timestamps_to_process.append(item)

    if not timestamps_to_process:
        return []

    if len(timestamps_to_process) == 1 and timestamps_to_process[0]['startTime'] == "00:00:00.000":
        return timestamps_list

    for item in timestamps_to_process:
        startTime = item['startTime']
        endTime = item['endTime']

        i_frames = []
        if run_ffprobe:
            SEC_TO_SUBTRACT = 10
            start_seconds = timestamp_to_seconds(startTime)
            search_start = max(0, start_seconds - SEC_TO_SUBTRACT)

            cmd = [
                settings.FFPROBE_COMMAND,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "frame=pts_time,pict_type",
                "-of", "csv=p=0",
                "-read_intervals", f"{search_start}%{startTime}",
                media_file_path,
            ]
            cmd = [str(s) for s in cmd]
            logger.info(f"trim cmd: {cmd}")

            stdout = run_command(cmd).get("out")

            if stdout:
                for line in stdout.strip().split('\n'):
                    if line and line.endswith(',I'):
                        i_frames.append(line.replace(',I', ''))

            if i_frames:
                adjusted_startTime = seconds_to_timestamp(float(i_frames[-1]))

        if not i_frames:
            adjusted_startTime = startTime

        timestamps_results.append({'startTime': adjusted_startTime, 'endTime': endTime})

    return timestamps_results


def trim_video_method(media_file_path, timestamps_list):
    """Trim a video file based on a list of timestamps"""
    if not isinstance(timestamps_list, list) or not timestamps_list:
        return False

    if not os.path.exists(media_file_path):
        return False

    with tempfile.TemporaryDirectory(dir=settings.TEMP_DIRECTORY) as temp_dir:
        _, input_ext = os.path.splitext(media_file_path)
        output_file = os.path.join(temp_dir, f"output{input_ext}")

        segment_files = []
        for i, item in enumerate(timestamps_list):
            start_time = timestamp_to_seconds(item['startTime'])
            end_time = timestamp_to_seconds(item['endTime'])
            duration = end_time - start_time

            segment_file = output_file if len(timestamps_list) == 1 else os.path.join(temp_dir, f"segment_{i}{input_ext}")

            cmd = [settings.FFMPEG_COMMAND, "-y", "-ss", str(item['startTime']), "-i", media_file_path, "-t", str(duration), "-c", "copy", "-avoid_negative_ts", "1", segment_file]

            result = run_command(cmd)  # noqa

            if os.path.exists(segment_file) and os.path.getsize(segment_file) > 0:
                if len(timestamps_list) > 1:
                    segment_files.append(segment_file)
            else:
                return False

        if len(timestamps_list) > 1:
            if not segment_files:
                return False

            concat_list_path = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_list_path, "w") as f:
                for segment in segment_files:
                    f.write(f"file '{segment}'\n")
            concat_cmd = [settings.FFMPEG_COMMAND, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", output_file]

            concat_result = run_command(concat_cmd)  # noqa

            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                return False

        try:
            rm_file(media_file_path)
            shutil.copy2(output_file, media_file_path)
            return True
        except Exception as e:
            logger.info(f"Failed to replace original file: {str(e)}")
            return False


def get_alphanumeric_only(string):
    """Returns a query that contains only alphanumeric characters"""
    string = "".join([char for char in string if char.isalnum()])
    return string.lower()
