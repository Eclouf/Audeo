
class Formateur:
    def __init__(self, options):
        self.options = options

    def formater(self, options: dict):
        yt_dlp_options = {}
        yt_dlp_postprocessors = {}
        
        for key, value in options.items():
            if key != 'postprocessors':
                yt_dlp_options.update({key: value})
            
        if 'postprocessors' in options:
            for key, value in options['postprocessors'].items():
                if key == 'FFmpegExtractAudio':
                    # Traiter FFmpegExtractAudio avec tuple (codec, qualité, nopostoverwrites)
                    codec, quality, nopostoverwrites = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'preferredcodec': codec,
                        'preferredquality': quality,
                        'nopostoverwrites': nopostoverwrites
                    })
                if key == 'FFmpegMetadata':
                    # Traiter FFmpegMetadata avec booléen add_metadata
                    metadata, chapters, sponsorblock = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'add_metadata': metadata,  # Ajouter des métadonnées au fichier
                        'add_chapters': chapters,  # Ajouter des chapitres au fichier
                        'add_sponsorblock_chapters': sponsorblock,  # Ajouter des chapitres SponsorBlock
                    })
                if key == 'FFmpegEmbedSubtitle':
                    # Traiter FFmpegEmbedSubtitle avec booléen already_have_subtitle
                    subtitle = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'already_have_subtitle': subtitle,  # Indicateur si les sous-titres sont déjà intégrés
                    })
                if key == 'FFmpegMerger':
                    # Traiter FFmpegMerger avec booléen only_merge
                    merge = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'only_merge': merge,  # Indicateur pour ne faire que la fusion
                    })
                if key == 'FFmpegFixupM3u8':
                    # Traiter FFmpegFixupM3u8 avec chaîne fixup
                    fixup = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'fixup': fixup,  # Choix de fixup (never, warn, detect_or_warn)
                    })
                if key == 'FFmpegThumbnailsConvertor':
                    # Traiter FFmpegThumbnailsConvertor avec chaîne format
                    format = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'format': format,  # Format de la miniature (ex: jpg, png)
                    })
                if key == 'FFmpegEmbedThumbnail':
                    # Traiter FFmpegEmbedThumbnail avec booléen already_have_thumbnail
                    thumbnail = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'already_have_thumbnail': thumbnail,  # Indique si la miniature est déjà intégrée
                    })
                if key == 'FFmpegExtractFrames':
                    # Traiter FFmpegExtractFrames avec chaîne frames et output_dir
                    frames, output_dir = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'frames': frames,  # Cadres à extraire
                        'output_dir': output_dir,  # Répertoire de sortie pour les images
                    })
                if key == 'SRTSubtitlesConvertor':
                    # Traiter SRTSubtitlesConvertor avec chaîne format
                    format = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'format': format,  # Format des sous-titres (ex: srt, vtt)
                    })
                if key == 'FFmpegChaptersConvertor':
                    # Traiter FFmpegChaptersConvertor avec chaîne chapters
                    chapters = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'chapters': chapters,  # Fichier de chapitres à utiliser
                    })
                if key == 'MetadataFromField':
                    # Traiter MetadataFromField avec chaîne field
                    field = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'field': field,  # Champ à extraire (ex: title, uploader)
                    })
                if key == 'FFmpegWatermark':
                    # Traiter FFmpegWatermark avec chaîne watermark et position
                    watermark, position = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'watermark': watermark,  # Fichier de filigrane
                        'position': position,  # Position du filigrane (ex: top-right, bottom-left)
                    })
                if key == 'FFmpegTextOverlay':
                    # Traiter FFmpegTextOverlay avec chaîne text et position
                    text, position = value
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'text': text,  # Texte à ajouter
                        'position': position,  # Position du texte (ex: top-right, bottom-left)
                    })
                
                if key == 'FFmpegVideoConvertor':
                    # Traiter les autres postprocesseurs avec une seule valeur
                    yt_dlp_postprocessors.append({
                        'key': key,
                        'preferedformat': value
                    })
        yt_dlp_options.update({'postprocessors': yt_dlp_postprocessors})
        return yt_dlp_options



yt_dlp_options = {
    
    # Options d'authentification
    'username': 'myusername',  # Username for authentication purposes.
    'password': 'mypassword',  # Password for authentication purposes.
    'videopassword': 'videopassword',  # Password for accessing a video.
    'ap_mso': 'AdobePassMSO',  # Adobe Pass multiple-system operator identifier.
    'ap_username': 'apusername',  # Multiple-system operator account username.
    'ap_password': 'appassword',  # Multiple-system operator account password.
    'usenetrc': True,  # Use netrc for authentication instead.
    'netrc_location': '/path/to/netrc',  # Location of the netrc file. Defaults to ~/.netrc.
    'netrc_cmd': 'command_to_get_credentials',  # Use a shell command to get credentials.

    # Options de sortie
    'verbose': True,  # Print additional info to stdout.
    'quiet': True,  # Do not print messages to stdout (contradicts verbose).
    'no_warnings': True,  # Do not print out anything for warnings.
    'forceprint': {'video': ['%(title)s', '%(url)s']},  # Print specific templates to stdout.
    'print_to_file': {'video': [('%(title)s', 'title.txt')]},  # Print specific templates to files.
    'forcejson': True,  # Force printing info_dict as JSON.
    'dump_single_json': True,  # Force printing the info_dict of the whole playlist (or video) as a single JSON line.
    'force_write_download_archive': True,  # Force writing download archive regardless of 'skip_download' or 'simulate'.
    'simulate': True,  # Do not download the video files.
    'format': 'best',  # Video format code.
    'allow_unplayable_formats': True,  # Allow unplayable formats to be extracted and downloaded.
    'ignore_no_formats_error': True,  # Ignore "No video formats" error.
    'format_sort': ['res', 'br'],  # Sort formats by resolution and bitrate.
    'format_sort_force': True,  # Force the given format_sort.
    'prefer_free_formats': True,  # Prefer free formats over non-free ones.
    'allow_multiple_video_streams': True,  # Allow multiple video streams to be merged into a single file.
    'allow_multiple_audio_streams': True,  # Allow multiple audio streams to be merged into a single file.
    'check_formats': 'selected',  # Check selected formats for downloadability.
    'paths': {'home': '/downloads', 'temp': '/temp'},  # Dictionary of output paths.
    'outtmpl': {'default': '%(title)s.%(ext)s'},  # Template for output names.
    'outtmpl_na_placeholder': 'NA',  # Placeholder for unavailable meta fields.
    'restrictfilenames': True,  # Do not allow "&" and spaces in file names.
    'trim_file_name': 50,  # Limit length of filename (extension excluded).
    'windowsfilenames': True,  # Force the filenames to be Windows compatible.
    'ignoreerrors': 'only_download',  # Ignore only download errors.
    'skip_playlist_after_errors': 5,  # Number of allowed failures until the rest of the playlist is skipped.
    'allowed_extractors': ['youtube', 'vimeo'],  # List of allowed extractors.
    'overwrites': True,  # Overwrite all video and metadata files if True.
    'playlist_items': '1-5,10',  # Specific indices of playlist to download.
    'playlistrandom': True,  # Download playlist items in random order.
    'lazy_playlist': True,  # Process playlist entries as they are received.
    'matchtitle': '.*Tutorial.*',  # Download only matching titles.
    'rejecttitle': '.*Ad.*',  # Reject downloads for matching titles.
    'logger': None,  # Log messages to a logging.Logger instance.
    'logtostderr': True,  # Print everything to stderr instead of stdout.
    'consoletitle': True,  # Display progress in the console window's titlebar.
    'writedescription': True,  # Write the video description to a .description file.
    'writeinfojson': True,  # Write the video description to a .info.json file.
    'clean_infojson': True,  # Remove internal metadata from the infojson.
    'getcomments': True,  # Extract video comments.
    'writeannotations': True,  # Write the video annotations to a .annotations.xml file.
    'writethumbnail': True,  # Write the thumbnail image to a file.
    'allow_playlist_files': True,  # Write playlists' description, infojson etc. to disk.
    'write_all_thumbnails': True,  # Write all thumbnail formats to files.
    'writelink': True,  # Write an internet shortcut file.
    'writeurllink': True,  # Write a Windows internet shortcut file.
    'writewebloclink': True,  # Write a macOS internet shortcut file.
    'writedesktoplink': True,  # Write a Linux internet shortcut file.
    'writesubtitles': True,  # Write the video subtitles to a file.
    'writeautomaticsub': True,  # Write the automatically generated subtitles to a file.
    'listsubtitles': True,  # List all available subtitles for the video.
    'subtitlesformat': 'srt',  # The format code for subtitles.
    'subtitleslangs': ['all', '-live_chat'],  # List of languages of the subtitles to download.
    'keepvideo': True,  # Keep the video file after post-processing.
    'daterange': None,  # A utils.DateRange object for date filtering.
    'skip_download': True,  # Skip the actual download of the video file.
    'cachedir': '/cache',  # Location of the cache files in the filesystem.
    'noplaylist': True,  # Download single video instead of a playlist if in doubt.
    'age_limit': 18,  # Skip videos unsuitable for the given age.
    'min_views': 1000,  # Minimum view count required to download.
    'max_views': 1000000,  # Maximum view count allowed to download.
    'download_archive': 'archive.txt',  # File where all downloads are recorded.
    'break_on_existing': True,  # Stop the download process if a file is in the archive.
    'break_per_url': True,  # Apply break_on_existing per URL.
    'cookiefile': 'cookies.txt',  # File name or text stream from where cookies should be read and dumped to.
    'cookiesfrombrowser': ('chrome', 'default'),  # Load cookies from browser profile.
    'legacyserverconnect': True,  # Allow HTTPS connection to servers without secure renegotiation.
    'nocheckcertificate': True,  # Do not verify SSL certificates.
    'client_certificate': 'client.pem',  # Path to client certificate file in PEM format.
    'client_certificate_key': 'client-key.pem',  # Path to private key file for client certificate.
    'client_certificate_password': 'password',  # Password for client certificate private key.
    'prefer_insecure': True,  # Use HTTP instead of HTTPS.
    'enable_file_urls': True,  # Enable file:// URLs.
    'http_headers': {'User-Agent': 'Mozilla/5.0'},  # Custom headers for all requests.
    'proxy': 'http://proxy.example.com:8080',  # URL of the proxy server to use.
    'geo_verification_proxy': 'http://geo-proxy.example.com:8080',  # Proxy for geo-verification.
    'socket_timeout': 10,  # Time to wait for unresponsive hosts in seconds.
    'bidi_workaround': True,  # Workaround for terminals without bidirectional text support.
    'debug_printtraffic': True,  # Print out sent and received HTTP traffic.
    'default_search': 'auto',  # Prepend this string if an input URL is not valid.
    'encoding': 'utf-8',  # Use this encoding instead of the system-specified.
    'extract_flat': 'in_playlist',  # Resolve and process url_results further.
    'wait_for_video': (30, 300),  # Wait for scheduled streams to become available.
    'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],  # List of postprocessors.
    'progress_hooks': [lambda d: print(d)],  # List of functions called on download progress.
    'postprocessor_hooks': [lambda d: print(d)],  # List of functions called on postprocessing progress.
    'merge_output_format': 'mp4',  # Extensions to use when merging formats.
    'final_ext': 'mp4',  # Expected final extension.
    'fixup': 'detect_or_warn',  # Automatically correct known faults of the file.
    'source_address': '0.0.0.0',  # Client-side IP address to bind to.
    'impersonate': 'chrome',  # Client to impersonate for requests.
    'sleep_interval_requests': 2,  # Seconds to sleep between requests during extraction.
    'sleep_interval': 5,  # Seconds to sleep before each download.
    'max_sleep_interval': 10,  # Upper bound for randomized sleep before each download.
    'sleep_interval_subtitles': 1,  # Seconds to sleep before each subtitle download.
    'listformats': True,  # Print an overview of available video formats and exit.
    'list_thumbnails': True,  # Print a table of all thumbnails and exit.
    'match_filter': lambda info_dict: None if 'Tutorial' in info_dict['title'] else 'Skipping',  # Function to filter videos.
    'color': 'auto',  # Output color policy.
    'geo_bypass': True,  # Bypass geographic restriction.
    'geo_bypass_country': 'US',  # Country code for geographic restriction bypass.
    'geo_bypass_ip_block': '192.168.0.0/24',  # IP range for geographic restriction bypass.
    'external_downloader': {'http': 'aria2c'},  # External downloader for HTTP.
    'compat_opts': {'filename': True, 'abort-on-error': False},  # Compatibility options.
    'progress_template': {'download': '%(progress)s', 'postprocess': '%(progress)s'},  # Templates for progress outputs.
    'retry_sleep_functions': {'http': lambda attempts: 2 * attempts},  # Functions for retry sleep times.
    'download_ranges': lambda info_dict, ydl: [{'start_time': 0, 'end_time': 10}],  # Callback function for download ranges.
    'force_keyframes_at_cuts': True,  # Re-encode video for precise cuts.
    'noprogress': True,  # Do not print the progress bar.
    'live_from_start': True,  # Download livestreams from the start.
    
}

print(yt_dlp_options)