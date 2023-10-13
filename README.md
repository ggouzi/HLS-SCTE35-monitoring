# HLS Adbreak Monitoring

This script will monitor a HLS stream periodically until it finds a SCTE35 marker (cue-point) flagged with the corresponding tag. Supported tags are:
- EXT-X-CUE-OUT/IN
- EXT-X-DATERANGE
- EXT-OATCLS-SCTE35
- Any custom tag you can specify

## Purpose

The purpose of this project is to provide a tool for monitoring and analyzing ad-markers in HLS media playlists. This can be valuable for content creators, broadcasters, or developers who need to track and understand ad-markers for various purposes, such as ad insertion or content analytics.

## How It Works

1. **Input HLS Master Playlist URL**: Enters your master playlist URL as parameter of the script. Format must be HTTP(S) and ends with a valid .m3u8 extension (query parameters are supported)

2. **Add optional parameters**: See [Usage](#Usage) below

3. **Let it run for a while**: Script will scan periodically each rendition of the master playlist and look for ad-marker-related tags, sleep for the chunk duration, and fetch again the updated version of the playlist until it finds a keyword to stop.

4. **Analyse Results**: The output is retured to stdout

## Usage

```bash
usage: hls-scte35-monitoring.py [-h] [-e EXIT_IF_FOUND] [-d DECODE] [-t ADBREAK_TYPE | -c CUSTOM_MATCH] master_playlist_url

positional arguments:
  master_playlist_url

options:
  -h, --help            show this help message and exit
  -e EXIT_IF_FOUND, --exit-if-found EXIT_IF_FOUND
                        Stop script after the first ad break is being found, default True
  -d DECODE, --decode DECODE
                        Decode SCTE35 binarydata (hex or base64). Works only for tags where the binarydata can be parsed from the tag
  -t ADBREAK_TYPE, --ad-break-type ADBREAK_TYPE
                        Ad break types to match: EXT-X-CUE, EXT-X-DATERANGE, EXT-OATCLS-SCTE35 or ALL, default ALL
  -c CUSTOM_MATCH, --custom CUSTOM_MATCH
                        Define a custom keyword to match
```

## Examples

<ins>Example</ins>: Look for any EXT-X-CUE-OUT tag and stop once found
```bash
$ python3 hls-scte35-monitoring.py http://localhost:8000/demo_streams/demo_master_cue.m3u8 -t EXT-X-CUE

Media Playlist found
Path: index_1_cue.m3u8, bandwidth: 2665726, average-bandwidth: 2526299, resolution: 960x540, frame_rate: 29.97, codecs: avc1.640029,mp4a.40.2

2023-10-13 16:53:14 - No ad break found
Waiting 7000ms
2023-10-13 16:53:21 - No ad break found
Waiting 7000ms
2023-10-13 16:53:28 - Ad break found!
	ID=1.0, DURATION=6.000
Exiting..
```

<ins>Example</ins>: Look for any EXT-X-CUE-DATERANGE tag and never stop
```bash
$ python3 hls-scte35-monitoring.py http://localhost:8000/demo_streams/demo_master_daterange.m3u8 -t EXT-X-DATERANGE -e false

Media Playlist found
Path: index_1_daterange.m3u8, bandwidth: 2665726, average-bandwidth: 2526299, resolution: 960x540, frame_rate: 29.97, codecs: avc1.640029,mp4a.40.2

2023-10-13 17:16:43 - No ad break found
Waiting 7000ms
2023-10-13 17:16:50 - Ad break found!
	ID=111.0, DURATION=None, PLANNED_DURATION=None, START_DATE=2023-10-13T10:31:00.000Z, BINARYDATA=/DBIAAAAAAAA///wBQb+ek2ItgAyAhdDVUVJSAAAGH+fCAgAAAAALMvDRBEAAAIXQ1VFSUgAABl/nwgIAAAAACyk26AQAACZcuND
```

<ins>Example</ins>: Look for any EXT-X-OATCLS tag, stop once found and decode its binarydata
```bash
$ python3 hls-scte35-monitoring.py http://localhost:8000/demo_streams/demo_master_oatcls.m3u8 -t EXT-OATCLS-SCTE35 -e true -d true

Media Playlist found
Path: index_1_oatcls.m3u8, bandwidth: 2665726, average-bandwidth: 2526299, resolution: 960x540, frame_rate: 29.97, codecs: avc1.640029,mp4a.40.2

2023-10-13 17:18:39 - Ad break found!
	ID=-1, BINARYDATA=/DAnAAAAAAAAAP/wBQb+AA27oAARAg9DVUVJAAAAAX+HCQA0AAE0xUZn
{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 39,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment_ticks": 0,
        "pts_adjustment": 0.0,
        "cw_index": "0x0",
        "tier": "0xfff",
        "splice_command_length": 5,
        "splice_command_type": 6,
        "descriptor_loop_length": 17,
        "crc": "0x34c54667"
    },
    "command": {
        "command_length": 5,
        "command_type": 6,
        "name": "Time Signal",
        "time_specified_flag": true,
        "pts_time": 10.0,
        "pts_time_ticks": 900000
    },
    "descriptors": [
        {
            "tag": 2,
            "descriptor_length": 15,
            "name": "Segmentation Descriptor",
            "identifier": "CUEI",
            "components": [],
            "segmentation_event_id": "0x1",
            "segmentation_event_cancel_indicator": false,
            "program_segmentation_flag": true,
            "segmentation_duration_flag": false,
            "delivery_not_restricted_flag": false,
            "web_delivery_allowed_flag": false,
            "no_regional_blackout_flag": false,
            "archive_allowed_flag": true,
            "device_restrictions": "No Restrictions",
            "segmentation_message": "Provider Placement Opportunity Start",
            "segmentation_upid_type": 9,
            "segmentation_upid_type_name": "No UPID",
            "segmentation_upid_length": 0,
            "segmentation_type_id": 52,
            "segment_num": 0,
            "segments_expected": 1,
            "sub_segment_num": 0,
            "sub_segments_expected": 0
        }
    ]
}
Exiting..
```

You can customize the script to monitor the presence of any string. It may not be related to ad-markers at all.
<ins>Example</ins>: Monitor if the tag EXT-X-DISCONTINUITY appears in a rendition of the playlist
```bash
python3 hls-scte35-monitoring.py http://localhost:8000/demo_stream/demo_master.m3u8 -c EXT-X-DISCONTINUITY
```

If you do not know what kind of tags are present in the playlists, you can use -t ALL to match any of the supported ad-marker tags


## Dependencies

- [argsparse](https://docs.python.org/3/library/argparse.html)
- [threefive](https://github.com/futzu/scte35-threefive)
- [urllib](https://docs.python.org/fr/3/library/urllib.html)

## License

This project is released under the [MIT License](LICENSE).

---

**Note:** HLS-SCTE35-Monitoring is a side project and provided as-is. It may require adjustments and improvements to meet your specific use case.
