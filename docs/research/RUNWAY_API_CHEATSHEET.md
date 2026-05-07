# Runway API Cheatsheet

Все по Runway API в одном месте, чтобы не гуглить каждый раз во время хакатона.

## Базовое

- **Base URL:** `https://api.dev.runwayml.com`
- **Auth header:** `Authorization: Bearer <RUNWAYML_API_SECRET>`
- **Version header:** `X-Runway-Version: 2024-11-06` (обязательный)
- **Docs:** https://docs.dev.runwayml.com
- **API Reference:** https://docs.dev.runwayml.com/api
- **Developer Portal:** https://dev.runwayml.com
- **Skills repo:** https://github.com/runwayml/skills (готовые python-скрипты)

## SDK

**Python:**
```bash
pip install runwayml
```

**Node:**
```bash
npm install --save @runwayml/sdk
```

**Skills (готовые скрипты для polling, batch generation):**
```bash
npx skills add runwayml/skills
```

## Эндпоинты которые нужны

### Видео
| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/image_to_video` | POST | image-to-video, основной для нас (gen4.5) |
| `/v1/text_to_video` | POST | text-to-video, без стартового кадра |
| `/v1/video_to_video` | POST | gen4_aleph, video editing - не используем |
| `/v1/text_to_image` | POST | gen4_image для генерации стартовых кадров |

### Аудио
| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/text_to_speech` | POST | TTS через ElevenLabs internally |
| `/v1/voices` | GET | список доступных голосов |
| `/v1/voices` | POST | создать voice (clone) |
| `/v1/sound_effect` | POST | sound effects |

### Task management
| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/tasks/{id}` | GET | статус задачи |
| `/v1/tasks/{id}` | DELETE | отменить/удалить |

### Uploads
| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/uploads` | POST | загрузить файл, получить runway:// URI |

### Org
| Endpoint | Метод | Назначение |
|---|---|---|
| `/v1/organization` | GET | инфа об орге |
| `/v1/organization/usage` | POST | сколько credits сожгли |

## Модели и цены

### Video
| Модель | Цена | Use case |
|---|---|---|
| **gen4.5** | **12 credits/sec** | основной для нас, image-to-video и text-to-video |
| gen4_turbo | 5 credits/sec | дешевле, image required |
| seedance2 | 36 credits/sec | reference image+video, длинный duration - fallback если ffmpeg склейка не зайдет |
| gen4_aleph | 15 credits/sec | video-to-video editing |
| veo3 | 40 credits/sec | премиум, не используем |
| veo3.1_fast | 10 credits/sec | Google fast |

**Duration constraint Gen-4.5:** только 5 или 10 секунд за один task. Для 30-45 сек постера склеиваем 3-5 клипов.

### Image
| Модель | Цена | Use case |
|---|---|---|
| **gen4_image_turbo** | **2 credits** | для генерации стартовых кадров - используем |
| gen4_image (1080p) | 8 credits | если нужна детализация |
| gen4_image (720p) | 5 credits | компромисс |
| gemini_2.5_flash | 5 credits | альтернатива |

### Audio
| Модель | Use case |
|---|---|
| **eleven_multilingual_v2** | TTS, поддерживает русский - используем |
| eleven_text_to_sound_v2 | sound effects |
| eleven_voice_isolation | очистка голоса |
| eleven_voice_dubbing | дубляж |
| eleven_multilingual_sts_v2 | voice conversion |

**TTS pricing:** 1 credit per 50 characters. Скрипт на 70-110 слов ≈ 500-800 chars ≈ 10-16 credits.

## Quickstart примеры

### Image-to-video Python (gen4.5)
```python
from runwayml import RunwayML, TaskFailedError

client = RunwayML()

try:
    task = client.image_to_video.create(
        model='gen4.5',
        prompt_image='https://example.com/start_frame.jpg',  # или data URI
        prompt_text='abstract slot reels spinning, deep purple, cinematic',
        ratio='1280:720',
        duration=10,
    ).wait_for_task_output()

    print('Task complete:', task)
    print('Video URL:', task.output[0])
except TaskFailedError as e:
    print('Failed:', e.task_details)
```

### Base64 data URI (если кадр локальный)
```python
import base64

with open('frame.png', 'rb') as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')
    data_uri = f"data:image/png;base64,{base64_image}"

# далее prompt_image=data_uri
```

### Text-to-image (gen4_image)
```python
task = client.text_to_image.create(
    model='gen4_image',
    ratio='1920:1080',
    prompt_text='@brand_palette abstract slot reels, cinematic, no text',
    reference_images=[
        {'uri': 'https://.../palette.jpg', 'tag': 'brand_palette'},
    ],
).wait_for_task_output()
```

### Text-to-speech
```python
task = client.text_to_speech.create(
    model='eleven_multilingual_v2',
    text='Артем, давно тебя не было. Возвращайся, у нас есть подарок.',
    voice_id='<russian_warm_voice_id>',  # достать из /v1/voices
).wait_for_task_output()
```

### Параллельные таски (важно для нашего pipeline)
```python
import asyncio
from runwayml import AsyncRunwayML

client = AsyncRunwayML()

async def generate_scene(scene):
    task = await client.image_to_video.create(
        model='gen4.5',
        prompt_image=scene['start_frame'],
        prompt_text=scene['visual_brief'],
        ratio='1280:720',
        duration=10,
    )
    return await task.wait_for_task_output()

# параллельно генерим 4 сцены
results = await asyncio.gather(*[generate_scene(s) for s in scenes])
```

## cURL для тестов

```bash
curl -X POST https://api.dev.runwayml.com/v1/image_to_video \
  -d '{
    "promptImage": "https://example.com/frame.jpg",
    "promptText": "cinematic motion",
    "model": "gen4.5",
    "ratio": "1280:720",
    "duration": 5
  }' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNWAYML_API_SECRET" \
  -H "X-Runway-Version: 2024-11-06"
```

## Бюджет credits на проект

50K credits на хакатон. Расчет с запасом:

| Что | Сколько | Credits |
|---|---|---|
| Тестовые генерации (50 итераций по 5 сек gen4_turbo) | 50 × 5 × 5 | 1,250 |
| Стартовые кадры gen4_image_turbo (50 шт) | 50 × 2 | 100 |
| Финальный батч 7 видео × 4 сцены × 10 сек gen4.5 | 7 × 4 × 10 × 12 | 3,360 |
| TTS финал (7 видео по 800 chars) | 7 × 16 | 112 |
| Demo video для submission, генерация сегментов | ~2,000 | 2,000 |
| Buffer на повторы и эксперименты | - | 25,000 |
| **Итого закладываем** | - | **~32,000** |

Остается ~18K credits в запасе. Если жмет - переключаемся на gen4_turbo (5 credits/sec вместо 12).

## Constraints и edge cases

- **gen4.5 duration:** только 5 или 10 секунд. Не 7, не 12.
- **Aspect ratios:** `1280:720`, `720:1280`, `1024:1024` (квадрат), `1920:1080`, `1080:1920`
- **Image input size:** до 10MB на файл, JPG/JPEG/PNG
- **Wait time:** image-to-video gen4.5 в среднем 1-3 минуты, в пиковые часы до 5-7 минут. **В выходные на хакатоне ожидаем очереди.**
- **Rate limits:** зависит от tier, на free tier и hackathon credits должно быть нормально для соло-проекта; если получаешь 429 - exponential backoff
- **Content moderation:** есть. Не упоминать конкретных брендов, реальных людей, не пытаться создавать realistic faces. Generic abstract motion graphics проходят без проблем.
- **task statuses:** `PENDING | THROTTLED | RUNNING | SUCCEEDED | FAILED | CANCELLED`
- **promptImage форматы:** URL или data URI

## Что делать если

- **Task FAILED:** в `task.failure_code` есть код ошибки. Самые частые: `SAFETY` (контент модерация), `INTERNAL` (повтори), `INVALID_INPUT` (плохой промпт или картинка)
- **Очередь медленная:** генерим финальные видео заранее (вечер воскресенья), не оставляем на утро понедельника
- **Credits заканчиваются:** в `client.organization.usage` смотрим остаток. Переключаемся на gen4_turbo
- **Голос не русский:** `client.voices.list()` -> ищем по `language='ru'` -> сохраняем `voice_id` в env
- **Воровство:** все секреты в `.env`, никогда не коммитить в git

## Modal как партнер хакатона

Если бэкенд тяжелый по compute (параллельный polling, ffmpeg stitching) - можно вынести render workers на Modal. $30/мес free compute. Не обязательно для нашего PoC, но если Railway волнами тормозит - запасной вариант.

```python
# modal_worker.py пример
import modal

app = modal.App("recall-render")
image = modal.Image.debian_slim().pip_install("ffmpeg-python", "runwayml")

@app.function(image=image, timeout=600)
def stitch_video(clips_urls, voiceover_url, campaign_id):
    # download, ffmpeg concat + audio overlay, upload
    pass
```
