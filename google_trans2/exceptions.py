class GoogleTranslateError(Exception):
    def __init__(self, msg=None, **kwargs):
        self.tts = kwargs.pop("tts", None)
        self.rsp = kwargs.pop("response", None)
        if msg:
            self.msg = msg
        elif self.tts is not None:
            self.msg = self.infer_msg(self.tts, self.rsp)
        else:
            self.msg = None
        super().__init__(self.msg)

    def infer_msg(self, tts, rsp=None):
        cause = "Unknown"

        if rsp is None:
            premise = "Failed to connect"
            return f"{premise}. Probable cause: timeout"

        status = rsp.status_code
        reason = rsp.reason

        premise = f"{status} ({reason}) from TTS API"

        if status == 403:
            cause = "Bad token or upstream API changes"
        elif status == 200 and not tts.lang_check:
            cause = f"No audio stream in response. Unsupported language '{tts.lang}'"
        elif status >= 500:
            cause = "Upstream API error. Try again later."

        return f"{premise}. Probable cause: {cause}"
