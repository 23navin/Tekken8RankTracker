from yt_dlp import YoutubeDL
from requests import get, RequestException
from re import search
from os.path import exists
from os import makedirs, remove

from src.T8RankTracker.constants import request_headers
from src.T8RankTracker.helpers import time_to_seconds, log_dir

#downloads the text content of a url
def fetch_content(url):
    resp = get(url, headers=request_headers, timeout=10)
    resp.raise_for_status()
    return resp.text

#downlaod the manifest for a given youtube video
def fetch_manifest(url="https://www.youtube.com/watch?v=XjxiN_thnnk", resolution="1920x1080"):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': False,
        'noplaylist': True,
        'youtube_include_dash_manifest': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', None)

    for fmt in formats:
        if fmt.get('protocol') == 'm3u8_native' :
            format_url = fmt.get('manifest_url')
            # video_url = fmt.get('url')
            break
    else:
        raise RuntimeError("No HLS format with manifest found.")
    
    format_list = fetch_content(format_url)
    
    url_pattern = f'#EXT-X-STREAM-INF:.*RESOLUTION={resolution}.*\n(.*)'
    parse = search(url_pattern, format_list)
    
    if parse:
        manifest_url =  parse.group(1)
    else:
        raise RuntimeError("No DASH manifest URL found.")
    
    return manifest_url, fetch_content(manifest_url)

# parse the hls manifest into a list of segments with their urls
def parse_hls_manifest(hls_content) -> list:
    lines = hls_content.strip().splitlines()
    segments = [] # List of tuples (start_time, duration, url, downloaded)
    current_time = 0.0
    
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            duration = float(line.split(':')[1].split(',')[0])
            segments.append((current_time, duration))
            current_time += duration
        elif line and not line.startswith('#'):
            # This is a segment URL
            segments[-1] = (segments[-1][0], segments[-1][1], line, False)
            
    return segments

#get a segment for a given time
def find_segment(segments, target_time, output_prefix='segment'):
    #find the right segment for the given time
    for start_time, duration, url in segments:
        if start_time <= target_time < (start_time + duration):
            #download the segment
            try:
                resp = get(url, headers=request_headers, stream=True, timeout=15)
                resp.raise_for_status()
                
                # Save the segment to a file
                file_dir = f"bin/vid/{output_prefix}_{start_time:.2f}.ts"
                with open(file_dir, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return start_time, file_dir
            #if there is an error, print it
            except RequestException as e:
                print(f"Error fetching segment {url}: {e}")
            return None, None

#returns a list of segments for a given youtube video
def get_manifest(url="https://www.youtube.com/watch?v=XjxiN_thnnk", resolution="1920x1080") -> list:
    #Setup Manifest List
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': False,
        'noplaylist': True,
        'youtube_include_dash_manifest': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', None)

    for fmt in formats:
        if fmt.get('protocol') == 'm3u8_native' :
            format_url = fmt.get('manifest_url')
            # video_url = fmt.get('url')
            break
    else:
        raise RuntimeError("No HLS format with manifest found.")
    
    format_list = fetch_content(format_url)
    
    url_pattern = f'#EXT-X-STREAM-INF:.*RESOLUTION={resolution}.*\n(.*)'
    parse = search(url_pattern, format_list)
    
    if parse:
        manifest_url =  parse.group(1)
    else:
        raise RuntimeError("No DASH manifest URL found.")
    
    lines = fetch_content(manifest_url).strip().splitlines()
    segments = [] # List of lists (start_time, duration, url, downloaded)
    current_time = 0.0
    
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            duration = float(line.split(':')[1].split(',')[0])
            segments.append([current_time, duration])
            current_time += duration
        elif line and not line.startswith('#'):
            # This is a segment URL
            segments[-1].extend([line, False])
    
    print(f"Manifest parsed: {len(segments)} segments found. Video length: {current_time:.2f} seconds")
    return segments

def locate_segment():
    pass

class YoutubeVideoManager:
    def __init__(self, video_link, resolution="1920x1080", vid_dir="bin/vid"):
        self.video_link = video_link
        self.resolution = resolution
        self.dir = vid_dir
        
        #setup the directory for saving segments
        if not exists(vid_dir):
            makedirs(vid_dir)
            print(f"Directory created: {vid_dir}")
        
        self.manifest = get_manifest(video_link, resolution)
        
    #get the segment and its info for a given time
    def determine_segment(self, time):
        for idx, (start_time, duration, url, downloaded) in enumerate(self.manifest):
            if start_time <= time < (start_time + duration):
                segment_info = {
                    "start_time": start_time,
                    "duration": duration,
                    "url": url,
                    "filename": f"{self.dir}/segment_{start_time:.2f}.ts",
                    "downloaded": downloaded,
                    "index": idx
                }
                return segment_info
        else:
            print(f"No segment found for time: {time}")
            return None
            
    def download_segment(self, time, segment_info=None):
        #if no segment info is provided, get it
        if segment_info is None:
            segment_info = self.determine_segment(time)
        
        if segment_info:
            try:
                resp = get(segment_info['url'], headers=request_headers, stream=True, timeout=15)
                resp.raise_for_status()
                
                # Save the segment to a file
                with open(segment_info['filename'], 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Update the downloaded status
                self.manifest[segment_info['index']][-1] = True
                
                print(f"Segment downloaded: {segment_info['filename']}")
                return segment_info['filename']
            
            except RequestException as e:
                print(f"Error fetching segment {segment_info['url']}: {e}")
                return None
                
    def get_segment(self, time, segment_info=None):
        #if no segment info is provided, get it
        if segment_info is None:
            segment_info = self.determine_segment(time)
    
        #get prospective filename
        filename = segment_info['filename']
            
        if exists(filename):
            #Ensure the downloaded status is correct
            self.manifest[segment_info['index']][-1] = True
            
            print(f"Segment file already exists: {filename}")
            return filename
        else:
            print(f"Segment file does not exist: {filename}")
            self.download_segment(time, segment_info)
            return None
        
    def delete_segment(self, time, segment_info=None):
        #if no segment info is provided, get it
        if segment_info is None:
            segment_info = self.determine_segment(time)
            
        if segment_info:
            filename = segment_info['filename']
            if exists(filename):
                try:
                    remove(filename)
                    print(f"Segment deleted: {filename}")
                    
                    #update the downloaded status
                    self.manifest[segment_info['index']][-1] = False
                    
                except OSError as e:
                    print(f"Error deleting file {filename}: {e}")
                    
            else:
                print(f"File does not exist: {filename}")
                
    #verify that manifest download status is correct
    def scan_dir(self):
        marked_as_downloaded = 0
        in_dir = 0
        
        for idx, (start_time, duration, url, downloaded) in enumerate(self.manifest):
            if downloaded:
                marked_as_downloaded += 1
                
                filename = f"{self.dir}/segment_{start_time:.2f}.ts"
                if exists(filename):
                    in_dir += 1
                    print(f"File exists and marked as downloaded: {filename}")
                else:
                    print(f"File marked as downloaded but does not exist: {filename}")
                    # self.manifest[idx][-1] = False
        
        print(f"Total segments: {len(self.manifest)} | Marked as downloaded: {marked_as_downloaded} | Downloaded: {in_dir}")        

#demo
if __name__ == "__main__":
    from time import perf_counter
    
    yt_utl = 'https://www.youtube.com/watch?v=XjxiN_thnnk'
    # yt_utl = 'https://www.youtube.com/watch?v=aVYMfKTjGJ8'
    
    start_time = perf_counter()
    capture = YoutubeVideoManager(yt_utl)
    end_time = perf_counter()
    print(f"Time to initialize YoutubeCapture: {end_time - start_time:.2f} seconds")

    # Measure time for each get_segment call
    for t in range(20, 31):
        start_time = perf_counter()
        capture.get_segment(time_to_seconds(f'4:28:{t}'))
        end_time = perf_counter()
        print(f"Time to process get_segment for 4:28:{t}: {end_time - start_time:.2f} seconds")

    # # Measure time for delete_segment
    # start_time = perf_counter()
    # capture.delete_segment(time_to_seconds('4:28:20'))
    # end_time = perf_counter()
    # print(f"Time to process delete_segment for 4:28:20: {end_time - start_time:.2f} seconds")

    # Measure time for scan_dir
    start_time = perf_counter()
    capture.scan_dir()
    end_time = perf_counter()
    print(f"Time to process scan_dir: {end_time - start_time:.2f} seconds")
    
    # st_fetch = perf_counter()
    # info = get_manifest(yt_utl)
    # fi_fetch = perf_counter()
    # print(f"time to parse manifest: {fi_fetch - st_fetch:.2f} seconds")
    # print("manifest found.")
    
    # st_fetch = perf_counter()
    # time, file = find_segment(info, time_to_seconds('4:28:20'), 'segment')
    # print(f"segment {time:.2f} saved as {file}")
    # fi_fetch = perf_counter()
    # print(f"time to fetch 1st segment: {fi_fetch - st_fetch:.2f} seconds")
    
    # st_fetch = perf_counter()
    # time, file = find_segment(info, time_to_seconds('4:25:33'), 'segment')
    # print(f"segment {time:.2f} saved as {file}")
    # fi_fetch = perf_counter()
    # print(f"time to fetch 2nd segment: {fi_fetch - st_fetch:.2f} seconds")