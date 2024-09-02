import json
import random
import urllib3
import requests as rq
from loguru import logger
from typing import Optional
from urllib.parse import quote


from .uas import USER_AGENTS
from .exceptions import GoogleTranslateError
from .constants import GOOGLE_TTS_RPC, LANGUAGES, URL_SUFFIX_DEFAULT, URLS_SUFFIX


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GoogleTranslate:
    def __init__(
        self, url_suffix: str = "com", timeout: int = 5, proxies: Optional[dict] = None
    ):
        """
        Initializes the translation client with the specified settings.

        Args:
            url_suffix (str, optional): The suffix for the URL used in translation requests
                                        (e.g., 'com' for 'translate.google.com'). Defaults to 'com'.
            timeout (int, optional): The maximum time, in seconds, to wait for a response from the server.
                                    Defaults to 5 seconds.
            proxies (Optional[dict], optional): A dictionary of proxies to use for the translation requests.
                                                Format: {'http': 'http://ip:host', 'https': 'http://ip:host'}.
                                                Defaults to None if no proxy is to be used.

        """
        self.proxies = {} if proxies is None else proxies
        if url_suffix not in URLS_SUFFIX:
            self.url_suffix = URL_SUFFIX_DEFAULT
        else:
            self.url_suffix = url_suffix
        self.base_url = f"https://translate.google.{self.url_suffix}"
        self.url = self.base_url + "/_/TranslateWebserverUi/data/batchexecute"
        self.timeout = timeout

        self.session = rq.Session()
        self.session.verify = False
        self.session.proxies = self.proxies
        self.session.headers = self._rq_headers()

    def _rq_headers(self):
        return {
            "Referer": self.base_url,
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }

    def _f_req_data(self, text: str, src_lang: str = "auto", tgt_lang: str = "auto"):
        parameter = [[text.strip(), src_lang, tgt_lang, True], [1]]
        escaped_parameter = json.dumps(parameter, separators=(",", ":"))
        rpc = [[[random.choice(GOOGLE_TTS_RPC), escaped_parameter, None, "generic"]]]
        espaced_rpc = json.dumps(rpc, separators=(",", ":"))
        f_req = "f.req={}&".format(quote(espaced_rpc))
        return f_req

    def _process_lang(self, lang):
        if lang == "auto":
            return lang

        if lang in LANGUAGES.keys():
            return lang
        else:
            logger.warning(f"{lang=} not supported, will default to 'auto'")
            return "auto"

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "auto",
        pronounce: bool = False,
    ) -> str | list | None:
        """
        Translates the given text from the source language to the target language.

        Args:
            text (str): The text to be translated.
            source_lang (str, optional): The source language code (e.g., 'en' for English).
                                        Defaults to 'auto' for automatic language detection.
            target_lang (str, optional): The target language code (e.g., 'es' for Spanish).
                                        Defaults to 'auto' for automatic detection.
            pronounce (bool, optional): If True, returns the pronunciation of the translated text if possible.
                                        Defaults to False.

        Returns:
            str | list | None:
                - If `pronounce` is False, returns the translated text as a string.
                - If `pronounce` is True, returns a list containing the translated text and its pronunciation if its available.
                - Returns None if the translation fails or no text is provided.
        """
        text = str(text)
        if len(text) >= 5000:
            logger.warning(
                "GoogleTranslate can only translate text with less than 5000 characters"
            )
            return
        if len(text) == 0:
            logger.warning(f"Nothing to translate: {len(text)=}")
            return ""

        src_lang = self._process_lang(lang=source_lang)
        tgt_lang = self._process_lang(lang=target_lang)
        f_req_data = self._f_req_data(text=text, src_lang=src_lang, tgt_lang=tgt_lang)

        try:
            r = self.session.post(url=self.url, data=f_req_data, timeout=self.timeout)
            for line in r.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if GOOGLE_TTS_RPC[0] in decoded_line:
                    try:
                        response = list(json.loads(decoded_line))
                        response = list(response)
                        response = json.loads(response[0][2])
                        response_ = list(response)
                        response = response_[1][0]
                        if len(response) == 1:
                            if len(response[0]) > 5:
                                sentences = response[0][5]
                            else:  ## only url
                                sentences = response[0][0]
                                if pronounce:
                                    return [sentences, None, None]
                                return sentences

                            translate_text = ""
                            for sentence in sentences:
                                sentence = sentence[0]
                                translate_text += sentence.strip() + " "
                            if not pronounce:
                                return translate_text
                            pronounce_src = response_[0][0]
                            pronounce_tgt = response_[1][0][0][1]
                            return [translate_text, pronounce_src, pronounce_tgt]
                        elif len(response) == 2:
                            sentences = []
                            for i in response:
                                sentences.append(i[0])
                            if not pronounce:
                                return sentences
                            pronounce_src = response_[0][0]
                            pronounce_tgt = response_[1][0][0][1]
                            return [sentences, pronounce_src, pronounce_tgt]
                    except Exception as e:
                        raise e
            r.raise_for_status()
        except rq.exceptions.ConnectTimeout as e:
            # logger.debug(str(e))
            raise e
        except rq.exceptions.HTTPError as e:
            # Request successful, bad response
            # logger.debug(str(e))
            raise GoogleTranslateError(tts=self, response=r)
        except rq.exceptions.RequestException as e:
            # Request failed
            # logger.debug(str(e))
            raise GoogleTranslateError(tts=self)

    def detect(self, text: str) -> dict | None:
        """
        Detects the language of the given text.

        Args:
            text (str): The text for which to detect the language.

        Returns:
            dict | None:
                - Returns a dictionary where the key is the detected language code (e.g., 'en')
                and the value is the full language name (e.g., 'english').
                Example: {"en": "english"}.
                - Returns None if the language detection fails or if no text is provided.
        """
        if len(text) >= 5000:
            logger.warning(
                "GoogleTranslate can only detect text with less than 5000 characters"
            )
            return
        if len(text) == 0:
            logger.warning(f"Nothing to detact: {len(text)=}")
            return

        f_req_data = self._f_req_data(text)
        try:
            r = self.session.post(url=self.url, data=f_req_data, timeout=self.timeout)

            for line in r.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if GOOGLE_TTS_RPC[0] in decoded_line:
                    try:
                        response = json.loads(decoded_line)
                        response = json.loads(response[0][2])
                        detected_lang = response[0][2]
                        detected_lang = detected_lang.lower()
                    except Exception as e:
                        raise e
                    return {detected_lang: LANGUAGES[detected_lang]}
            r.raise_for_status()
        except rq.exceptions.HTTPError as e:
            # Request successful, bad response
            # logger.debug(str(e))
            raise GoogleTranslateError(tts=self, response=r)
        except rq.exceptions.RequestException as e:
            # Request failed
            # logger.debug(str(e))
            raise GoogleTranslateError(tts=self)
