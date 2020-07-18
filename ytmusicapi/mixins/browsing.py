from typing import List, Dict
from ytmusicapi.helpers import *
from ytmusicapi.parsers import *


class BrowsingMixin:
    def search(self, query: str, filter: str = None) -> List[Dict]:
        """
        Search YouTube music
        Returns up to 20 results within the provided category.

        :param query: Query string, i.e. 'Oasis Wonderwall'
        :param filter: Filter for item types. Allowed values:
          'songs', 'videos', 'albums', 'artists', 'playlists'.
          Default: Default search, including all types of items.
        :return: List of results depending on filter.
          resultType specifies the type of item (important for default search).
          albums, artists and playlists additionally contain a browseId, corresponding to
          albumId, channelId and playlistId (browseId='VL'+playlistId)

          Example list::

            [
              {
                "videoId": "ZrOKjDZOtkA",
                "title": "Wonderwall (Remastered)",
                "artists": [
                  {
                    "name": "Oasis",
                    "id": "UCmMUZbaYdNH0bEd1PAlAqsA"
                  }
                ],
                "album": {
                  "name": "(What's The Story) Morning Glory? (Remastered)",
                  "id": "MPREb_9nqEki4ZDpp"
                },
                "duration": "4:19",
                "thumbnails": [...],
                "resultType": "song"
              }
            ]
        """
        body = {'query': query}
        endpoint = 'search'
        search_results = []
        filters = ['albums', 'artists', 'playlists', 'songs', 'videos']
        if filter and filter not in filters:
            raise Exception(
                "Invalid filter provided. Please use one of the following filters or leave out the parameter: "
                + ', '.join(filters))

        if filter:
            param1 = 'Eg-KAQwIA'
            param3 = 'MABqChAEEAMQCRAFEAo%3D'

            if filter == 'videos':
                param2 = 'BABGAAgACgA'
            elif filter == 'albums':
                param2 = 'BAAGAEgACgA'
            elif filter == 'artists':
                param2 = 'BAAGAAgASgA'
            elif filter == 'playlists':
                param2 = 'BAAGAAgACgB'
            else:
                param2 = 'RAAGAAgACgA'

            body['params'] = param1 + param2 + param3

        response = self._send_request(endpoint, body)

        try:
            # no results
            if 'contents' not in response:
                return search_results

            if 'tabbedSearchResultsRenderer' in response['contents']:
                results = response['contents']['tabbedSearchResultsRenderer']['tabs'][0][
                    'tabRenderer']['content']
            else:
                results = response['contents']

            results = nav(results, SECTION_LIST)

            # no results
            if len(results) == 1 and 'itemSectionRenderer' in results:
                return search_results

            for res in results:
                if 'musicShelfRenderer' in res:
                    results = res['musicShelfRenderer']['contents']

                    for result in results:
                        data = result['musicResponsiveListItemRenderer']
                        type = filter[:-1] if filter else None
                        search_result = self.parser.parse_search_result(data, type)
                        search_results.append(search_result)

        except Exception as e:
            print(str(e))

        return search_results

    @i18n
    def get_artist(self, channelId: str) -> Dict:
        """
        Get information about an artist and their top releases (songs,
        albums, singles and videos). The top lists contain pointers
        for getting the full list of releases. For songs/videos, pass
        the browseId to :py:func:`get_playlist`. For albums/singles,
        pass browseId and params to :py:func:`get_artist_albums`.

        :param channelId: channel id of the artist
        :return: Dictionary with requested information.

        Example::

            {
                "description": "Oasis were ...",
                "views": "1838795605",
                "name": "Oasis",
                "channelId": "UCUDVBtnOQi4c7E8jebpjc9Q",
                "subscribers": "2.3M",
                "subscribed": false,
                "thumbnails": [...],
                "songs": {
                    "browseId": "VLPLMpM3Z0118S42R1npOhcjoakLIv1aqnS1",
                    "results": [
                        {
                            "videoId": "ZrOKjDZOtkA",
                            "title": "Wonderwall (Remastered)",
                            "thumbnails": [...],
                            "artist": "Oasis",
                            "album": "(What's The Story) Morning Glory? (Remastered)"
                        }
                    ]
                },
                "albums": {
                    "results": [
                        {
                            "title": "Familiar To Millions",
                            "thumbnails": [...],
                            "year": "2018",
                            "browseId": "MPREb_AYetWMZunqA"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "singles": {
                    "results": [
                        {
                            "title": "Stand By Me (Mustique Demo)",
                            "thumbnails": [...],
                            "year": "2016",
                            "browseId": "MPREb_7MPKLhibN5G"
                        }
                    ],
                    "browseId": "UCmMUZbaYdNH0bEd1PAlAqsA",
                    "params": "6gPTAUNwc0JDbndLYlFBQV..."
                },
                "videos": {
                    "results": [
                        {
                            "title": "Wonderwall",
                            "thumbnails": [...],
                            "views": "358M",
                            "videoId": "bx1Bh8ZvH84",
                            "playlistId": "PLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                        }
                    ],
                    "browseId": "VLPLMpM3Z0118S5xuNckw1HUcj1D021AnMEB"
                }
            }
        """
        body = prepare_browse_endpoint("ARTIST", channelId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST)

        artist = {'description': None, 'views': None}
        header = response['header']['musicImmersiveHeaderRenderer']
        artist['name'] = nav(header, TITLE_TEXT)
        descriptionShelf = find_object_by_key(results,
                                              'musicDescriptionShelfRenderer',
                                              is_key=True)
        if descriptionShelf:
            artist['description'] = descriptionShelf['description']['runs'][0]['text']
            artist['views'] = None if 'subheader' not in descriptionShelf else descriptionShelf[
                'subheader']['runs'][0]['text']
        subscription_button = header['subscriptionButton']['subscribeButtonRenderer']
        artist['channelId'] = subscription_button['channelId']
        artist['subscribers'] = nav(subscription_button,
                                    ['subscriberCountText', 'runs', 0, 'text'], True)
        artist['subscribed'] = subscription_button['subscribed']
        artist['thumbnails'] = nav(header, THUMBNAILS)
        artist['songs'] = {'browseId': None}
        if 'musicShelfRenderer' in results[0]:  # API sometimes does not return songs
            musicShelf = nav(results, MUSIC_SHELF)
            if 'navigationEndpoint' in nav(musicShelf, TITLE):
                artist['songs']['browseId'] = nav(musicShelf, TITLE + NAVIGATION_BROWSE_ID)
            artist['songs']['results'] = parse_playlist_items(musicShelf['contents'])

        categories = ['albums', 'singles', 'videos']
        categories_local = [_('albums'), _('singles'), _('videos')]
        for i, category in enumerate(categories):
            data = [
                r['musicCarouselShelfRenderer'] for r in results
                if 'musicCarouselShelfRenderer' in r
                and nav(r['musicCarouselShelfRenderer'],
                        CAROUSEL_TITLE)['text'].lower() == categories_local[i]
            ]
            if len(data) > 0:
                artist[category] = {'browseId': None, 'results': []}
                if 'navigationEndpoint' in nav(data[0], CAROUSEL_TITLE):
                    artist[category]['browseId'] = nav(data[0],
                                                       CAROUSEL_TITLE + NAVIGATION_BROWSE_ID)
                    if category in ['albums', 'singles']:
                        artist[category]['params'] = nav(
                            data[0],
                            CAROUSEL_TITLE)['navigationEndpoint']['browseEndpoint']['params']

                for item in data[0]['contents']:
                    item = item['musicTwoRowItemRenderer']
                    result = {'title': nav(item, TITLE_TEXT)}
                    result['thumbnails'] = nav(item, THUMBNAIL_RENDERER)
                    if category == 'albums':
                        result['year'] = nav(item, SUBTITLE2)
                        result['browseId'] = nav(item, TITLE + NAVIGATION_BROWSE_ID)
                    elif category == 'singles':
                        result['year'] = nav(item, SUBTITLE)
                        result['browseId'] = nav(item, TITLE + NAVIGATION_BROWSE_ID)
                    elif category == 'videos':
                        result['views'] = nav(item, SUBTITLE2).split(' ')[0]
                        result['videoId'] = nav(item, NAVIGATION_VIDEO_ID)
                        result['playlistId'] = nav(item, NAVIGATION_PLAYLIST_ID)
                    artist[category]['results'].append(result)

        return artist

    def get_artist_albums(self, channelId: str, params: str) -> List[Dict]:
        """
        Get the full list of an artist's albums or singles

        :param channelId: channel Id of the artist
        :param params: params obtained by :py:func:`get_artist`
        :return: List of albums or singles

        Example::

            {
                "browseId": "MPREb_0rtvKhqeCY0",
                "artist": "Armin van Buuren",
                "title": "This I Vow (feat. Mila Josef)",
                "thumbnails": [...],
                "type": "EP",
                "year": "2020"
            }
        """
        body = {"browseId": channelId, "params": params}
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        artist = nav(response['header']['musicHeaderRenderer'], TITLE_TEXT)
        results = nav(response, SINGLE_COLUMN_TAB + SECTION_LIST + MUSIC_SHELF)
        albums = []
        release_type = nav(results, TITLE_TEXT).lower()
        for result in results['contents']:
            data = result['musicResponsiveListItemRenderer']
            browseId = nav(data, NAVIGATION_BROWSE_ID)
            title = get_item_text(data, 0)
            thumbnails = nav(data, THUMBNAILS)
            album_type = get_item_text(data, 1) if release_type == "albums" else "Single"
            year = get_item_text(data, 1, 2) if release_type == "albums" else get_item_text(
                data, 1)
            albums.append({
                "browseId": browseId,
                "artist": artist,
                "title": title,
                "thumbnails": thumbnails,
                "type": album_type,
                "year": year
            })

        return albums

    def get_album(self, browseId: str) -> Dict:
        """
        Get information and tracks of an album

        :param browseId: browseId of the album, for example
            returned by :py:func:`search`
        :return: Dictionary with title, description, artist and tracks.

        Each track is in the following format::

            {
              "title": "Seven",
              "trackCount": "7",
              "durationMs": "1439579",
              "playlistId": "OLAK5uy_kGnhwT08mQMGw8fArBowdtlew3DpgUt9c",
              "releaseDate": {
                "year": 2016,
                "month": 10,
                "day": 28
              },
              "description": "Seven is ...",
              "thumbnails": [...],
              "artist": [
                {
                  "name": "Martin Garrix",
                  "id": "UCqJnSdHjKtfsrHi9aI-9d3g"
                }
              ],
              "tracks": [
                {
                  "index": "1",
                  "title": "WIEE (feat. Mesto)",
                  "artists": "Martin Garrix",
                  "videoId": "8xMNeXI9wxI",
                  "lengthMs": "203406",
                  "likeStatus": "INDIFFERENT"
                }
              ]
            }
        """
        body = prepare_browse_endpoint("ALBUM", browseId)
        endpoint = 'browse'
        response = self._send_request(endpoint, body)
        data = nav(response, FRAMEWORK_MUTATIONS)
        album = {}
        album_data = find_object_by_key(data, 'musicAlbumRelease', 'payload', True)
        album['title'] = album_data['title']
        album['trackCount'] = album_data['trackCount']
        album['durationMs'] = album_data['durationMs']
        album['playlistId'] = album_data['audioPlaylistId']
        album['releaseDate'] = album_data['releaseDate']
        album['description'] = find_object_by_key(data, 'musicAlbumReleaseDetail', 'payload',
                                                  True)['description']
        album['thumbnails'] = album_data['thumbnailDetails']['thumbnails']
        album['artist'] = []
        artists_data = find_objects_by_key(data, 'musicArtist', 'payload')
        for artist in artists_data:
            album['artist'].append({
                'name': artist['musicArtist']['name'],
                'id': artist['musicArtist']['externalChannelId']
            })
        album['tracks'] = []

        likes = {}
        for item in data:
            if 'musicTrackUserDetail' in item['payload']:
                like_state = item['payload']['musicTrackUserDetail']['likeState'].split('_')[-1]
                parent_track = item['payload']['musicTrackUserDetail']['parentTrack']
                if like_state in ['NEUTRAL', 'UNKNOWN']:
                    likes[parent_track] = 'INDIFFERENT'
                else:
                    likes[parent_track] = like_state[:-1]

        for item in data[4:]:
            if 'musicTrack' in item['payload']:
                track = {}
                track['index'] = item['payload']['musicTrack']['albumTrackIndex']
                track['title'] = item['payload']['musicTrack']['title']
                track['thumbnails'] = item['payload']['musicTrack']['thumbnailDetails'][
                    'thumbnails']
                track['artists'] = item['payload']['musicTrack']['artistNames']
                # in case the song is unavailable, there is no videoId
                track['videoId'] = item['payload']['musicTrack']['videoId'] if 'videoId' in item[
                    'payload']['musicTrack'] else None
                track['lengthMs'] = item['payload']['musicTrack']['lengthMs']
                track['likeStatus'] = likes[item['entityKey']]
                album['tracks'].append(track)

        return album