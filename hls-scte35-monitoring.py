import requests
from requests import HTTPError
import re
import time
from datetime import datetime
import sys
import urllib
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass
import cue_parser
import argparse
import traceback

# TODO: Dynamic
TO_MATCH = ["EXT-X-CUE", "EXT-X-DATERANGE", "EXT-X-OATCLS"]
DEFAULT_CHUNK_DURATION = 6 # 6s default chunk duration

@dataclass
class MediaPlaylist:
    path: str
    bandwidth: int
    average_bandwidth: int
    resolution: str
    frame_rate: float
    codecs: str

    def __str__(self):
        return f"Path: {self.path}, bandwidth: {self.bandwidth}, average-bandwidth: {self.average_bandwidth}, resolution: {self.resolution}, frame_rate: {self.frame_rate}, codecs: {self.codecs}"

def get_chunk_duration(media_playlist):
    lines = media_playlist.split('\n')
    for line in lines:
        if line.startswith("#EXT-X-TARGETDURATION"):
            duration_str = line.split(":")[1]
            duration = float(duration_str)
            return round(duration)
    return DEFAULT_CHUNK_DURATION

def extract_cues_from_media_playlist(media_playlist, adbreak_type, custom_match, decode):
    cues = []
    scte35_enum = cue_parser.SCTE35Type
    for line in media_playlist.splitlines():
        cue = None
        if scte35_enum.CUE.name in line and (adbreak_type == scte35_enum.CUE.ALL or scte35_enum.CUE==adbreak_type):
            cue = cue_parser.parse_scte_35_cue_out(line)
        elif scte35_enum.DATERANGE.name in line and (adbreak_type == scte35_enum.CUE.ALL or scte35_enum.DATERANGE==adbreak_type):
            cue = cue_parser.parse_scte_35_daterange(line, decode)
        elif scte35_enum.OATCLS.name in line and (adbreak_type == scte35_enum.CUE.ALL or scte35_enum.OATCLS==adbreak_type):
            cue = cue_parser.parse_scte_35_oatcls(line, decode)
        elif custom_match:
            cue = cue_parser.parse_scte_35_custom(line, custom_match)
        if cue:
            cues.append(cue)
    return cues

def fetch_media_playlist(media_playlist_url, adbreak_type, custom_match, exit_if_found, decode):
    adbreaks = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ad_break = None
    chunk_duration = 6000

    try:
        media_playlist_response = requests.get(media_playlist_url)
        if media_playlist_response.status_code != 200:
            raise HTTPError(f"Error fetching HLS media playlist URL {media_playlist_url}. HTTP status code: {media_playlist_response.status_code}")
        media_playlist = media_playlist_response.text

        chunk_duration = get_chunk_duration(media_playlist)

        # Look for any CUE
        cues = []
        if any(keyword in media_playlist for keyword in TO_MATCH):
            cues = extract_cues_from_media_playlist(media_playlist, adbreak_type, custom_match, decode)

        if len(cues) == 0:
            print(f"{now} - No ad break found")
        else:
            print(f"{now} - Ad break found!")
            for cue in cues:
                print(f"\t{cue}")
            if exit_if_found == True:
                print("Exiting..")
                return

        if len(cues) == 0 or (len(cues)>0 and exit_if_found==False):
            print("Waiting " + str(chunk_duration * 1000) + "ms")
            time.sleep(chunk_duration)
            fetch_media_playlist(media_playlist_url, adbreak_type, custom_match, exit_if_found, decode)
    except Exception as e:
        print("Error:", e)


def parse_master_playlist(master_playlist):
    media_playlists = []
    pattern = r'(?:BANDWIDTH=(\d+))|' \
              r'(?:AVERAGE-BANDWIDTH=(\d+))|' \
              r'(?:RESOLUTION=([\d]+x[\d]+))|' \
              r'(?:FRAME-RATE=([\d.]+))|' \
              r'(?:CODECS="([^"]*)")'

    lines = master_playlist.splitlines()
    for index, line in enumerate(lines):
        matches = re.findall(pattern, line)

        path = None
        bandwidth = None
        average_bandwidth = None
        resolution = None
        frame_rate = None
        codecs = None

        for match in matches:
            if match[0]:
                bandwidth = int(match[0])
            elif match[1]:
                average_bandwidth = int(match[1])
            elif match[2]:
                resolution = match[2]
            elif match[3]:
                frame_rate = float(match[3])
            elif match[4]:
                codecs = match[4]
        if all(v is not None for v in [bandwidth, average_bandwidth, resolution, frame_rate, codecs]):
            if (index != len(lines)-1):
                path = lines[index+1]
                media_playlists.append(MediaPlaylist(path, bandwidth, average_bandwidth, resolution, frame_rate, codecs))
    return media_playlists


def fetchMasterPlaylist(master_playlist_url):
    try:
        response = requests.get(master_playlist_url)
        if response.status_code == 200:
            master_playlist = response.text
            return parse_master_playlist(master_playlist)
        else:
            print("Error fetching HLS master playlist. HTTP status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error fetching HLS master playlist:", str(e))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('master_playlist_url')
    parser.add_argument("-e", "--exit-if-found", dest="exit_if_found", help="Stop script after the first ad break is being found, default True", type=str2bool, default=True)
    parser.add_argument("-d", "--decode", dest="decode", help="Decode SCTE35 binarydata (hex or base64). Works only for tags where the binarydata can be parsed from the tag", type=str2bool, default=False)
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("-t", "--ad-break-type", dest='adbreak_type', help="Ad break types to match: EXT-X-CUE, EXT-X-DATERANGE, EXT-OATCLS-SCTE35 or ALL, default ALL", type=cue_parser.SCTE35Type, default=cue_parser.SCTE35Type.CUE.name)
    command_group.add_argument("-c", "--custom", dest="custom_match", help="Define a custom keyword to match", type=str, default=None)
    args = parser.parse_args()

    master_playlist_url = args.master_playlist_url
    parsed_url = urlparse(master_playlist_url)
    # Allow only HTTP/HTTPS protocol and URL must have a valid .m3u8 extension (query parameters are allowed)
    if parsed_url.path.endswith(".m3u8") and parsed_url.scheme in ("http", "https"):
        media_playlists = fetchMasterPlaylist(master_playlist_url)
        if media_playlists is None:
            return

        base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
        for media_playlist in media_playlists:
            print(f"\nMedia Playlist found\n{media_playlist}\n")
            media_playlist_url = parsed_url.scheme
            media_playlist_url = urllib.parse.urljoin(base_url, media_playlist.path)
            fetch_media_playlist(media_playlist_url, args.adbreak_type, args.custom_match, args.exit_if_found, args.decode)
    else:
        print("HLS master playlist URL must end with .m3u8 and be retrieved through http or https protocols")
        return

if __name__ == "__main__":
    main()
