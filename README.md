# google-trans2

A free and unlimited Python API for Google Translate. **Academic use only, do not abuse.**

Forked from [google_trans_new](https://github.com/lushan88a/google_trans_new), which seems to be no longer maintained. I only updated some decoding logic to accommodate changes in Google's API and made a few other minor modifications to the codebase.

## Installation

```bash
pip install -U git+https://github.com/chrk623/google-trans2.git
```

## Usage

### Translate

```python
from google_trans2 import GoogleTranslate

g = GoogleTranslate(url_suffix="com", timeout=5)
g.translate(text="Talk is cheap. Show me the code.", target_lang="ja")
# '話は安いです。 コードを見せてください。 '
```

### Detect

```python
g.detect("这是我的代码")
# {'zh-cn': 'chinese (simplified)'}
```

### Supported languages

```python
from google_trans2.constants import LANGUAGES

print(LANGUAGES)
# {
#     "auto": "auto",
#     "af": "afrikaans",
#     "sq": "albanian",
#     "am": "amharic",
#     "ar": "arabic",
#     "hy": "armenian",
#     ...
# }
```
