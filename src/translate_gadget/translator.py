"""翻译 API 接口与阿里云机器翻译实现"""

from abc import ABC, abstractmethod

from alibabacloud_alimt20181012.client import Client as AlimtClient
from alibabacloud_alimt20181012 import models as alimt_models
from alibabacloud_tea_openapi import models as open_api_models


# 短语言代码 → 阿里云 ALMT 语言代码
LANG_MAP = {
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "ru": "ru",
}


class TranslatorBase(ABC):
    """翻译服务基类，所有翻译实现需继承此类"""

    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        翻译文本

        Args:
            text: 待翻译的源文本
            source_lang: 源语言代码（如 'zh', 'en'）
            target_lang: 目标语言代码（如 'zh', 'en'）

        Returns:
            翻译后的文本
        """
        raise NotImplementedError


class AliTranslator(TranslatorBase):
    """基于阿里云机器翻译 (ALMT) 的翻译实现"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        region_id: str = "cn-hangzhou",
    ) -> None:
        config = open_api_models.Config()
        config.access_key_id = access_key_id
        config.access_key_secret = access_key_secret
        config.region_id = region_id
        self._client = AlimtClient(config)

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        src = LANG_MAP.get(source_lang, source_lang)
        tgt = LANG_MAP.get(target_lang, target_lang)

        request = alimt_models.TranslateGeneralRequest(
            format_type="text",
            source_language=src,
            target_language=tgt,
            source_text=text,
        )
        response = await self._client.translate_general_async(request)
        return response.body.data.translated
