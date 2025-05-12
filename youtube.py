import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from whoosh.filedb.filestore import RamStorage
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from apiclient.discovery import build

def jaccard_index(tokens, str):
    return (len(tokens.intersection(str)) * 1.0)/(len(tokens.union(str)))

schema = Schema(
    videoId=TEXT(stored=True),      # The title of the document
    content=TEXT(stored=True),    # The content of the document
    path=ID(stored=True)
)
def add_document(title, content, path, ix):
    writer = ix.writer()
    writer.add_document(videoId=title, content=content, path=path)
    writer.commit()

# Function to search the index
def search_index(query_str, ix):
        ans = []
        with ix.searcher() as searcher:
            query = QueryParser("content", ix.schema).parse(query_str)  # Search in 'content' field
            results = searcher.search(query)
            for result in results:
                print(f"Title: {result['videoId']}, Path: {result['path']}")
                print(f"Content: {result['content']}\n")
                ans.append(result['videoId'])
            return ans

def get_quotes(q_used, s):
    api_key='AIzaSyA5EHCy_esmk3QoYFmRUiDKg-pCBgsdSYk'
    #api_key='AIzaSyBl42xTgiNGW2VTtC1Ur_4RIk7AhiDZchY'
    youtube = build('youtube','v3',developerKey = api_key)
    request = youtube.search().list(q=q_used,part='snippet',type='video', maxResults=10)
    res = request.execute()
    response_dict = dict(res)
    video_ids = []
    for item in response_dict['items']:
        if 'videoId' in item['id']:
            video_ids.append(item['id']['videoId'])
    count = 1 
    snippet_dict = dict()
    texts = []
    stop_words = set(['ve', 'am', 'can', 'shouldn', 'down', 'from', "wouldn't", 'as', 'be', 'are', 'too', 'through', "don't", 'does', 'a', 'but', 'now', 'some', 'an', "couldn't", 'we', 'below', 'against', 'here', 'won', 'did', 'yourselves', 'was', 'how', 'above', 'him', 'shan', 'it', 'which', "weren't", 'himself', 'its', 'most', 'the', 'wouldn', 'needn', 're', 'or', 'while', "mustn't", 'your', 'if', "hasn't", "shouldn't", 'yours', 'she', 'her', 'wasn', 'other', 'aren', 'any', 'll', 'off', 'couldn', 'ain', "wasn't", 'few', 'is', 'of', 'there', "isn't", 'than', "shan't", 'why', 'has', 'so', 'in', "didn't", 'only', 'have', 'itself', 'for', 'under', 'own', 'hasn', 'were', "doesn't", "needn't", 'those', 'isn', 'out', 'very', "won't", 'until', 'hers', 'after', "it's", 'up', 'they', 'their', 'not', 'doing', 'no', 'them', 'where', 'ourselves', 'themselves', "aren't", 'our', 'on', 'that', 'theirs', 'nor', 't', 'ours', 'at', 's', 'again', 'same', 'over', 'just', 'ma', 'because', 'who', 'mightn', "you've", 'before', 'by', 'more', "should've", 'being', 'had', 'weren', 'this', "mightn't", 'm', 'with', 'should', "haven't", "hadn't", 'what', "that'll", "you're", 'during', 'haven', 'herself', 'and', 'these', 'such', 'further', 'mustn', 'do', "you'd", 'having', 'didn', 'd', 'hadn', 'y', 'yourself', 'his', 'into', 'once', 'each', 'don', 'all', 'then', 'both', 'when', 'he', 'will', 'me', 'whom', 'i', 'my', 'you', 'to', 'between', 'myself', 'doesn', 'about', 'been', 'o', "you'll", "she's"])

    storage = RamStorage()

    ix = storage.create_index(schema)
    # Function to add documents to the index
    results_found = []
    print("trying w proxy")
    for video_id in video_ids:
        try:
            print(f"for video {count}")

            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies={"https": "http://spfrxkwruc:cC6N1wBtvu~qa4Ng5z@gate.decodo.com:10001"})
            full_text = []
            snippet_dict[video_id] = []
            for entry in transcript:
                snippet_dict[video_id].append((entry['text'].lower(), int(entry['start'])))
                full_text.append(entry['text'].lower())
            print(video_id)
            print(" ".join(full_text))
            add_document(video_id, " ".join(full_text), f"/video/{video_id}", ix)
            count += 1
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            count += 1
    print(s)
    vids = search_index(s, ix)
    filtered_q = set(s.lower().split(' ')) - stop_words
    print(vids)
    for vid in vids:
        best_timestamp = 0
        best_text = ""
        best_score = -1
        for (text_found, start_time) in snippet_dict[vid]:
            score = jaccard_index(set(text_found.lower().split(' ')), filtered_q)
            if score > best_score:
                best_text = text_found
                best_timestamp = start_time
                best_score = score

        results_found.append((vid, best_text, best_score, best_timestamp))
    return sorted(results_found, key=lambda x: -x[2])

